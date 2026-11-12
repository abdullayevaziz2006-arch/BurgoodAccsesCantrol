import os
import time
import json
import asyncio
import logging
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from fastapi import Request, Response
from sqlalchemy.orm import Session

from app.models.models import AccessLog, Device, User, DirectionType, DeviceStatus
from app.services.websocket import ws_manager
from app.services.telegram_bot import telegram_bot

logger = logging.getLogger(__name__)

def parse_hikvision_xml(xml_str: str) -> Dict[str, Any]:
    """Hikvision XML xabarnomasidan asosiy ma'lumotlarni chiqarib olish"""
    data = {}
    try:
        root = ET.fromstring(xml_str)
        # Barcha elementlarni rekursiv qidirish
        for elem in root.iter():
            tag = elem.tag.split('}')[-1] # namespace larni olib tashlash
            if elem.text and elem.text.strip():
                data[tag] = elem.text.strip()
    except Exception as e:
        logger.warning(f"Hikvision XML tahlilida xatolik: {e}")
    return data

def extract_event_fields(event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Har xil Hikvision formatlaridan (JSON/XML/ISAPI) standart maydonlarni ajratish"""
    extracted = {
        "employee_no": None,
        "name": None,
        "card_no": None,
        "event_time": datetime.now(),
        "event_type": "Face Match",
        "serial_no": None,
        "device_serial": None,
        "direction": None
    }

    # AcsEvent ichini tekshirish
    acs = event_dict.get("AcsEvent") or event_dict.get("AccessControllerEvent") or event_dict

    # 1. Xodim/Talaba raqami
    emp_no = (
        acs.get("employeeNoString") or 
        acs.get("employeeNo") or 
        event_dict.get("employeeNoString") or 
        event_dict.get("employeeNo")
    )
    if emp_no:
        extracted["employee_no"] = str(emp_no).strip()

    # 2. Ism
    name = acs.get("name") or acs.get("label") or event_dict.get("name")
    if name:
        extracted["name"] = str(name).strip()

    # 3. Karta raqami
    card = acs.get("cardNo") or event_dict.get("cardNo")
    if card:
        extracted["card_no"] = str(card).strip()

    # 4. Vaqt
    time_str = acs.get("time") or acs.get("dateTime") or event_dict.get("time") or event_dict.get("dateTime")
    if time_str:
        try:
            extracted["event_time"] = datetime.fromisoformat(str(time_str).replace("Z", "+00:00")).replace(tzinfo=None)
        except Exception:
            try:
                extracted["event_time"] = datetime.strptime(str(time_str)[:19], "%Y-%m-%d %H:%M:%S")
            except Exception:
                extracted["event_time"] = datetime.now()

    # 5. Qurilma seriya raqami yoki ID si
    dev_serial = (
        acs.get("serialNo") or 
        acs.get("deviceSerial") or 
        acs.get("subSerialNo") or
        event_dict.get("serialNo") or 
        event_dict.get("deviceSerial") or
        event_dict.get("macAddress")
    )
    if dev_serial:
        extracted["device_serial"] = str(dev_serial).strip()

    # 5.1 Qurilma ichki IP manzili
    dev_ip = (
        acs.get("ipAddress") or 
        acs.get("ip") or 
        event_dict.get("ipAddress") or 
        event_dict.get("ip")
    )
    if dev_ip:
        extracted["device_ip"] = str(dev_ip).strip()

    # 5.2 MAC manzili
    dev_mac = acs.get("macAddress") or event_dict.get("macAddress")
    if dev_mac:
        extracted["mac_address"] = str(dev_mac).strip()

    # 6. Davomat holati (Attendance Status: checkIn, checkOut, breakOut, breakIn)
    att_status = (
        acs.get("attendanceStatus") or 
        acs.get("status") or 
        event_dict.get("attendanceStatus") or 
        event_dict.get("status")
    )
    if att_status:
        extracted["attendance_status"] = str(att_status).strip()

    return extracted

def resolve_event_direction(
    db: Session, 
    device: Optional[Device], 
    emp_no: Optional[str], 
    event_time: Optional[datetime] = None, 
    att_status: Optional[str] = None
) -> DirectionType:
    """
    Terminal yo'nalishini aniqlash:
    1. Standart (ENTRY yoki EXIT) -> o'z yo'nalishi qaytadi
    2. UNIVERSAL (Bitta terminal - Kirish, Tushlik, Chiqish):
       - 1-usul (Status mode): Terminal ekrani orqali (checkIn, checkOut, breakOut, breakIn)
       - 2-usul (Smart Auto): Vaqt va kunlik navbat bo'yicha (ertalab kelish, tushlik oralig'i, ketish)
    """
    # 1-usul: Terminal ekrani orqali bosilgan aniq tugma (checkIn, checkOut, breakOut, breakIn)
    if att_status:
        s = str(att_status).strip().lower()
        if "breakout" in s or s == "2":
            return DirectionType.BREAK_OUT
        elif "breakin" in s or s == "3":
            return DirectionType.BREAK_IN
        elif "checkout" in s or s == "1":
            return DirectionType.EXIT
        elif "checkin" in s or s == "0":
            return DirectionType.ENTRY

    if not device:
        return DirectionType.ENTRY
    if device.direction != DirectionType.UNIVERSAL:
        return device.direction

    # Universal ruxsat etilgan holatlar (checkboxlar)
    raw_opts = getattr(device, "universal_options", "") or "check_in,break_out,break_in,check_out"
    opts = [o.strip() for o in raw_opts.split(",") if o.strip()]

    # 2-usul: Avtomatik Aqlli ketma-ketlik (Smart Auto)
    if not emp_no:
        return DirectionType.ENTRY

    now_dt = event_time or datetime.now()
    today_start = now_dt.replace(hour=0, minute=0, second=0, microsecond=0)

    last_log = db.query(AccessLog).filter(
        AccessLog.employee_no == str(emp_no),
        AccessLog.event_time >= today_start
    ).order_by(AccessLog.event_time.desc()).first()

    if not last_log:
        return DirectionType.ENTRY

    # 90 soniya ichida takroriy yuz ko'rsatish (antiflood)
    diff_sec = abs((now_dt - last_log.event_time).total_seconds())
    if diff_sec < 90:
        return last_log.direction

    lunch_start_str = getattr(device, "lunch_start", "12:00") or "12:00"
    lunch_end_str = getattr(device, "lunch_end", "14:00") or "14:00"
    try:
        ls_h, ls_m = map(int, lunch_start_str.split(":"))
        le_h, le_m = map(int, lunch_end_str.split(":"))
        t_lunch_start = now_dt.replace(hour=ls_h, minute=ls_m, second=0)
        t_lunch_end = now_dt.replace(hour=le_h, minute=le_m, second=0)
    except Exception:
        t_lunch_start = now_dt.replace(hour=12, minute=0, second=0)
        t_lunch_end = now_dt.replace(hour=14, minute=0, second=0)

    last_dir = last_log.direction
    allow_breaks = ("break_out" in opts) and ("break_in" in opts)
    if allow_breaks and (t_lunch_start <= now_dt <= t_lunch_end):
        if last_dir in [DirectionType.ENTRY, DirectionType.BREAK_IN]:
            return DirectionType.BREAK_OUT
        else:
            return DirectionType.BREAK_IN
    else:
        if last_dir in [DirectionType.ENTRY, DirectionType.BREAK_IN]:
            return DirectionType.EXIT if "check_out" in opts else DirectionType.ENTRY
        else:
            return DirectionType.ENTRY if "check_in" in opts else DirectionType.EXIT

async def handle_hikvision_http_event(request: Request, db: Session) -> Response:
    """
    Hikvision HTTP Listening (Alarm Host) so'rovlarini qabul qilib saqlash:
    - JSON, XML yoki Multipart (yuz rasmi bilan) formatlarni taniydi
    - Baza (AccessLog) ga yozadi
    - WebSocket orqali Real-time jonli efirga uzatadi
    - Telegram botga bildirishnoma yuboradi
    - Hikvision kutgan standart 200 OK XML javobini qaytaradi
    """
    content_type = request.headers.get("content-type", "")
    client_ip = request.client.host if request.client else "127.0.0.1"
    
    event_dict: Dict[str, Any] = {}
    snapshot_url: Optional[str] = None

    # 1. Formatni tahlil qilish
    if "multipart/form-data" in content_type:
        try:
            form = await request.form()
            for key, val in form.items():
                if hasattr(val, "filename") and val.filename:
                    # Yuz rasmi fayli (Snapshot)
                    try:
                        file_bytes = await val.read()
                        if file_bytes and len(file_bytes) > 200:
                            upload_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads", "live_events")
                            os.makedirs(upload_dir, exist_ok=True)
                            fname = f"live_{int(time.time())}_{val.filename}"
                            fpath = os.path.join(upload_dir, fname)
                            with open(fpath, "wb") as f:
                                f.write(file_bytes)
                            snapshot_url = f"/uploads/live_events/{fname}"
                    except Exception as e:
                        logger.error(f"Hikvision rasmini saqlashda xatolik: {e}")
                else:
                    val_str = str(val).strip()
                    if val_str.startswith("{"):
                        try:
                            event_dict = json.loads(val_str)
                        except Exception:
                            pass
                    elif "<" in val_str and ">" in val_str:
                        event_dict = parse_hikvision_xml(val_str)
        except Exception as e:
            logger.error(f"Multipart parse xatosi: {e}")

    elif "json" in content_type:
        try:
            event_dict = await request.json()
        except Exception:
            event_dict = {}
    else:
        # Raw body
        try:
            body_bytes = await request.body()
            body_text = body_bytes.decode(errors="ignore").strip()
            if body_text.startswith("{"):
                event_dict = json.loads(body_text)
            elif "<" in body_text:
                event_dict = parse_hikvision_xml(body_text)
        except Exception as e:
            logger.error(f"Raw body parse xatosi: {e}")

    # Maydonlarni ajratish
    fields = extract_event_fields(event_dict)
    emp_no = fields.get("employee_no")

    # Standart Hikvision 200 OK XML javobi tayyorlaymiz
    xml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<ResponseStatus version="1.0" xmlns="http://www.hikvision.com/ver10/XMLSchema">
    <requestURL>{request.url.path}</requestURL>
    <statusCode>1</statusCode>
    <statusString>OK</statusString>
</ResponseStatus>"""

    # Qurilmani topish (Ichki IP, Tashqi IP, Seriya raqami yoki eng so'nggi faol qurilma)
    device = None
    dev_ip = fields.get("device_ip")
    dev_serial = fields.get("device_serial")

    if dev_ip:
        device = db.query(Device).filter(Device.ip_address == dev_ip).first()
    if not device and dev_serial:
        device = db.query(Device).filter(Device.serial_number == dev_serial).first()
    if not device and client_ip:
        device = db.query(Device).filter(Device.ip_address == client_ip).first()
    if not device:
        # Eng oxirgi faol turniket
        device = db.query(Device).filter(Device.is_active == True).order_by(Device.id.desc()).first()

    if device:
        device.status = DeviceStatus.ONLINE
        device.last_seen = datetime.utcnow()
        db.commit()

    # MUHIM: Faqat haqiqatda shaxs kelganda (employee_no yoki card_no mavjud bo'lganda) bazaga yoziladi va efirga chiqadi!
    # Texnik heartbeat, keepalive, kamera statusi va bo'sh xabarlar e'tiborsiz qoldiriladi.
    if not emp_no and not fields.get("card_no"):
        logger.debug("Hikvision texnik/heartbeat signali qabul qilindi (shaxs yo'q, e'tiborsiz qoldirildi)")
        return Response(content=xml_response, media_type="application/xml", status_code=200)

    device_id = device.id if device else 1
    device_name = device.name if device else "Asosiy Turniket (HTTP)"
    org_id = device.organization_id if device else None

    # Universal yoki oddiy terminal yo'nalishini aniqlash (Tushlik / Kirish / Chiqish)
    direction = resolve_event_direction(
        db=db,
        device=device,
        emp_no=str(emp_no) if emp_no else None,
        event_time=fields.get("event_time", datetime.now()),
        att_status=fields.get("attendance_status")
    )

    # Agar xodim yoki talaba aniqlangan bo'lsa
    user = None
    if emp_no:
        user = db.query(User).filter(User.employee_no == str(emp_no)).first()

    resolved_name = user.full_name if user else (fields.get("name") or (f"Foydalanuvchi #{emp_no}" if emp_no else "Noma'lum o'tish"))
    
    # Log yaratish
    new_log = AccessLog(
        device_id=device_id,
        user_id=user.id if user else None,
        employee_no=str(emp_no) if emp_no else None,
        user_name=resolved_name,
        card_number=fields.get("card_no"),
        direction=direction,
        event_time=fields.get("event_time", datetime.now()),
        event_type=fields.get("event_type", "Face Match"),
        status="Success",
        snapshot_url=snapshot_url,
        raw_event=f"http_alarm_{int(time.time())}",
        organization_id=org_id
    )
    db.add(new_log)
    db.commit()
    db.refresh(new_log)

    logger.info(f"⚡️ Hikvision HTTP Listening o'tish qayd etildi: {resolved_name} (ID: {emp_no}) -> {device_name}")

    # WebSocket orqali Real-Time uzatish (Kompyuter va telefon ekraniga darhol chiqadi!)
    ws_payload = {
        "type": "NEW_ACCESS_EVENT",
        "data": {
            "id": new_log.id,
            "device_id": device_id,
            "device_name": device_name,
            "user_id": user.id if user else None,
            "employee_no": str(emp_no) if emp_no else "",
            "user_name": resolved_name,
            "role": user.role.value if user else "student",
            "group_name": user.group_name if user else None,
            "photo_path": snapshot_url or (user.photo_path if user else None),
            "direction": direction.value if hasattr(direction, "value") else str(direction),
            "event_time": new_log.event_time.strftime("%Y-%m-%d %H:%M:%S"),
            "event_type": new_log.event_type,
            "status": new_log.status
        }
    }
    await ws_manager.broadcast(ws_payload)

    # Telegram bot orqali bildirishnoma (Direktor, kadrlar va barcha biriktirilgan rahbarlarga)
    try:
        ws_payload["data"]["organization_id"] = org_id
        asyncio.create_task(telegram_bot.broadcast_access_event(ws_payload["data"]))
    except Exception as e:
        logger.error(f"Telegram bildirishnomasi xatosi: {e}")

    # Hikvision kutgan standart 200 OK XML javobi
    xml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<ResponseStatus version="1.0" xmlns="http://www.hikvision.com/ver10/XMLSchema">
    <requestURL>{request.url.path}</requestURL>
    <statusCode>1</statusCode>
    <statusString>OK</statusString>
</ResponseStatus>"""

    return Response(content=xml_response, media_type="application/xml", status_code=200)
