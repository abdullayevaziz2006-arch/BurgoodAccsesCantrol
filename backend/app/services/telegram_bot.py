import asyncio
import logging
import os
from datetime import datetime, date, time
from io import BytesIO
from typing import Optional, List, Dict, Any

import httpx
import openpyxl
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.models import (
    User, AccessLog, Device, Shift, Schedule, 
    DirectionType, TelegramUser, Department, Group, UserRole, Faculty, SystemAccount
)

logger = logging.getLogger("telegram_bot")

class TelegramBotService:
    def __init__(self, token: str):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        self._last_update_id = 0

    # -------------------------------------------------------------
    # Low-level Telegram API Client methods
    # -------------------------------------------------------------
    async def send_message(self, chat_id: str, text: str, reply_markup: Optional[Dict] = None, parse_mode: str = "HTML"):
        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(url, json=payload)
                return res.json()
        except Exception as e:
            logger.error(f"Telegram sendMessage xatosi ({chat_id}): {e}")
            return None

    async def send_document(self, chat_id: str, file_bytes: BytesIO, filename: str, caption: str = ""):
        url = f"{self.base_url}/sendDocument"
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                files = {
                    "document": (filename, file_bytes.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                }
                data = {
                    "chat_id": chat_id,
                    "caption": caption,
                    "parse_mode": "HTML"
                }
                res = await client.post(url, data=data, files=files)
                return res.json()
        except Exception as e:
            logger.error(f"Telegram sendDocument xatosi ({chat_id}): {e}")
            return None

    async def send_photo(self, chat_id: str, photo_path: str, caption: str = ""):
        url = f"{self.base_url}/sendPhoto"
        try:
            if not os.path.exists(photo_path):
                return await self.send_message(chat_id, caption)

            async with httpx.AsyncClient(timeout=20.0) as client:
                with open(photo_path, "rb") as f:
                    files = {"photo": f}
                    data = {"chat_id": chat_id, "caption": caption, "parse_mode": "HTML"}
                    res = await client.post(url, data=data, files=files)
                    return res.json()
        except Exception as e:
            logger.error(f"Telegram sendPhoto xatosi ({chat_id}): {e}")
            return None

    # -------------------------------------------------------------
    # Dynamic Keyboards per Role
    # -------------------------------------------------------------
    def get_keyboard_for_user(self, t_user: Optional[TelegramUser]) -> Dict:
        if not t_user or t_user.role == "pending" or not t_user.is_active:
            return {
                "keyboard": [[{"text": "🔄 Tekshirish (Status)"}]],
                "resize_keyboard": True
            }

        if t_user.role == "direktor":
            return {
                "keyboard": [
                    [{"text": "📊 Korxona Davomati"}, {"text": "⚠️ Kechikkan Xodimlar"}],
                    [{"text": "❌ Kelmagan Xodimlar"}, {"text": "📥 Oylik Tabel (Excel)"}],
                    [{"text": "🔍 Xodimni Qidirish"}, {"text": "🔔 Bildirishnomalar"}]
                ],
                "resize_keyboard": True,
                "persistent": True
            }

        if t_user.role == "buxgalter":
            return {
                "keyboard": [
                    [{"text": "📥 Oylik Tabel (Excel)"}, {"text": "📊 Korxona Davomati"}],
                    [{"text": "⚠️ Kechikkan Xodimlar"}, {"text": "❌ Kelmagan Xodimlar"}],
                    [{"text": "🔍 Xodimni Qidirish"}, {"text": "🔔 Bildirishnomalar"}]
                ],
                "resize_keyboard": True,
                "persistent": True
            }

        if t_user.role == "otdel_kadr":
            return {
                "keyboard": [
                    [{"text": "📊 Xodimlar Davomati"}, {"text": "⚠️ Kechikkan Xodimlar"}],
                    [{"text": "❌ Kelmagan Xodimlar"}, {"text": "📥 Oylik Tabel (Excel)"}],
                    [{"text": "📥 Xodimlar Excel"}, {"text": "🔍 Xodimni Qidirish"}]
                ],
                "resize_keyboard": True,
                "persistent": True
            }

        if t_user.role == "tutor":
            grp_name = t_user.assigned_group.name if t_user.assigned_group else "Guruh"
            return {
                "keyboard": [
                    [{"text": f"📊 {grp_name} Davomati"}, {"text": "⚠️ Kechikkan Talabalar"}],
                    [{"text": "❌ Kelmagan Talabalar"}, {"text": "📥 Guruh Excel"}],
                    [{"text": "🔍 Talabani Qidirish"}, {"text": "🔔 Bildirishnomalar"}]
                ],
                "resize_keyboard": True,
                "persistent": True
            }

        # superadmin, admin, dekan
        return {
            "keyboard": [
                [{"text": "📊 Bugungi Davomat"}, {"text": "⚠️ Kechikkanlar"}],
                [{"text": "❌ Kelmaganlar"}, {"text": "📥 Excel Hisobot"}],
                [{"text": "📥 Oylik Tabel (Excel)"}, {"text": "🔍 Qidiruv"}],
                [{"text": "🔔 Bildirishnomalar"}]
            ],
            "resize_keyboard": True,
            "persistent": True
        }

    # -------------------------------------------------------------
    # Business Logic Handlers with Role Filtering
    # -------------------------------------------------------------
    def _get_today_range(self):
        today = date.today()
        start = datetime.combine(today, time.min)
        end = datetime.combine(today, time.max)
        return start, end

    def _filter_user_query_by_role(self, query, t_user: TelegramUser):
        """Rol va tashkilot bo'yicha foydalanuvchilar filtrini qo'llash"""
        if t_user.organization_id and t_user.role != "superadmin":
            query = query.filter(User.organization_id == t_user.organization_id)

        if t_user.role in ("otdel_kadr", "direktor", "buxgalter"):
            # OTDEL KADR / DIREKTOR / BUXGALTER: Faqat xodimlar! TALABALAR 100% YO'Q!
            return query.filter(User.role.in_([UserRole.STAFF, UserRole.TEACHER]))
        elif t_user.organization and getattr(t_user.organization, "org_type", "") == "company":
            # Idora / Korxona bo'lsa
            return query.filter(User.role.in_([UserRole.STAFF, UserRole.TEACHER]))
        elif t_user.role == "tutor":
            # TYUTOR: Faqat o'ziga biriktirilgan guruh talabalari!
            q = query.filter(User.role == UserRole.STUDENT)
            if t_user.assigned_group_id:
                q = q.filter(User.group_id == t_user.assigned_group_id)
            return q
        elif t_user.role == "dekan" and t_user.assigned_faculty_id:
            # DEKAN: Fakultet talabalari va kafedra xodimlari
            return query.filter(
                (User.group.has(faculty_id=t_user.assigned_faculty_id)) |
                (User.department.has(faculty_id=t_user.assigned_faculty_id))
            )
        # superadmin / admin / rektor: hamma
        return query

    async def handle_start(self, chat_id: str, user_info: Dict):
        db: Session = SessionLocal()
        try:
            is_superadmin = (str(chat_id) == str(settings.SUPERADMIN_CHAT_ID))
            t_user = db.query(TelegramUser).filter(TelegramUser.chat_id == str(chat_id)).first()

            # SystemAccount orqali tekshirish (agar Master bot / veb paneldan oldindan biriktirilgan bo'lsa)
            username_val = user_info.get("username")
            username_query = [SystemAccount.telegram_chat_id == str(chat_id)]
            if username_val:
                username_query.append(SystemAccount.telegram_chat_id == f"@{username_val}")
                username_query.append(SystemAccount.telegram_chat_id == username_val)
            
            sys_acc = db.query(SystemAccount).filter(or_(*username_query)).first()

            if not t_user:
                assigned_role = "superadmin" if is_superadmin else (sys_acc.role if sys_acc else "pending")
                assigned_org_id = sys_acc.organization_id if sys_acc else None
                assigned_grp_id = sys_acc.assigned_group_id if sys_acc else None
                assigned_fac_id = sys_acc.assigned_faculty_id if sys_acc else None

                t_user = TelegramUser(
                    chat_id=str(chat_id),
                    username=user_info.get("username"),
                    first_name=user_info.get("first_name"),
                    last_name=user_info.get("last_name"),
                    role=assigned_role,
                    organization_id=assigned_org_id,
                    assigned_group_id=assigned_grp_id,
                    assigned_faculty_id=assigned_fac_id,
                    is_active=True,
                    notifications_enabled=True if sys_acc else False
                )
                db.add(t_user)
                db.commit()

                # Master Botga xabar yuborish (agar oldindan biriktirilmagan bo'lsa)
                if not is_superadmin and not sys_acc:
                    try:
                        from app.services.telegram_master_bot import telegram_master_bot
                        asyncio.create_task(telegram_master_bot.notify_new_user_request(
                            str(chat_id),
                            f"{user_info.get('first_name', '')} {user_info.get('last_name', '')}".strip() or "Noma'lum",
                            user_info.get("username")
                        ))
                    except Exception as err:
                        logger.error(f"Master bot bildirishnoma xatosi: {err}")
            elif (t_user.role == "pending" or not t_user.organization_id) and sys_acc:
                t_user.role = sys_acc.role
                t_user.organization_id = sys_acc.organization_id
                t_user.assigned_group_id = sys_acc.assigned_group_id
                t_user.assigned_faculty_id = sys_acc.assigned_faculty_id
                t_user.is_active = True
                db.commit()

            if t_user.role == "pending":
                pending_text = (
                    f"⏳ <b>Arizangiz qabul qilindi!</b>\n\n"
                    f"Assalomu alaykum, <b>{user_info.get('first_name', 'Foydalanuvchi')}</b>!\n"
                    f"Sizning Telegram ID: <code>{chat_id}</code>\n\n"
                    f"Tizim egasi/administratori (@BurgoodAccsesCantrolMaster_bot orqali) "
                    f"sizga mos rol (Otdel Kadr, Tyutor va h.k.) va tashkilot biriktirishi kutilmoqda.\n"
                    f"<i>Rol biriktirilishi bilan ushbu botda menyular ochiladi.</i>"
                )
                await self.send_message(chat_id, pending_text, reply_markup=self.get_keyboard_for_user(t_user))
                return

            role_names = {
                "superadmin": "👑 SuperAdmin",
                "admin": "👑 Rektor / Rahbariyat / Boshliq",
                "direktor": "👔 Bosh Direktor",
                "buxgalter": "🧮 Bosh Buxgalter",
                "otdel_kadr": "💼 Otdel Kadr (HR — Faqat Xodimlar)",
                "tutor": f"🎓 Tyutor ({t_user.assigned_group.name if t_user.assigned_group else 'Guruh'})",
                "dekan": "🏛 Dekan"
            }

            welcome_text = (
                f"🛡 <b>Burgood Access Control Tizimiga xush kelibsiz!</b>\n\n"
                f"Assalomu alaykum, <b>{user_info.get('first_name', 'Foydalanuvchi')}</b>!\n"
                f"📌 <b>Sizning rolingiz:</b> {role_names.get(t_user.role, t_user.role)}\n\n"
                f"Quyidagi menyu tugmalaridan foydalanishingiz mumkin:"
            )
            await self.send_message(chat_id, welcome_text, reply_markup=self.get_keyboard_for_user(t_user))
        finally:
            db.close()

    async def handle_today_stats(self, chat_id: str):
        db: Session = SessionLocal()
        try:
            t_user = db.query(TelegramUser).filter(TelegramUser.chat_id == str(chat_id)).first()
            if not t_user or t_user.role == "pending":
                await self.handle_start(chat_id, {})
                return

            start, end = self._get_today_range()
            today_str = date.today().strftime("%d.%m.%Y")

            # Rol bo'yicha ruxsat etilgan foydalanuvchilar IDlari
            base_query = db.query(User).filter(User.is_active == True)
            allowed_users = self._filter_user_query_by_role(base_query, t_user).all()
            allowed_user_ids = set(u.id for u in allowed_users)
            total_count = len(allowed_users)

            # Ruxsat etilgan loglar
            logs = db.query(AccessLog).filter(
                AccessLog.event_time >= start,
                AccessLog.event_time <= end,
                AccessLog.user_id.in_(allowed_user_ids)
            ).all()

            entries = sum(1 for l in logs if l.direction == DirectionType.ENTRY)
            exits = sum(1 for l in logs if l.direction == DirectionType.EXIT)
            present_user_ids = set(l.user_id for l in logs if l.user_id is not None)
            present_count = len(present_user_ids)
            absent_count = max(0, total_count - present_count)

            # Kechikkanlar
            late_count = await self._calculate_late_count(db, start, end, allowed_user_ids)

            title = "📊 BUGUNGI DAVOMAT HISOBOTI"
            if t_user.role == "otdel_kadr":
                title = "💼 XODIMLAR DAVOMATI HISOBOTI"
            elif t_user.role == "tutor":
                grp = t_user.assigned_group.name if t_user.assigned_group else "Guruh"
                title = f"🎓 {grp} GURUHI DAVOMAT HISOBOTI"

            text = (
                f"<b>{title} ({today_str})</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"👥 <b>Jami ro'yxatda:</b> {total_count} nafar\n"
                f"✅ <b>Kelganlar:</b> {present_count} nafar\n"
                f"⚠️ <b>Kechikkanlar:</b> {late_count} nafar\n"
                f"❌ <b>Kelmaganlar:</b> {absent_count} nafar\n\n"
                f"🔄 <b>Turniket harakatlari:</b>\n"
                f"🟢 Kirishlar: <b>{entries}</b> ta | 🔴 Chiqishlar: <b>{exits}</b> ta\n"
            )
            await self.send_message(chat_id, text, reply_markup=self.get_keyboard_for_user(t_user))
        finally:
            db.close()

    async def _calculate_late_count(self, db: Session, start: datetime, end: datetime, allowed_user_ids: set) -> int:
        if not allowed_user_ids:
            return 0

        logs = db.query(AccessLog).filter(
            AccessLog.event_time >= start,
            AccessLog.event_time <= end,
            AccessLog.direction == DirectionType.ENTRY,
            AccessLog.user_id.in_(allowed_user_ids)
        ).order_by(AccessLog.event_time.asc()).all()

        first_entries: Dict[int, datetime] = {}
        for l in logs:
            if l.user_id not in first_entries:
                first_entries[l.user_id] = l.event_time

        late_count = 0
        weekday_idx = date.today().weekday()
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        day_key = days[weekday_idx]

        for user_id, entry_time in first_entries.items():
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                continue

            sch_id = user.schedule_id
            if not sch_id and user.group_id and user.group:
                sch_id = user.group.schedule_id
            if not sch_id and user.department_id and user.department:
                sch_id = user.department.schedule_id

            if not sch_id:
                shift_start = "08:30"
                late_tol = 15
            else:
                sch = db.query(Schedule).filter(Schedule.id == sch_id).first()
                shift_id = getattr(sch, f"{day_key}_shift_id", None) if sch else None
                if not shift_id:
                    continue
                shift = db.query(Shift).filter(Shift.id == shift_id).first()
                if not shift:
                    continue
                shift_start = shift.start_time
                late_tol = shift.late_tolerance_minutes

            try:
                sh_hour, sh_min = map(int, shift_start.split(":"))
                limit_minutes = sh_hour * 60 + sh_min + late_tol
                actual_minutes = entry_time.hour * 60 + entry_time.minute
                if actual_minutes > limit_minutes:
                    late_count += 1
            except Exception:
                pass

        return late_count

    async def handle_late_list(self, chat_id: str):
        db: Session = SessionLocal()
        try:
            t_user = db.query(TelegramUser).filter(TelegramUser.chat_id == str(chat_id)).first()
            if not t_user or t_user.role == "pending":
                await self.handle_start(chat_id, {})
                return

            start, end = self._get_today_range()
            today_str = date.today().strftime("%d.%m.%Y")

            base_query = db.query(User).filter(User.is_active == True)
            allowed_users = self._filter_user_query_by_role(base_query, t_user).all()
            allowed_user_ids = set(u.id for u in allowed_users)

            logs = db.query(AccessLog).filter(
                AccessLog.event_time >= start,
                AccessLog.event_time <= end,
                AccessLog.direction == DirectionType.ENTRY,
                AccessLog.user_id.in_(allowed_user_ids)
            ).order_by(AccessLog.event_time.asc()).all()

            first_entries: Dict[int, datetime] = {}
            for l in logs:
                if l.user_id not in first_entries:
                    first_entries[l.user_id] = l.event_time

            weekday_idx = date.today().weekday()
            days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
            day_key = days[weekday_idx]

            late_list = []
            for user_id, entry_time in first_entries.items():
                user = db.query(User).filter(User.id == user_id).first()
                if not user:
                    continue

                sch_id = user.schedule_id
                if not sch_id and user.group_id and user.group:
                    sch_id = user.group.schedule_id
                if not sch_id and user.department_id and user.department:
                    sch_id = user.department.schedule_id

                if not sch_id:
                    shift_start = "08:30"
                    late_tol = 15
                else:
                    sch = db.query(Schedule).filter(Schedule.id == sch_id).first()
                    shift_id = getattr(sch, f"{day_key}_shift_id", None) if sch else None
                    if not shift_id:
                        continue
                    shift = db.query(Shift).filter(Shift.id == shift_id).first()
                    if not shift:
                        continue
                    shift_start = shift.start_time
                    late_tol = shift.late_tolerance_minutes

                try:
                    sh_hour, sh_min = map(int, shift_start.split(":"))
                    target_min = sh_hour * 60 + sh_min
                    actual_min = entry_time.hour * 60 + entry_time.minute
                    delay = actual_min - (target_min + late_tol)
                    if delay > 0:
                        dept_or_grp = user.group.name if user.group else (user.department.name if user.department else "-")
                        late_list.append({
                            "name": user.full_name,
                            "dept": dept_or_grp,
                            "entry": entry_time.strftime("%H:%M:%S"),
                            "shift": shift_start,
                            "delay": actual_min - target_min
                        })
                except Exception:
                    pass

            target_label = "Xodimlar" if t_user.role == "otdel_kadr" else ("Talabalar" if t_user.role == "tutor" else "Shaxslar")
            if not late_list:
                await self.send_message(
                    chat_id,
                    f"✅ <b>Bugun ({today_str}) kechikkan {target_label.lower()} yo'q!</b>\nBarchasi vaqtida kelgan.",
                    reply_markup=self.get_keyboard_for_user(t_user)
                )
                return

            text = f"⚠️ <b>KECHIKKANLAR RO'YXATI ({today_str}):</b>\n"
            text += f"<i>Jami: {len(late_list)} nafar</i>\n━━━━━━━━━━━━━━━━━━━━━\n"

            for i, item in enumerate(late_list[:25], 1):
                text += f"<b>{i}. {item['name']}</b> ({item['dept']})\n"
                text += f"   ⏱ Kirgan: <code>{item['entry']}</code> (Reja: {item['shift']})\n"
                text += f"   🚨 Kechikish: <b>+{item['delay']} daqiqa</b>\n\n"

            await self.send_message(chat_id, text, reply_markup=self.get_keyboard_for_user(t_user))
        finally:
            db.close()

    async def handle_absent_list(self, chat_id: str):
        db: Session = SessionLocal()
        try:
            t_user = db.query(TelegramUser).filter(TelegramUser.chat_id == str(chat_id)).first()
            if not t_user or t_user.role == "pending":
                await self.handle_start(chat_id, {})
                return

            start, end = self._get_today_range()
            today_str = date.today().strftime("%d.%m.%Y")

            base_query = db.query(User).filter(User.is_active == True)
            allowed_users = self._filter_user_query_by_role(base_query, t_user).all()
            allowed_user_ids = set(u.id for u in allowed_users)

            logs = db.query(AccessLog.user_id).filter(
                AccessLog.event_time >= start,
                AccessLog.event_time <= end,
                AccessLog.user_id.in_(allowed_user_ids)
            ).distinct().all()

            present_ids = set(l[0] for l in logs)

            absent_users = [u for u in allowed_users if u.id not in present_ids]
            target_label = "Xodimlar" if t_user.role == "otdel_kadr" else ("Talabalar" if t_user.role == "tutor" else "Shaxslar")

            if not absent_users:
                await self.send_message(
                    chat_id,
                    f"🎉 <b>Ajoyib natija!</b>\nBugun ({today_str}) barcha {target_label.lower()} to'liq 100% kelgan!",
                    reply_markup=self.get_keyboard_for_user(t_user)
                )
                return

            text = f"❌ <b>BUGUN KELMAGANLAR ({today_str}):</b>\n"
            text += f"Jami kelmaganlar: <b>{len(absent_users)} nafar</b>\n━━━━━━━━━━━━━━━━━━━━━\n\n"

            for i, u in enumerate(absent_users[:30], 1):
                info = u.group.name if u.group else (u.department.name if u.department else "-")
                text += f"{i}. <b>{u.full_name}</b> ({info})\n"

            if len(absent_users) > 30:
                text += f"\n<i>...yana {len(absent_users) - 30} nafar.</i>"

            await self.send_message(chat_id, text, reply_markup=self.get_keyboard_for_user(t_user))
        finally:
            db.close()

    async def handle_excel_report(self, chat_id: str):
        db: Session = SessionLocal()
        try:
            t_user = db.query(TelegramUser).filter(TelegramUser.chat_id == str(chat_id)).first()
            if not t_user or t_user.role == "pending":
                await self.handle_start(chat_id, {})
                return

            start, end = self._get_today_range()
            today_str = date.today().strftime("%Y-%m-%d")

            base_query = db.query(User).filter(User.is_active == True)
            allowed_users = self._filter_user_query_by_role(base_query, t_user).all()
            allowed_user_ids = set(u.id for u in allowed_users)

            logs = db.query(AccessLog).filter(
                AccessLog.event_time >= start,
                AccessLog.event_time <= end,
                AccessLog.user_id.in_(allowed_user_ids)
            ).order_by(AccessLog.event_time.asc()).limit(5000).all()

            await self.send_message(chat_id, "⏳ <i>Excel hisobot tayyorlanmoqda, kuting...</i>")

            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Davomat"

            headers = ["№", "Vaqt", "ID", "F.I.SH", "Maqomi", "Bo'lim / Guruh", "Yo'nalish", "Turniket", "Holat"]
            ws.append(headers)

            for cell in ws[1]:
                cell.font = openpyxl.styles.Font(bold=True, color="FFFFFF")
                cell.fill = openpyxl.styles.PatternFill(start_color="1F497D", end_color="1F497D", fill_type="solid")

            for i, l in enumerate(logs, 1):
                role_str = "Talaba" if l.user and l.user.role == UserRole.STUDENT else "Xodim"
                info = (l.user.group.name if l.user and l.user.group else (l.user.department.name if l.user and l.user.department else "-")) if l.user else "-"
                ws.append([
                    i,
                    l.event_time.strftime("%Y-%m-%d %H:%M:%S"),
                    l.employee_no or "-",
                    l.user_name or "Noma'lum",
                    role_str,
                    info,
                    "KIRISH" if l.direction == DirectionType.ENTRY else "CHIQISH",
                    l.device.name if l.device else f"Qurilma #{l.device_id}",
                    l.status
                ])

            for col in ws.columns:
                max_len = max(len(str(cell.value or '')) for cell in col)
                col_letter = openpyxl.utils.get_column_letter(col[0].column)
                ws.column_dimensions[col_letter].width = max(max_len + 3, 10)

            output = BytesIO()
            wb.save(output)
            output.seek(0)

            filename = f"Davomat_{today_str}.xlsx"
            caption = f"📊 <b>Davomat Hisoboti ({today_str})</b>\nJami qatorlar: {len(logs)} ta"
            await self.send_document(chat_id, output, filename, caption=caption)
        finally:
            db.close()

    async def handle_tabel_report(self, chat_id: str):
        db: Session = SessionLocal()
        try:
            t_user = db.query(TelegramUser).filter(TelegramUser.chat_id == str(chat_id)).first()
            if not t_user or t_user.role == "pending":
                await self.handle_start(chat_id, {})
                return

            await self.send_message(chat_id, "⏳ <i>Oylik Ish Vaqti Tabeli tayyorlanmoqda, kuting...</i>")

            today = date.today()
            url = f"http://127.0.0.1:{settings.PORT}/api/v1/attendance/export-tabel-excel?year={today.year}&month={today.month}"
            async with httpx.AsyncClient(timeout=60.0) as client:
                res = await client.get(url)
                if res.status_code == 200:
                    output = BytesIO(res.content)
                    filename = f"Tabel_{today.strftime('%Y_%m')}.xlsx"
                    caption = (
                        f"🧮 <b>Oylik Ish Vaqti Tabeli ({today.strftime('%B %Y')})</b>\n\n"
                        f"Xodimlar ishlagan soatlari, kechikishlar va keldi-ketdi hisoboti."
                    )
                    await self.send_document(chat_id, output, filename, caption=caption)
                else:
                    await self.send_message(chat_id, "❌ Tabel hisobotini yaratishda xatolik yuz berdi.")
        except Exception as e:
            logger.error(f"handle_tabel_report xatosi: {e}")
            await self.send_message(chat_id, f"❌ Xatolik: {e}")
        finally:
            db.close()

    async def handle_search(self, chat_id: str, query_text: str):
        db: Session = SessionLocal()
        try:
            t_user = db.query(TelegramUser).filter(TelegramUser.chat_id == str(chat_id)).first()
            if not t_user or t_user.role == "pending":
                await self.handle_start(chat_id, {})
                return

            q = query_text.strip().lower()
            base_query = db.query(User).filter(
                (func.lower(User.full_name).contains(q)) |
                (func.lower(User.employee_no).contains(q)) |
                (func.lower(User.phone_number).contains(q))
            )

            # Rol bo'yicha cheklov
            filtered_query = self._filter_user_query_by_role(base_query, t_user)
            users = filtered_query.limit(5).all()

            if not users:
                await self.send_message(
                    chat_id, 
                    f"🔍 '<b>{query_text}</b>' bo'yicha hech kim topilmadi.\n(Eslatma: Sizning rolingiz bo'yicha faqat ruxsat etilgan shaxslar ko'rsatiladi)"
                )
                return

            start, end = self._get_today_range()

            for u in users:
                last_log = db.query(AccessLog).filter(
                    AccessLog.user_id == u.id,
                    AccessLog.event_time >= start,
                    AccessLog.event_time <= end
                ).order_by(AccessLog.event_time.desc()).first()

                role_icon = "🎓 Talaba" if u.role == UserRole.STUDENT else "💼 Xodim"
                org_info = u.group.name if u.group else (u.department.name if u.department else "-")

                if last_log:
                    dir_str = "🟢 Kirgan" if last_log.direction == DirectionType.ENTRY else "🔴 Chiqqan"
                    status_text = f"{dir_str} ({last_log.event_time.strftime('%H:%M:%S')}) — {last_log.device.name if last_log.device else 'Turniket'}"
                else:
                    status_text = "❌ Bugun hali kelmadi"

                caption = (
                    f"👤 <b>{u.full_name}</b>\n"
                    f"━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🆔 <b>ID:</b> <code>{u.employee_no}</code>\n"
                    f"📌 <b>Maqomi:</b> {role_icon}\n"
                    f"🏛 <b>Bo'lim / Guruh:</b> {org_info}\n"
                    f"📞 <b>Tel:</b> {u.phone_number or 'Kiritilmagan'}\n\n"
                    f"🕒 <b>Bugungi holati:</b>\n{status_text}\n"
                )

                if u.photo_path and os.path.exists(u.photo_path):
                    await self.send_photo(chat_id, u.photo_path, caption=caption)
                else:
                    await self.send_message(chat_id, caption)
        finally:
            db.close()

    async def handle_toggle_notifications(self, chat_id: str):
        db: Session = SessionLocal()
        try:
            t_user = db.query(TelegramUser).filter(TelegramUser.chat_id == str(chat_id)).first()
            if not t_user:
                return

            t_user.notifications_enabled = not t_user.notifications_enabled
            db.commit()

            text = "🔔 <b>Jonli bildirishnomalar YOQILDI!</b>" if t_user.notifications_enabled else "🔕 <b>Bildirishnomalar O'CHIRILDI.</b>"
            await self.send_message(chat_id, text, reply_markup=self.get_keyboard_for_user(t_user))
        finally:
            db.close()

    # -------------------------------------------------------------
    # Real-time event broadcaster (called on turnstile pass)
    # -------------------------------------------------------------
    async def broadcast_access_event(self, log_dict: Dict[str, Any]):
        db: Session = SessionLocal()
        try:
            subscribers = db.query(TelegramUser).filter(
                TelegramUser.is_active == True,
                TelegramUser.notifications_enabled == True,
                TelegramUser.role != "pending"
            ).all()

            if not subscribers:
                return

            dir_raw = str(log_dict.get("direction", "")).lower()
            if "break_out" in dir_raw or "breakout" in dir_raw:
                direction_icon = "🍱 TUSHLIKKA CHIQISH"
            elif "break_in" in dir_raw or "breakin" in dir_raw:
                direction_icon = "☕ TUSHLIKDAN KIRISH"
            elif "exit" in dir_raw or "chiqish" in dir_raw:
                direction_icon = "🔴 CHIQISH"
            else:
                direction_icon = "🟢 KIRISH"
            user_name = log_dict.get("user_name") or "Noma'lum shaxs"
            device_name = log_dict.get("device_name") or "Turniket"
            event_time = log_dict.get("event_time", "")
            user_role = log_dict.get("role", "student")
            group_name = log_dict.get("group_name")

            try:
                dt_obj = datetime.fromisoformat(event_time)
                time_str = dt_obj.strftime("%H:%M:%S")
            except Exception:
                time_str = event_time

            msg = (
                f"🚨 <b>Turniket Harakati: {direction_icon}</b>\n"
                f"👤 <b>F.I.SH:</b> {user_name}\n"
                f"🆔 <b>ID:</b> <code>{log_dict.get('employee_no', '-')}</code>\n"
                f"🚪 <b>Turniket:</b> {device_name}\n"
                f"⏱ <b>Vaqti:</b> {time_str}"
            )

            for s in subscribers:
                # Tashkilot tekshiruvi: agar xodim boshqa obyektdan bo'lsa, xabar bormasin
                if s.organization_id and log_dict.get("organization_id") and s.organization_id != log_dict.get("organization_id"):
                    continue
                # Direktor, buxgalter va otdel kadrga faqat xodimlar xabari boradi
                if s.role in ("otdel_kadr", "direktor", "buxgalter") and user_role == "student":
                    continue
                # Tyutorga faqat o'z guruhi xabari boradi
                if s.role == "tutor":
                    if user_role != "student":
                        continue
                    if s.assigned_group and s.assigned_group.name != group_name:
                        continue

                await self.send_message(s.chat_id, msg)
        except Exception as e:
            logger.error(f"Telegram broadcast xatosi: {e}")
        finally:
            db.close()

    # -------------------------------------------------------------
    # Polling Loop
    # -------------------------------------------------------------
    async def _process_update(self, update: Dict):
        message = update.get("message")
        if not message:
            return

        chat = message.get("chat", {})
        chat_id = str(chat.get("id"))
        text = message.get("text", "").strip()
        from_user = message.get("from", {})

        if not text:
            return

        logger.info(f"Telegram buyruq ({chat_id}): {text}")

        if text.startswith("/start") or text == "🔄 Tekshirish (Status)":
            await self.handle_start(chat_id, from_user)
        elif any(k in text for k in ("Tabel", "/tabel")):
            await self.handle_tabel_report(chat_id)
        elif any(k in text for k in ("Davomati", "Bugungi Davomat", "Korxona Davomati", "/stats", "/bugun")):
            await self.handle_today_stats(chat_id)
        elif any(k in text for k in ("Kechikkan", "/late")):
            await self.handle_late_list(chat_id)
        elif any(k in text for k in ("Kelmagan", "/absent")):
            await self.handle_absent_list(chat_id)
        elif any(k in text for k in ("Excel", "/excel", "/report")):
            await self.handle_excel_report(chat_id)
        elif any(k in text for k in ("Bildirishnoma", "/notify")):
            await self.handle_toggle_notifications(chat_id)
        elif any(k in text for k in ("Qidirish", "Qidiruv", "/search")):
            await self.send_message(
                chat_id, 
                "🔍 <b>Qidirish:</b>\n\nQidirayotgan shaxsingizning F.I.SH yoki ID raqamini yozib yuboring (Masalan: <code>Alisher</code>):"
            )
        else:
            await self.handle_search(chat_id, text)

    async def _polling_loop(self):
        logger.info("Telegram Bot Polling ishga tushdi (@BurgoodAccsesCantrol_bot)...")
        timeout = 25
        
        while self.is_running:
            try:
                url = f"{self.base_url}/getUpdates"
                params = {"offset": self._last_update_id + 1, "timeout": timeout}

                async with httpx.AsyncClient(timeout=timeout + 10) as client:
                    res = await client.get(url, params=params)
                    if res.status_code == 200:
                        data = res.json()
                        if data.get("ok"):
                            updates = data.get("result", [])
                            for upd in updates:
                                self._last_update_id = upd["update_id"]
                                await self._process_update(upd)
                    elif res.status_code in (401, 404):
                        logger.error(f"Telegram Bot Token xato: {res.text}")
                        await asyncio.sleep(60)
                    else:
                        await asyncio.sleep(3)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Telegram Bot Polling xatosi: {e}")
                await asyncio.sleep(5)

    async def start(self):
        if not self.token or self.is_running:
            return
        self.is_running = True
        self._task = asyncio.create_task(self._polling_loop())

    async def stop(self):
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Telegram Bot Polling to'xtatildi.")

telegram_bot = TelegramBotService(settings.TELEGRAM_BOT_TOKEN)
