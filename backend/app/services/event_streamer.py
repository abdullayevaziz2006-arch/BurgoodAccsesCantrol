import asyncio
import httpx
import xml.etree.ElementTree as ET
import json
import logging
import time
from datetime import datetime
from typing import Dict, Optional
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.models import Device, DeviceStatus, AccessLog, User, DirectionType
from app.services.websocket import ws_manager
from app.services.hikvision_listener import resolve_event_direction

logger = logging.getLogger(__name__)

class EventStreamWorker:
    """
    Hikvision yuzni tanish (Face ID) terminallaridan hodisalarni uzluksiz oluvchi servis:
    1. Polling mexanizmi (POST /ISAPI/AccessControl/AcsEvent?format=json) - har 2 soniyada
       yangi tanilgan shaxslar (Face Match, Card Match) hodisalarini qabul qiladi.
    2. Filtr: videoloss, heartbeat va noma'lum texnik xabarlar e'tiborsiz qoldiriladi.
       Faqat haqiqatda kelgan shaxslar (employee_no mavjud bo'lganlar) bazaga saqlanadi
       va jonli turniket oqimiga (WebSocket) uzatiladi.
    """
    def __init__(self):
        self.polling_tasks: Dict[int, asyncio.Task] = {}
        self.last_processed_serial: Dict[int, int] = {}
        self.last_user_seen: Dict[str, datetime] = {}
        self.is_running = True

    async def start(self):
        self.is_running = True
        logger.info("Hikvision EventStreamWorker (AcsEvent Poller) ishga tushdi.")
        asyncio.create_task(self.sync_active_devices_loop())

    async def stop(self):
        self.is_running = False
        for device_id, task in self.polling_tasks.items():
            task.cancel()
        self.polling_tasks.clear()
        logger.info("Hikvision EventStreamWorker to'xtatildi.")

    async def sync_active_devices_loop(self):
        """Har 15 soniyada bazadagi faol qurilmalarni tekshiradi va monitoringni yangilaydi"""
        while self.is_running:
            try:
                db = SessionLocal()
                devices = db.query(Device).filter(Device.is_active == True).all()
                active_ids = {d.id for d in devices}

                # Har bir faol terminal uchun monitoring vazifasini ishga tushirish
                for device in devices:
                    if device.id not in self.polling_tasks or self.polling_tasks[device.id].done():
                        task = asyncio.create_task(self.poll_device_events_loop(device.id))
                        self.polling_tasks[device.id] = task

                # O'chirilgan yoki nofaol qurilmalar monitoringini to'xtatish
                for dev_id in list(self.polling_tasks.keys()):
                    if dev_id not in active_ids:
                        self.polling_tasks[dev_id].cancel()
                        del self.polling_tasks[dev_id]

                db.close()
            except Exception as e:
                logger.error(f"sync_active_devices_loop xatolik: {e}")

            await asyncio.sleep(15)

    async def poll_device_events_loop(self, device_id: int):
        """Terminaldan har 2 soniyada yangi o'tish hodisalarini (AcsEvent) so'rab olish"""
        logger.info(f"Terminal #{device_id} uchun AcsEvent kuzatuvi boshlandi.")
        
        while self.is_running:
            db = SessionLocal()
            try:
                device = db.query(Device).filter(Device.id == device_id).first()
                if not device or not device.is_active:
                    break

                url = f"http://{device.ip_address}:{device.port}/ISAPI/AccessControl/AcsEvent?format=json"
                auth = httpx.DigestAuth(username=device.username, password=device.password)

                # Bugungi kundan boshlab qidirish
                today_str = datetime.now().strftime("%Y-%m-%d") + "T00:00:00+05:00"
                
                search_payload = {
                    "AcsEventCond": {
                        "searchID": f"poll_{int(time.time())}",
                        "searchResultPosition": 0,
                        "maxResults": 30,
                        "major": 5,
                        "minor": 0,
                        "startTime": today_str
                    }
                }

                async with httpx.AsyncClient(auth=auth, timeout=5.0) as client:
                    response = await client.post(url, json=search_payload)
                    
                    if response.status_code == 200:
                        self._update_device_status(device_id, DeviceStatus.ONLINE)
                        res_json = response.json().get("AcsEvent", {})
                        info_list = res_json.get("InfoList", [])

                        for item in info_list:
                            # MUHIM: Faqat haqiqatda shaxs aniqlangan (employee_no mavjud) hodisalar olinadi!
                            # Texnik hodisalar (videoloss, sensor, eshik ochilishi) e'tiborsiz qoldiriladi
                            emp_no = item.get("employeeNoString")
                            if not emp_no:
                                continue

                            serial_no = item.get("serialNo", 0)
                            
                            # Oldin o'qilgan bo'lsa o'tkazib yuborish
                            last_serial = self.last_processed_serial.get(device_id, 0)
                            if serial_no <= last_serial:
                                continue

                            # Bazada ushbu hodisa bor-yo'qligini tekshirish
                            raw_tag = f"serial_{serial_no}"
                            exists = db.query(AccessLog).filter(
                                AccessLog.device_id == device_id,
                                AccessLog.raw_event == raw_tag
                            ).first()
                            
                            if exists:
                                self.last_processed_serial[device_id] = max(last_serial, serial_no)
                                continue

                            # Vaqtni tahlil qilish
                            t_str = item.get("time", "")
                            try:
                                event_time = datetime.fromisoformat(t_str).replace(tzinfo=None)
                            except Exception:
                                event_time = datetime.now()

                            # Dublikatdan himoya: Agar ayni shu shaxs ayni shu qurilmada oxirgi 10 soniya ichida qayd etilgan bo'lsa, o'tkazib yuborish
                            cooldown_key = f"{device_id}_{emp_no}"
                            last_seen_time = self.last_user_seen.get(cooldown_key)
                            if last_seen_time and abs((event_time - last_seen_time).total_seconds()) < 10:
                                self.last_processed_serial[device_id] = max(last_serial, serial_no)
                                continue

                            self.last_user_seen[cooldown_key] = event_time

                            # Bazadan foydalanuvchini topish
                            user = db.query(User).filter(User.employee_no == str(emp_no)).first()
                            resolved_name = user.full_name if user else (item.get("name") or f"Foydalanuvchi #{emp_no}")

                            # Yo'nalishni aniqlash
                            direction = resolve_event_direction(
                                db=db,
                                device=device,
                                emp_no=str(emp_no),
                                event_time=event_time,
                                att_status=item.get("attendanceStatus") or item.get("status")
                            )

                            # Yangi kirish logini bazaga yozish
                            log = AccessLog(
                                device_id=device_id,
                                user_id=user.id if user else None,
                                employee_no=str(emp_no),
                                user_name=resolved_name,
                                card_number=item.get("cardNo"),
                                direction=direction,
                                event_time=event_time,
                                event_type="Face Match",
                                status="Success",
                                raw_event=raw_tag
                            )
                            db.add(log)
                            db.commit()
                            db.refresh(log)

                            self.last_processed_serial[device_id] = max(last_serial, serial_no)

                            # Jonli WebSocket orqali frontendga uzatish
                            event_payload = {
                                "type": "NEW_ACCESS_EVENT",
                                "data": {
                                    "id": log.id,
                                    "device_id": device.id,
                                    "device_name": device.name,
                                    "user_id": user.id if user else None,
                                    "employee_no": str(emp_no),
                                    "user_name": resolved_name,
                                    "role": user.role.value if user else "student",
                                    "group_name": user.group_name if user else None,
                                    "photo_path": user.photo_path if user else None,
                                    "direction": device.direction.value,
                                    "event_time": log.event_time.strftime("%Y-%m-%d %H:%M:%S"),
                                    "event_type": log.event_type,
                                    "status": log.status
                                }
                            }
                            await ws_manager.broadcast(event_payload)
                            logger.info(f"Yangi kelgan shaxs qayd etildi: {resolved_name} (ID: {emp_no}) -> {device.name}")
                    else:
                        logger.warning(f"Terminal #{device_id} AcsEvent javob bermadi: status {response.status_code}")
            except httpx.RequestError as e:
                self._update_device_status(device_id, DeviceStatus.OFFLINE)
                logger.warning(f"Terminal #{device_id} bilan aloqa uzildi: {e}")
            except Exception as e:
                logger.error(f"poll_device_events_loop #{device_id} xatolik: {e}")
            finally:
                db.close()

            await asyncio.sleep(2)

    def _update_device_status(self, device_id: int, status: DeviceStatus):
        try:
            db = SessionLocal()
            dev = db.query(Device).filter(Device.id == device_id).first()
            if dev:
                if status == DeviceStatus.OFFLINE and dev.last_seen:
                    diff_seconds = (datetime.utcnow() - dev.last_seen).total_seconds()
                    if diff_seconds < 900:
                        db.close()
                        return
                dev.status = status
                if status == DeviceStatus.ONLINE:
                    dev.last_seen = datetime.utcnow()
                db.commit()
            db.close()
        except Exception as e:
            logger.error(f"Device status update error: {e}")

    async def handle_event_json(self, device_id: int, data: dict):
        """Agar alertStream orqali hodisa kelsa tahlil qilish (faqat shaxslar)"""
        try:
            # videoloss yoki texnik xabarlar mutlaqo qabul qilinmaydi
            if data.get("eventType") == "videoloss":
                return

            event = data.get("AccessControllerEvent", {})
            employee_no = event.get("employeeNoString") or str(event.get("employeeNo", ""))
            if not employee_no or employee_no == "None" or employee_no == "0":
                return

            name = event.get("name")
            card_no = event.get("cardNo")
            
            await self.save_and_broadcast_log(
                device_id=device_id,
                employee_no=employee_no,
                card_number=card_no,
                user_name=name,
                event_type="Face Match",
                status="Success",
                raw=json.dumps(data)
            )
        except Exception as e:
            logger.error(f"Error parsing event JSON: {e}")

    async def save_and_broadcast_log(self, device_id: int, employee_no: str = None, card_number: str = None, 
                                     user_name: str = None, event_type: str = "Face Match", 
                                     status: str = "Success", raw: str = ""):
        # XAVFSIZLIK: Hech qachon employee_no si bo'lmagan soxta log yozilmaydi
        if not employee_no:
            return

        db = SessionLocal()
        try:
            device = db.query(Device).filter(Device.id == device_id).first()
            if not device:
                return

            user = db.query(User).filter(User.employee_no == str(employee_no)).first()
            resolved_name = user.full_name if user else (user_name or f"Foydalanuvchi #{employee_no}")
            direction = resolve_event_direction(
                db=db,
                device=device,
                emp_no=str(employee_no) if employee_no else None,
                event_time=datetime.utcnow()
            )

            log = AccessLog(
                device_id=device_id,
                user_id=user.id if user else None,
                employee_no=str(employee_no),
                user_name=resolved_name,
                card_number=card_number,
                direction=direction,
                event_time=datetime.utcnow(),
                event_type=event_type,
                status=status,
                raw_event=raw[:500] if raw else None
            )
            db.add(log)
            db.commit()
            db.refresh(log)

            # WebSocket orqali frontendga yuborish
            event_payload = {
                "type": "NEW_ACCESS_EVENT",
                "data": {
                    "id": log.id,
                    "device_id": device.id,
                    "device_name": device.name,
                    "user_id": user.id if user else None,
                    "employee_no": str(employee_no),
                    "user_name": resolved_name,
                    "role": user.role.value if user else "student",
                    "group_name": user.group_name if user else None,
                    "photo_path": user.photo_path if user else None,
                    "direction": direction.value,
                    "event_time": log.event_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "event_type": log.event_type,
                    "status": log.status
                }
            }
            await ws_manager.broadcast(event_payload)
            logger.info(f"O'tish qayd etildi: {resolved_name} ({direction.value}) -> {device.name}")

            # Telegram bot orqali bildirishnoma yuborish (agar sozlamalarda yoqilgan bo'lsa)
            if getattr(settings, "ENABLE_TELEGRAM_BOT", True):
                try:
                    from app.services.telegram_bot import telegram_bot
                    asyncio.create_task(telegram_bot.broadcast_access_event(event_payload["data"]))
                except Exception as tb_err:
                    logger.error(f"Telegram event broadcast xatosi: {tb_err}")
        except Exception as e:
            logger.error(f"Error saving log: {e}")
        finally:
            db.close()

event_stream_worker = EventStreamWorker()
