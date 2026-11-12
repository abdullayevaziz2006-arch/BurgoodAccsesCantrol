import asyncio
import logging
import json
import os
import time
from typing import Optional, Dict, Any, List

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.models import (
    TelegramUser, Organization, Group, Faculty, User, UserRole, SystemAccount
)

logger = logging.getLogger("telegram_master_bot")

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "master_config.json")
DEFAULT_WEBAPP_URL = "https://44.221.176.109.sslip.io"

def get_webapp_url() -> str:
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                url = data.get("webapp_url", "").strip().rstrip("/")
                if url:
                    return url
        except Exception:
            pass
    env_url = os.getenv("WEBAPP_URL", "").strip().rstrip("/")
    if env_url:
        return env_url
    return DEFAULT_WEBAPP_URL

def get_miniapp_url() -> str:
    base = get_webapp_url()
    # Telegram WebView eski HTML ni keshlab qolmasligi uchun doimiy yangi versiya parametri
    return f"{base}/miniapp?v={int(time.time())}"

def set_webapp_url(url: str):
    data = {}
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
    data["webapp_url"] = url.strip().rstrip("/")
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

class TelegramMasterBotService:
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
            logger.error(f"MasterBot sendMessage xatosi ({chat_id}): {e}")
            return None

    async def edit_message_text(self, chat_id: str, message_id: int, text: str, reply_markup: Optional[Dict] = None):
        url = f"{self.base_url}/editMessageText"
        payload = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "parse_mode": "HTML"
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(url, json=payload)
                return res.json()
        except Exception as e:
            logger.error(f"MasterBot editMessageText xatosi: {e}")
            return None

    async def answer_callback_query(self, callback_query_id: str, text: str = ""):
        url = f"{self.base_url}/answerCallbackQuery"
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(url, json={"callback_query_id": callback_query_id, "text": text})
        except Exception:
            pass

    async def send_document(self, chat_id: str, file_path: str, caption: str = "", filename: Optional[str] = None):
        url = f"{self.base_url}/sendDocument"
        if not os.path.exists(file_path):
            logger.error(f"Fayl topilmadi: {file_path}")
            return None
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                with open(file_path, "rb") as f:
                    fname = filename or os.path.basename(file_path)
                    files = {"document": (fname, f, "application/vnd.android.package-archive")}
                    data = {"chat_id": chat_id, "caption": caption, "parse_mode": "HTML"}
                    res = await client.post(url, data=data, files=files)
                    return res.json()
        except Exception as e:
            logger.error(f"MasterBot sendDocument xatosi ({chat_id}): {e}")
            return None

    # -------------------------------------------------------------
    # Keyboards
    # -------------------------------------------------------------
    def get_superadmin_keyboard(self) -> Dict:
        top_btn = {"text": "📱 Mini App (Boshqaruv)", "web_app": {"url": get_miniapp_url()}}

        return {
            "keyboard": [
                [top_btn],
                [{"text": "➕ Yangi Obyekt Qo'shish"}, {"text": "🏢 Obyektlar Ro'yxati"}],
                [{"text": "📱 Ilovalar & Akkauntlar (APK)"}, {"text": "➕ Xodim / Tyutor Qo'shish"}],
                [{"text": "👥 Foydalanuvchilar & Rollar"}, {"text": "⚡ Rol Biriktirish"}],
                [{"text": "📊 Umumiy Tizim Monitoringi"}]
            ],
            "resize_keyboard": True,
            "persistent": True
        }

    # -------------------------------------------------------------
    # Notification to Superadmin when new user joins Client Bot
    # -------------------------------------------------------------
    async def notify_new_user_request(self, target_chat_id: str, name: str, username: Optional[str] = None):
        """Client botga yangi foydalanuvchi kirganda Superadmin Master botiga tasdiqlash uchun yuborish"""
        superadmin_id = settings.SUPERADMIN_CHAT_ID
        uname = f"@{username}" if username else "Mavjud emas"
        text = (
            f"🔔 <b>YANGI FOYDALANUVCHI MUROJAAT QILDI!</b>\n\n"
            f"👤 <b>F.I.SH:</b> {name}\n"
            f"🆔 <b>Telegram ID:</b> <code>{target_chat_id}</code>\n"
            f"🔗 <b>Username:</b> {uname}\n\n"
            f"<i>Ushbu foydalanuvchiga qaysi rolni biriktirasiz?</i>"
        )
        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "💼 Otdel Kadr (HR)", "callback_data": f"setrole:{target_chat_id}:otdel_kadr"},
                    {"text": "👔 Bosh Direktor", "callback_data": f"setrole:{target_chat_id}:direktor"}
                ],
                [
                    {"text": "🧮 Buxgalter", "callback_data": f"setrole:{target_chat_id}:buxgalter"},
                    {"text": "🎓 Tyutor", "callback_data": f"selecttutor:{target_chat_id}"}
                ],
                [
                    {"text": "🏛 Dekan", "callback_data": f"setrole:{target_chat_id}:dekan"},
                    {"text": "👑 Rektor / Rahbariyat", "callback_data": f"setrole:{target_chat_id}:admin"}
                ],
                [
                    {"text": "❌ Rad etish (Bloklash)", "callback_data": f"setrole:{target_chat_id}:rejected"}
                ]
            ]
        }
        await self.send_message(superadmin_id, text, reply_markup=keyboard)

    # -------------------------------------------------------------
    # Command & Message Handlers
    # -------------------------------------------------------------
    async def handle_start(self, chat_id: str, user_info: Dict):
        db: Session = SessionLocal()
        try:
            # Superadmin tekshiruvi
            is_superadmin = (str(chat_id) == str(settings.SUPERADMIN_CHAT_ID))
            t_user = db.query(TelegramUser).filter(TelegramUser.chat_id == str(chat_id)).first()
            if not t_user:
                t_user = TelegramUser(
                    chat_id=str(chat_id),
                    username=user_info.get("username"),
                    first_name=user_info.get("first_name"),
                    last_name=user_info.get("last_name"),
                    role="superadmin" if is_superadmin else "pending",
                    is_active=True
                )
                db.add(t_user)
                db.commit()
            elif is_superadmin and t_user.role != "superadmin":
                t_user.role = "superadmin"
                db.commit()

            if t_user.role != "superadmin":
                await self.send_message(
                    chat_id,
                    f"⛔ <b>Kirish taqiqlandi!</b>\n"
                    f"Ushbu bot faqat tizim egasi va Superadmin uchun mo'ljallangan.\n"
                    f"Sizning Telegram ID: <code>{chat_id}</code>"
                )
                return

            inline_kb = {
                "inline_keyboard": [
                    [{"text": "🚀 Mini Appni Ochish (To'liq Boshqaruv)", "web_app": {"url": get_miniapp_url()}}]
                ]
            }

            welcome_text = (
                f"👑 <b>Burgood Access Control — Master Superadmin Boshqaruv Markazi</b>\n\n"
                f"Assalomu alaykum, <b>{user_info.get('first_name', 'Bosh Administrator')}</b>!\n\n"
                f"Bu yerdan barcha universitet va idora/korxonalar, APK & Desktop akkauntlari va "
                f"rollarni to'liq boshqarishingiz mumkin."
            )
            await self.send_message(chat_id, welcome_text, reply_markup=inline_kb)
            await self.send_message(chat_id, "Quyidagi tugmalar orqali boshqarishingiz mumkin:", reply_markup=self.get_superadmin_keyboard())

            # Telegram pastki chap burchagidagi Mini App menyu tugmasini ulash
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    await client.post(f"{self.base_url}/setChatMenuButton", json={
                        "chat_id": chat_id,
                        "menu_button": {
                            "type": "web_app",
                            "text": "📱 Mini App",
                            "web_app": {"url": get_miniapp_url()}
                        }
                    })
            except Exception:
                pass
        finally:
            db.close()

    async def handle_list_organizations(self, chat_id: str):
        db: Session = SessionLocal()
        try:
            orgs = db.query(Organization).all()
            if not orgs:
                await self.send_message(
                    chat_id, 
                    "🏢 Hozircha birorta ham obyekt kiritilmagan.\n'➕ Yangi Obyekt Qo'shish' tugmasini bosing."
                )
                return

            text = "🏢 <b>BURGOOD ACCESS CONTROL OBYEKTLARI RO'YXATI:</b>\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            for i, o in enumerate(orgs, 1):
                users_count = db.query(User).filter(User.is_active == True).count()
                bot_users_count = db.query(TelegramUser).filter(
                    TelegramUser.organization_id == o.id,
                    TelegramUser.is_active == True
                ).count()

                logo_icon = "🖼 [Yuklangan]" if o.logo_url else "⚙️ [Standart Burgood]"
                modules_str = o.modules_enabled or "Barchasi (All)"
                type_badge = "🏢 Idora / Tashkilot" if getattr(o, "org_type", "") == "company" else "🎓 Universitet / Maktab"

                text += f"<b>{i}. {o.name}</b> (ID: <code>{o.id}</code>)\n"
                text += f"   🏷 Turi: <b>{type_badge}</b>\n"
                text += f"   📍 Manzil: {o.address or 'Kiritilmagan'}\n"
                text += f"   🔑 Admin Login: <code>{o.admin_username or 'admin'}</code>\n"
                text += f"   🔒 Admin Parol: <code>{o.admin_password or 'admin123'}</code>\n"
                text += f"   🧩 Dasturlar: <code>{modules_str}</code>\n"
                text += f"   🎨 Logotip: <b>{logo_icon}</b>\n"
                text += f"   👥 Shaxslar: <b>{users_count} kishi</b> | Bot mas'ullari: <b>{bot_users_count} kishi</b>\n"
                text += f"   <i>Logo o'rnatish: Rasm yuborib captionga <code>/setlogo {o.id}</code> deb yozing</i>\n\n"

            text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            text += "💡 <b>Qo'shimcha buyruqlar:</b>\n"
            text += "• <code>/setcreds [ID] [LOGIN] [PAROL]</code> — Login/parolni o'zgartirish\n"
            text += "• <code>/setmodules [ID] [dasturlar]</code> — Dasturlarni biriktirish\n"
            text += "• <i>Rasm yuborib izohiga</i> <code>/setlogo [ID]</code> — Maxsus logo o'rnatish"

            await self.send_message(chat_id, text)
        finally:
            db.close()

    async def handle_list_users(self, chat_id: str):
        db: Session = SessionLocal()
        try:
            t_users = db.query(TelegramUser).order_by(TelegramUser.created_at.desc()).all()
            if not t_users:
                await self.send_message(chat_id, "👥 Hozircha botga birorta foydalanuvchi ulanmagan.")
                return

            role_titles = {
                "superadmin": "👑 SuperAdmin",
                "admin": "👑 Rektor / Boshliq",
                "direktor": "👔 Bosh Direktor",
                "buxgalter": "🧮 Bosh Buxgalter",
                "otdel_kadr": "💼 Otdel Kadr (HR)",
                "tutor": "🎓 Tyutor",
                "dekan": "🏛 Dekan",
                "pending": "⏳ Tasdiqlanmagan",
                "rejected": "❌ Bloklangan"
            }

            text = f"👥 <b>BOTGA ULANISH VA ROLLAR ({len(t_users)} ta):</b>\n━━━━━━━━━━━━━━━━━━━━━\n\n"
            for i, u in enumerate(t_users, 1):
                role_str = role_titles.get(u.role, u.role)
                grp_info = f" ({u.assigned_group.name})" if u.assigned_group else ""
                org_info = f" • {u.organization.name}" if u.organization else ""

                text += f"<b>{i}. {u.first_name or ''} {u.last_name or ''}</b>\n"
                text += f"   🆔 ID: <code>{u.chat_id}</code> | @{u.username or '-'}\n"
                text += f"   📌 Rol: <b>{role_str}{grp_info}</b>{org_info}\n\n"

            text += "<i>Rolni o'zgartirish uchun: /assign [ID] [rol] buyrug'idan foydalaning.</i>"
            await self.send_message(chat_id, text)
        finally:
            db.close()

    async def handle_add_org_prompt(self, chat_id: str):
        text = (
            "➕ <b>YANGI OBYEKT QO'SHISH (Universitet yoki Idora / Korxona):</b>\n\n"
            "Tizimimiz 2 xil obyektni qo'llab-quvvatlaydi:\n\n"
            "🎓 <b>1. Universitet / Maktab (Ta'lim):</b>\n"
            "Talabalar, Guruhlar, Fakultetlar, Tyutorlar va Xodimlar bilan.\n"
            "Buyruq: <code>/newuniv Universitet Nomi, admin_login, admin_parol</code>\n"
            "<i>Masalan: <code>/newuniv Urganch Davlat Universiteti, urdu_admin, urdu2026</code></i>\n\n"
            "🏢 <b>2. Idora / Tashkilot / Korxona:</b>\n"
            "Faqat xodimlar, bo'limlar, lavozimlar, oylik Tabel, Buxgalteriya va Direktor.\n"
            "Buyruq: <code>/newoffice Tashkilot Nomi, admin_login, admin_parol</code>\n"
            "<i>Masalan: <code>/newoffice Oltin Voha MCHJ, voha_admin, voha2026</code></i>\n\n"
            "💡 <i>Shuningdek, <b>📱 Mini App (Boshqaruv)</b> orqali ham vizual belgilab qo'shishingiz mumkin.</i>"
        )
        await self.send_message(chat_id, text)

    async def handle_create_org(self, chat_id: str, cmd_text: str):
        cleaned = cmd_text.replace("/newoffice", "").replace("/newuniv", "").replace("/neworg", "").strip()
        parts = cleaned.split(",")
        if not parts or not parts[0].strip():
            await self.send_message(
                chat_id, 
                "❌ Noto'g'ri format.\n\n"
                "Universitet uchun: <code>/newuniv Universitet Nomi, admin_login, admin_parol</code>\n"
                "Idora/Korxona uchun: <code>/newoffice Tashkilot Nomi, admin_login, admin_parol</code>"
            )
            return

        name = parts[0].strip()
        if "/newoffice" in cmd_text:
            org_type = "company"
            admin_user = parts[1].strip() if len(parts) > 1 and parts[1].strip() else "admin"
            admin_pass = parts[2].strip() if len(parts) > 2 and parts[2].strip() else "admin123"
        elif "/newuniv" in cmd_text:
            org_type = "university"
            admin_user = parts[1].strip() if len(parts) > 1 and parts[1].strip() else "admin"
            admin_pass = parts[2].strip() if len(parts) > 2 and parts[2].strip() else "admin123"
        else: # /neworg
            type_indicator = parts[1].strip().lower() if len(parts) > 1 else ""
            if any(k in type_indicator for k in ["office", "company", "idora", "tashkilot", "korxona"]):
                org_type = "company"
                admin_user = parts[2].strip() if len(parts) > 2 and parts[2].strip() else "admin"
                admin_pass = parts[3].strip() if len(parts) > 3 and parts[3].strip() else "admin123"
            else:
                org_type = "university"
                admin_user = parts[1].strip() if len(parts) > 1 and parts[1].strip() else "admin"
                admin_pass = parts[2].strip() if len(parts) > 2 and parts[2].strip() else "admin123"

        if org_type == "company":
            modules = "dashboard,staff,structure,attendance,tabel,settings"
            type_label = "🏢 Idora / Tashkilot / Korxona (Faqat xodimlar va Tabel)"
        else:
            modules = "dashboard,students,staff,structure,attendance,settings"
            type_label = "🎓 Universitet / Maktab (Talabalar va Tyutorlar)"

        db: Session = SessionLocal()
        try:
            existing = db.query(Organization).filter(Organization.name == name).first()
            if existing:
                await self.send_message(chat_id, f"⚠️ '<b>{name}</b>' allaqachon ro'yxatda mavjud (ID: {existing.id})!")
                return

            new_org = Organization(
                name=name, 
                code=name[:4].upper(),
                org_type=org_type,
                admin_username=admin_user,
                admin_password=admin_pass,
                modules_enabled=modules,
                is_active=True
            )
            db.add(new_org)
            db.commit()
            db.refresh(new_org)

            reply = (
                f"✅ <b>YANGI OBYEKT MUVAFFAQIYATLI QO'SHILDI!</b>\n\n"
                f"🏢 <b>Nomi:</b> {new_org.name}\n"
                f"🏷 <b>Turi:</b> {type_label}\n"
                f"🆔 <b>Obyekt ID:</b> <code>{new_org.id}</code>\n"
                f"🔑 <b>Admin Login:</b> <code>{new_org.admin_username}</code>\n"
                f"🔒 <b>Admin Parol:</b> <code>{new_org.admin_password}</code>\n"
                f"🧩 <b>Qo'llaniladigan modullar:</b> <code>{new_org.modules_enabled}</code>\n\n"
                f"🖼 <b>MAXSUS LOGO O'RNATISH:</b>\n"
                f"Logotip rasmini yuborib izohiga <code>/setlogo {new_org.id}</code> deb yozing!"
            )
            await self.send_message(chat_id, reply)
        finally:
            db.close()

    async def handle_set_logo(self, chat_id: str, org_id: int, file_id: str):
        """Telegramdan yuborilgan rasmni yuklab olib, o'sha obyekt logosi qilib o'rnatish"""
        try:
            # 1. Telegram getFile API
            async with httpx.AsyncClient(timeout=20.0) as client:
                res = await client.get(f"{self.base_url}/getFile", params={"file_id": file_id})
                if res.status_code != 200:
                    await self.send_message(chat_id, "❌ Rasmni Telegram serveridan yuklab bo'lmadi.")
                    return
                data = res.json()
                file_path = data.get("result", {}).get("file_path")
                if not file_path:
                    await self.send_message(chat_id, "❌ Fayl yo'li aniqlanmadi.")
                    return

                # 2. Faylning o'zini yuklab olish
                download_url = f"https://api.telegram.org/file/bot{self.token}/{file_path}"
                img_res = await client.get(download_url)
                if img_res.status_code != 200:
                    await self.send_message(chat_id, "❌ Faylni yuklab olishda xatolik bo'ldi.")
                    return

            # 3. Faylni serverga saqlash
            import os
            os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
            ext = os.path.splitext(file_path)[1] or ".png"
            filename = f"org_{org_id}_logo{ext}"
            saved_disk_path = os.path.join(settings.UPLOAD_DIR, filename)
            
            with open(saved_disk_path, "wb") as f:
                f.write(img_res.content)

            # 4. Bazada yangilash
            db: Session = SessionLocal()
            try:
                org = db.query(Organization).filter(Organization.id == org_id).first()
                if not org:
                    await self.send_message(chat_id, f"❌ ID: <code>{org_id}</code> bo'lgan obyekt topilmadi.")
                    return

                org.logo_url = f"/uploads/{filename}"
                db.commit()

                await self.send_message(
                    chat_id,
                    f"🎉 <b>MAXSUS LOGOTIP O'RNATILDI!</b>\n\n"
                    f"🏢 <b>Obyekt:</b> {org.name}\n"
                    f"🆔 <b>ID:</b> <code>{org.id}</code>\n"
                    f"🖼 <b>Logotip fayli:</b> <code>/uploads/{filename}</code>\n\n"
                    f"✅ Endi ushbu tashkilotning dasturlarida (Desktop, Web, Mobil) "
                    f"<b>faqat siz kiritgan ushbu logotip</b> aks etadi!"
                )
            finally:
                db.close()
        except Exception as e:
            logger.error(f"handle_set_logo xatosi: {e}")
            await self.send_message(chat_id, f"❌ Logo yuklashda xatolik yuz berdi: {e}")

    async def handle_set_creds(self, chat_id: str, cmd_text: str):
        # Format: /setcreds <org_id> <login> <parol>
        parts = cmd_text.split()
        if len(parts) < 4:
            await self.send_message(
                chat_id, 
                "Format: <code>/setcreds [OBYEKT_ID] [YANGI_LOGIN] [YANGI_PAROL]</code>\n"
                "Masalan: <code>/setcreds 1 urdu_admin 2026pass</code>"
            )
            return

        try:
            org_id = int(parts[1])
            new_login = parts[2].strip()
            new_pass = parts[3].strip()
        except ValueError:
            await self.send_message(chat_id, "❌ Obyekt ID raqam bo'lishi kerak!")
            return

        db: Session = SessionLocal()
        try:
            org = db.query(Organization).filter(Organization.id == org_id).first()
            if not org:
                await self.send_message(chat_id, f"❌ ID: <code>{org_id}</code> bo'lgan obyekt topilmadi.")
                return

            org.admin_username = new_login
            org.admin_password = new_pass
            db.commit()

            await self.send_message(
                chat_id,
                f"✅ <b>Login va Parol yangilandi!</b>\n\n"
                f"🏢 <b>Obyekt:</b> {org.name}\n"
                f"🔑 <b>Yangi Login:</b> <code>{org.admin_username}</code>\n"
                f"🔒 <b>Yangi Parol:</b> <code>{org.admin_password}</code>"
            )
        finally:
            db.close()

    async def handle_set_modules(self, chat_id: str, cmd_text: str):
        # Format: /setmodules <org_id> <modules>
        parts = cmd_text.split(maxsplit=2)
        if len(parts) < 3:
            await self.send_message(
                chat_id, 
                "Format: <code>/setmodules [OBYEKT_ID] [modullar]</code>\n"
                "Masalan: <code>/setmodules 1 attendance,students,staff</code> yoki <code>/setmodules 1 all</code>"
            )
            return

        try:
            org_id = int(parts[1])
            raw_mods = parts[2].strip()
        except ValueError:
            await self.send_message(chat_id, "❌ Obyekt ID raqam bo'lishi kerak!")
            return

        modules = "dashboard,students,staff,structure,attendance,settings" if raw_mods.lower() == "all" else raw_mods

        db: Session = SessionLocal()
        try:
            org = db.query(Organization).filter(Organization.id == org_id).first()
            if not org:
                await self.send_message(chat_id, f"❌ ID: <code>{org_id}</code> bo'lgan obyekt topilmadi.")
                return

            org.modules_enabled = modules
            db.commit()

            await self.send_message(
                chat_id,
                f"✅ <b>Dastur modullari yangilandi!</b>\n\n"
                f"🏢 <b>Obyekt:</b> {org.name}\n"
                f"🧩 <b>Ruxsat etilgan dasturlar:</b> <code>{org.modules_enabled}</code>"
            )
        finally:
            db.close()

    async def handle_assign_command(self, chat_id: str, text: str):
        # Format: /assign <target_chat_id> <role> [group_name]
        # Masalan: /assign 987654321 otdel_kadr
        # Masalan: /assign 987654321 tutor 941-21
        parts = text.split()
        if len(parts) < 3:
            help_text = (
                "⚡ <b>Foydalanuvchiga rol biriktirish qo'llanmasi:</b>\n\n"
                "Format: <code>/assign [TELEGRAM_ID] [ROL] [GURUH_NOMI]</code>\n\n"
                "<b>Mavjud rollar:</b>\n"
                "• <code>direktor</code> — Bosh direktor (tashkilot/idoralar uchun)\n"
                "• <code>buxgalter</code> — Bosh buxgalter (tabel & davomat)\n"
                "• <code>otdel_kadr</code> — Faqat xodimlarni ko'radi (talabalar yashiriladi)\n"
                "• <code>tutor</code> — Faqat o'z guruhini ko'radi (masalan: <code>/assign 12345 tutor 941-21</code>)\n"
                "• <code>dekan</code> — Fakultetini ko'radi\n"
                "• <code>admin</code> — Rektor / Boshliq (to'liq ko'radi)\n"
                "• <code>rejected</code> — Bloklash"
            )
            await self.send_message(chat_id, help_text)
            return

        target_id = parts[1].strip()
        role = parts[2].strip().lower()
        extra = parts[3].strip() if len(parts) > 3 else None

        valid_roles = ["direktor", "buxgalter", "otdel_kadr", "tutor", "dekan", "admin", "superadmin", "rejected"]
        if role not in valid_roles:
            await self.send_message(chat_id, f"❌ Noto'g'ri rol. Mavjud rollar: {', '.join(valid_roles)}")
            return

        db: Session = SessionLocal()
        try:
            target_user = db.query(TelegramUser).filter(TelegramUser.chat_id == target_id).first()
            if not target_user:
                target_user = TelegramUser(chat_id=target_id, role=role, is_active=True)
                db.add(target_user)
            else:
                target_user.role = role

            # Agar tyutor bo'lsa va guruh nomi berilgan bo'lsa
            if role == "tutor" and extra:
                grp = db.query(Group).filter(Group.name.ilike(f"%{extra}%")).first()
                if grp:
                    target_user.assigned_group_id = grp.id

            db.commit()

            role_titles = {
                "direktor": "👔 Bosh Direktor",
                "buxgalter": "🧮 Bosh Buxgalter",
                "otdel_kadr": "💼 Otdel Kadr (HR - Faqat xodimlar)",
                "tutor": f"🎓 Tyutor (Guruh: {extra or 'barcha'})",
                "dekan": "🏛 Dekan",
                "admin": "👑 Rektor / Boshqaruvchi",
                "rejected": "❌ Bloklangan"
            }

            await self.send_message(
                chat_id, 
                f"✅ <b>Foydalanuvchi muvaffaqiyatli yangilandi!</b>\n"
                f"🆔 ID: <code>{target_id}</code>\n"
                f"📌 Yangi Rol: <b>{role_titles.get(role, role)}</b>"
            )

            # Client bot orqali o'sha foydalanuvchiga xabar yuborish
            from app.services.telegram_bot import telegram_bot
            if role == "rejected":
                await telegram_bot.send_message(target_id, "❌ Sizning akkauntingiz administrator tomonidan bloklandi.")
            else:
                notify_client = (
                    f"🎉 <b>Tabriklaymiz! Sizga tizimda rol biriktirildi.</b>\n\n"
                    f"📌 <b>Sizning rolingiz:</b> {role_titles.get(role, role)}\n\n"
                    f"Quyidagi menyu orqali o'zingizga tegishli davomat hisobotlaridan foydalanishingiz mumkin:"
                )
                await telegram_bot.send_message(target_id, notify_client, reply_markup=telegram_bot.get_keyboard_for_user(target_user))
        finally:
            db.close()

    # -------------------------------------------------------------
    # System Account Handlers (Tyutorlar, Kadrlar, APK Login/Parollar)
    # -------------------------------------------------------------
    async def handle_list_accounts(self, chat_id: str):
        db: Session = SessionLocal()
        try:
            accounts = db.query(SystemAccount).order_by(SystemAccount.created_at.desc()).all()
            if not accounts:
                await self.send_message(
                    chat_id,
                    "📱 <b>Hozircha birorta ham APK/Desktop akkaunti yaratilmagan.</b>\n\n"
                    "➕ Yangi Tyutor yoki Kadr qo'shish uchun pastdagi '➕ Tyutor / Kadr Qo'shish' tugmasini bosing yoki Mini Appdan foydalaning."
                )
                return

            text = f"📱 <b>ILOVA AKKAUNTLARI (APK & PC) — {len(accounts)} ta:</b>\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            for i, a in enumerate(accounts, 1):
                role_icon = "🎓 Tyutor" if a.role == "tutor" else ("💼 Otdel Kadr" if a.role == "otdel_kadr" else a.role)
                grp_info = f"\n   👥 Guruh: <b>{a.assigned_group.name}</b>" if a.assigned_group else ""
                status_icon = "🟢 Faol" if a.is_active else "🔴 Bloklangan"
                apps_info = a.allowed_apps or "desktop,android"

                text += f"<b>{i}. {a.full_name}</b> (ID: <code>{a.id}</code>)\n"
                text += f"   📌 Rol: <b>{role_icon}</b>{grp_info}\n"
                text += f"   🔑 Login: <code>{a.username}</code>\n"
                text += f"   🔒 Parol: <code>{a.password}</code>\n"
                text += f"   📲 Dasturlar: <code>{apps_info}</code> | {status_icon}\n\n"

            text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            text += "💡 <b>Tezkor buyruqlar:</b>\n"
            text += "• <code>/delaccount [ID]</code> — Akkauntni o'chirish\n"
            text += "• Barcha rollar va guruhlarni to'liq vizual boshqarish uchun: <b>📱 Mini App</b> tugmasini bosing."

            await self.send_message(chat_id, text)
        finally:
            db.close()

    async def handle_add_account_prompt(self, chat_id: str):
        text = (
            "➕ <b>YANGI AKKAUNT QO'SHISH (Universitet yoki Idora / Korxona):</b>\n\n"
            "Siz 2 xil usulda qo'shishingiz mumkin:\n\n"
            "<b>1-usul (Telegram Mini App orqali — Eng qulay va tezkor):</b>\n"
            "Pastdagi <b>'📱 Mini App (Boshqaruv)'</b> tugmasini bosing va <b>'Foydalanuvchilar & Rollar'</b> bo'limida 'Yangi Foydalanuvchi' tugmasini bosing.\n\n"
            "<b>2-usul (Shu botga to'g'ridan-to'g'ri buyruq yuborish orqali):</b>\n"
            "🏢 <b>Idora / Tashkilot uchun rollar:</b>\n"
            "• 👔 <b>Direktor:</b> <code>/newdirektor Ism Familiya, login, parol</code>\n"
            "• 🧮 <b>Buxgalter:</b> <code>/newbuxgalter Ism Familiya, login, parol</code>\n"
            "• 💼 <b>Otdel Kadr (HR):</b> <code>/newkadr Ism Familiya, login, parol</code>\n\n"
            "🎓 <b>Universitet / Maktab uchun rollar:</b>\n"
            "• 🎓 <b>Tyutor:</b> <code>/newtutor Ism Familiya, Guruh_Nomi, login, parol</code>\n"
            "• 💼 <b>Otdel Kadr (HR):</b> <code>/newkadr Ism Familiya, login, parol</code>"
        )
        await self.send_message(chat_id, text)

    async def handle_create_tutor(self, chat_id: str, cmd_text: str):
        parts = cmd_text.replace("/newtutor", "").strip().split(",")
        if len(parts) < 4:
            await self.send_message(
                chat_id,
                "❌ Format: <code>/newtutor [F.I.SH], [GURUH_NOMI], [LOGIN], [PAROL]</code>\n\n"
                "Masalan:\n<code>/newtutor Akmal Valiyev, 941-21, tutor_akmal, 123456</code>"
            )
            return

        full_name = parts[0].strip()
        group_name = parts[1].strip()
        username = parts[2].strip()
        password = parts[3].strip()

        db: Session = SessionLocal()
        try:
            # Guruhni topish
            grp = db.query(Group).filter(Group.name.ilike(f"%{group_name}%")).first()
            if not grp:
                await self.send_message(
                    chat_id,
                    f"❌ '<b>{group_name}</b>' nomli guruh topilmadi! Iltimos, guruh nomini tekshiring."
                )
                return

            chk = db.query(SystemAccount).filter(SystemAccount.username == username).first()
            if chk:
                await self.send_message(chat_id, f"❌ '<code>{username}</code>' logini band! Boshqa login tanlang.")
                return

            first_org = db.query(Organization).first()
            org_id = first_org.id if first_org else None

            account = SystemAccount(
                full_name=full_name,
                username=username,
                password=password,
                role="tutor",
                organization_id=org_id,
                assigned_group_id=grp.id,
                allowed_apps="android,bot",
                allowed_modules="attendance,students",
                is_active=True
            )
            db.add(account)
            db.commit()

            reply = (
                f"🎉 <b>YANGI TYUTOR AKKAUNTI YARATILDI!</b>\n\n"
                f"👤 <b>F.I.SH:</b> {full_name}\n"
                f"👥 <b>Biriktirilgan Guruh:</b> {grp.name}\n"
                f"🔑 <b>APK Login:</b> <code>{username}</code>\n"
                f"🔒 <b>APK Parol:</b> <code>{password}</code>\n"
                f"📲 <b>Ruxsat etilgan ilova:</b> <code>android,bot</code>\n\n"
                f"✅ Ushbu tyutor telefondagi APK ga ushbu login/parol bilan kirganda, "
                f"<b>faqat o'zining {grp.name} guruhi talabalari va davomatini</b> ko'radi!"
            )
            await self.send_message(chat_id, reply)
        finally:
            db.close()

    async def handle_create_kadr(self, chat_id: str, cmd_text: str):
        parts = cmd_text.replace("/newkadr", "").strip().split(",")
        if len(parts) < 3:
            await self.send_message(
                chat_id,
                "❌ Format: <code>/newkadr [F.I.SH], [LOGIN], [PAROL]</code>\n\n"
                "Masalan:\n<code>/newkadr Nodira Karimova, kadr_nodira, 123456</code>"
            )
            return

        full_name = parts[0].strip()
        username = parts[1].strip()
        password = parts[2].strip()

        db: Session = SessionLocal()
        try:
            chk = db.query(SystemAccount).filter(SystemAccount.username == username).first()
            if chk:
                await self.send_message(chat_id, f"❌ '<code>{username}</code>' logini band! Boshqa login tanlang.")
                return

            first_org = db.query(Organization).first()
            org_id = first_org.id if first_org else None

            account = SystemAccount(
                full_name=full_name,
                username=username,
                password=password,
                role="otdel_kadr",
                organization_id=org_id,
                allowed_apps="android,desktop",
                allowed_modules="attendance,staff",
                is_active=True
            )
            db.add(account)
            db.commit()

            reply = (
                f"🎉 <b>YANGI OTDEL KADR AKKAUNTI YARATILDI!</b>\n\n"
                f"👤 <b>F.I.SH:</b> {full_name}\n"
                f"📌 <b>Roli:</b> Otdel Kadr (HR)\n"
                f"🔑 <b>Login:</b> <code>{username}</code>\n"
                f"🔒 <b>Parol:</b> <code>{password}</code>\n"
                f"📲 <b>Ruxsat etilgan ilova:</b> <code>android, desktop</code>\n\n"
                f"✅ Ushbu xodim APK va Desktopga kirganda, <b>faqat xodimlar davomati va keldi-ketdisini</b> ko'radi."
            )
            await self.send_message(chat_id, reply)
        finally:
            db.close()

    async def handle_create_direktor(self, chat_id: str, cmd_text: str):
        parts = cmd_text.replace("/newdirektor", "").strip().split(",")
        if len(parts) < 3:
            await self.send_message(
                chat_id,
                "❌ Format: <code>/newdirektor [F.I.SH], [LOGIN], [PAROL]</code>\n\n"
                "Masalan:\n<code>/newdirektor Rustam Rahimov, dir_rustam, dir2026</code>"
            )
            return

        full_name = parts[0].strip()
        username = parts[1].strip()
        password = parts[2].strip()

        db: Session = SessionLocal()
        try:
            chk = db.query(SystemAccount).filter(SystemAccount.username == username).first()
            if chk:
                await self.send_message(chat_id, f"❌ '<code>{username}</code>' logini band! Boshqa login tanlang.")
                return

            first_org = db.query(Organization).first()
            org_id = first_org.id if first_org else None

            account = SystemAccount(
                full_name=full_name,
                username=username,
                password=password,
                role="direktor",
                organization_id=org_id,
                allowed_apps="android,desktop,bot",
                allowed_modules="dashboard,staff,structure,attendance,tabel",
                is_active=True
            )
            db.add(account)
            db.commit()

            reply = (
                f"🎉 <b>YANGI BOSH DIREKTOR AKKAUNTI YARATILDI!</b>\n\n"
                f"👤 <b>F.I.SH:</b> {full_name}\n"
                f"📌 <b>Roli:</b> 👔 Bosh Direktor\n"
                f"🔑 <b>Login:</b> <code>{username}</code>\n"
                f"🔒 <b>Parol:</b> <code>{password}</code>\n"
                f"📲 <b>Ruxsat etilgan ilova:</b> <code>android, desktop, bot</code>\n\n"
                f"✅ Ushbu rahbar korxona xodimlari davomati, oylik Tabel va o'tishlarini to'liq kuzata oladi."
            )
            await self.send_message(chat_id, reply)
        finally:
            db.close()

    async def handle_create_buxgalter(self, chat_id: str, cmd_text: str):
        parts = cmd_text.replace("/newbuxgalter", "").strip().split(",")
        if len(parts) < 3:
            await self.send_message(
                chat_id,
                "❌ Format: <code>/newbuxgalter [F.I.SH], [LOGIN], [PAROL]</code>\n\n"
                "Masalan:\n<code>/newbuxgalter Umida Rahimova, bux_umida, bux2026</code>"
            )
            return

        full_name = parts[0].strip()
        username = parts[1].strip()
        password = parts[2].strip()

        db: Session = SessionLocal()
        try:
            chk = db.query(SystemAccount).filter(SystemAccount.username == username).first()
            if chk:
                await self.send_message(chat_id, f"❌ '<code>{username}</code>' logini band! Boshqa login tanlang.")
                return

            first_org = db.query(Organization).first()
            org_id = first_org.id if first_org else None

            account = SystemAccount(
                full_name=full_name,
                username=username,
                password=password,
                role="buxgalter",
                organization_id=org_id,
                allowed_apps="android,desktop,bot",
                allowed_modules="attendance,tabel,staff",
                is_active=True
            )
            db.add(account)
            db.commit()

            reply = (
                f"🎉 <b>YANGI BUXGALTER AKKAUNTI YARATILDI!</b>\n\n"
                f"👤 <b>F.I.SH:</b> {full_name}\n"
                f"📌 <b>Roli:</b> 🧮 Bosh Buxgalter\n"
                f"🔑 <b>Login:</b> <code>{username}</code>\n"
                f"🔒 <b>Parol:</b> <code>{password}</code>\n"
                f"📲 <b>Ruxsat etilgan ilova:</b> <code>android, desktop, bot</code>\n\n"
                f"✅ Ushbu buxgalter oylik ish vaqti tabeli, kechikishlar va ishlangan soatlar hisobotini oladi."
            )
            await self.send_message(chat_id, reply)
        finally:
            db.close()

    async def handle_delete_account(self, chat_id: str, cmd_text: str):
        parts = cmd_text.split()
        if len(parts) < 2 or not parts[1].isdigit():
            await self.send_message(chat_id, "Format: <code>/delaccount [AKKAUNT_ID]</code>")
            return

        acc_id = int(parts[1])
        db: Session = SessionLocal()
        try:
            acc = db.query(SystemAccount).filter(SystemAccount.id == acc_id).first()
            if not acc:
                await self.send_message(chat_id, f"❌ ID: <code>{acc_id}</code> bo'lgan akkaunt topilmadi!")
                return

            db.delete(acc)
            db.commit()
            await self.send_message(chat_id, f"🗑 <b>Akkaunt ({acc.full_name} - {acc.username}) o'chirildi!</b>")
        finally:
            db.close()

    # -------------------------------------------------------------
    # Inline Callback Handlers (Tugmalar bosilganda)
    # -------------------------------------------------------------
    async def handle_callback_query(self, callback: Dict):
        cb_id = callback.get("id")
        data = callback.get("data", "")
        message = callback.get("message", {})
        msg_id = message.get("message_id")
        chat_id = str(message.get("chat", {}).get("id"))

        await self.answer_callback_query(cb_id)

        if data.startswith("setrole:"):
            # format: setrole:TARGET_ID:ROLE
            _, target_id, role = data.split(":")
            await self._apply_role(chat_id, msg_id, target_id, role)

        elif data.startswith("selecttutor:"):
            # Tyutor uchun guruh tanlash menyusini chiqarish
            _, target_id = data.split(":")
            db: Session = SessionLocal()
            try:
                groups = db.query(Group).limit(10).all()
                buttons = []
                for g in groups:
                    buttons.append([{"text": f"👥 {g.name}", "callback_data": f"settutorgroup:{target_id}:{g.id}"}])
                buttons.append([{"text": "« Orqaga", "callback_data": f"backtoroles:{target_id}"}])

                keyboard = {"inline_keyboard": buttons}
                await self.edit_message_text(
                    chat_id, msg_id, 
                    f"🎓 <b>Tyutor (ID: {target_id}) uchun guruhni tanlang:</b>",
                    reply_markup=keyboard
                )
            finally:
                db.close()

        elif data.startswith("settutorgroup:"):
            _, target_id, group_id = data.split(":")
            await self._apply_tutor_role(chat_id, msg_id, target_id, int(group_id))

        elif data == "prompt_set_app_url":
            await self.send_message(
                chat_id,
                "🌐 <b>Mini App manzilini kiritish:</b>\n\n"
                "Cloudflare Tunnel yoki tashqi domeningiz havolasini quyidagi formatda yuboring:\n"
                "<code>/setappurl https://sizning-domen.uz</code>\n\n"
                "<i>Masalan: <code>/setappurl https://my-server.trycloudflare.com</code></i>"
            )

    async def handle_set_app_url(self, chat_id: str, cmd_text: str):
        parts = cmd_text.split()
        if len(parts) < 2 or not parts[1].startswith("http"):
            await self.send_message(
                chat_id,
                "Format: <code>/setappurl https://sizning-domeningiz.uz</code>\n\n"
                "<i>Cloudflare Tunnel yoki tashqi domen havolasini yuboring.</i>"
            )
            return

        url = parts[1].strip().rstrip("/")
        set_webapp_url(url)

        # Telegram Chat Menu tugmasini sozlash
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                await client.post(f"{self.base_url}/setChatMenuButton", json={
                    "chat_id": chat_id,
                    "menu_button": {
                        "type": "web_app",
                        "text": "📱 Mini App",
                        "web_app": {"url": get_miniapp_url()}
                    }
                })
        except Exception as e:
            logger.error(f"setChatMenuButton xatosi: {e}")

        inline_kb = {
            "inline_keyboard": [
                [{"text": "🚀 Mini Appni Ochish", "web_app": {"url": get_miniapp_url()}}]
            ]
        }
        await self.send_message(
            chat_id,
            f"✅ <b>Mini App havolasi muvaffaqiyatli saqlandi!</b>\n\n"
            f"🌐 <b>Manzil:</b> <code>{url}/miniapp</code>\n\n"
            f"Endi Telegram orqali barcha obyektlar, Desktop & APK login-parollari va "
            f"rollarni to'liq vizual boshqarishingiz mumkin!",
            reply_markup=inline_kb
        )
        await self.send_message(chat_id, "Pastdagi menyu yangilandi:", reply_markup=self.get_superadmin_keyboard())

    async def handle_open_miniapp(self, chat_id: str):
        webapp_url = get_webapp_url()
        if webapp_url:
            inline_kb = {
                "inline_keyboard": [
                    [{"text": "🚀 Mini Appni Ochish", "web_app": {"url": get_miniapp_url()}}]
                ]
            }
            await self.send_message(
                chat_id,
                "📱 <b>Burgood Master Boshqaruv Mini Appi</b>\n\n"
                "Desktop, Bot va APK ilovalar uchun barcha login, parol, "
                "modul va rollarni boshqarish uchun pastdagi tugmani bosing:",
                reply_markup=inline_kb
            )
        else:
            await self.send_message(
                chat_id,
                "⚙️ <b>Mini App havolasi hali kiritilmagan!</b>\n\n"
                "Cloudflare Tunnel yoki tashqi domeningiz havolasini quyidagicha yuboring:\n"
                "<code>/setappurl https://sizning-domeningiz.uz</code>\n\n"
                "Shunda tugma avtomatik faollashadi va to'liq ekranli Mini App ochiladi!"
            )

    async def _apply_role(self, admin_chat_id: str, msg_id: int, target_id: str, role: str):
        db: Session = SessionLocal()
        try:
            target_user = db.query(TelegramUser).filter(TelegramUser.chat_id == str(target_id)).first()
            if not target_user:
                target_user = TelegramUser(chat_id=str(target_id), role=role, is_active=True)
                db.add(target_user)
            else:
                target_user.role = role
                target_user.is_active = (role != "rejected")
            db.commit()

            role_titles = {
                "direktor": "👔 Bosh Direktor",
                "buxgalter": "🧮 Bosh Buxgalter",
                "otdel_kadr": "💼 Otdel Kadr (HR — Faqat xodimlar)",
                "admin": "👑 Rektor / Rahbariyat",
                "dekan": "🏛 Dekan",
                "rejected": "❌ Rad etilgan"
            }

            await self.edit_message_text(
                admin_chat_id, msg_id,
                f"✅ <b>Foydalanuvchi tasdiqlandi!</b>\n"
                f"🆔 ID: <code>{target_id}</code>\n"
                f"📌 Belgilangan Rol: <b>{role_titles.get(role, role)}</b>"
            )

            from app.services.telegram_bot import telegram_bot
            if role == "rejected":
                await telegram_bot.send_message(target_id, "❌ Sizning arizangiz administrator tomonidan rad etildi.")
            else:
                msg = (
                    f"🎉 <b>Tabriklaymiz! Sizning akkauntingiz tasdiqlandi.</b>\n\n"
                    f"📌 <b>Rol:</b> {role_titles.get(role, role)}\n"
                    f"Davomat ma'lumotlarini olish uchun quyidagi menyudan foydalaning:"
                )
                await telegram_bot.send_message(target_id, msg, reply_markup=telegram_bot.get_keyboard_for_user(target_user))
        finally:
            db.close()

    async def _apply_tutor_role(self, admin_chat_id: str, msg_id: int, target_id: str, group_id: int):
        db: Session = SessionLocal()
        try:
            grp = db.query(Group).filter(Group.id == group_id).first()
            grp_name = grp.name if grp else "Guruh"

            target_user = db.query(TelegramUser).filter(TelegramUser.chat_id == str(target_id)).first()
            if not target_user:
                target_user = TelegramUser(chat_id=str(target_id), role="tutor", assigned_group_id=group_id, is_active=True)
                db.add(target_user)
            else:
                target_user.role = "tutor"
                target_user.assigned_group_id = group_id
                target_user.is_active = True
            db.commit()

            await self.edit_message_text(
                admin_chat_id, msg_id,
                f"✅ <b>Tyutor tasdiqlandi!</b>\n"
                f"🆔 ID: <code>{target_id}</code>\n"
                f"👥 Biriktirilgan guruh: <b>{grp_name}</b>\n"
                f"<i>Endi u faqat o'z guruhining davomatini ko'radi.</i>"
            )

            from app.services.telegram_bot import telegram_bot
            msg = (
                f"🎉 <b>Tabriklaymiz! Sizga Tyutorlik roli biriktirildi.</b>\n\n"
                f"👥 <b>Sizning guruhingiz:</b> {grp_name}\n"
                f"Siz faqat o'z guruhingiz talabalarining kirish-chiqish va kechikishlarini ko'rishingiz mumkin."
            )
            await telegram_bot.send_message(target_id, msg, reply_markup=telegram_bot.get_keyboard_for_user(target_user))
        finally:
            db.close()

    # -------------------------------------------------------------
    # Polling Loop
    # -------------------------------------------------------------
    async def _process_update(self, update: Dict):
        if "callback_query" in update:
            await self.handle_callback_query(update["callback_query"])
            return

        message = update.get("message")
        if not message:
            return

        chat = message.get("chat", {})
        chat_id = str(chat.get("id"))
        from_user = message.get("from", {})
        text = message.get("text", "").strip()
        photos = message.get("photo")
        caption = message.get("caption", "").strip()

        # 1. Rasm yuborilganda (Logotip o'rnatish)
        if photos:
            largest_photo = photos[-1]
            file_id = largest_photo.get("file_id")
            
            # Captionda /setlogo ID tekshirish
            if caption.startswith("/setlogo") or caption.startswith("/logo") or caption.startswith("logo"):
                parts = caption.split()
                if len(parts) >= 2 and parts[1].isdigit():
                    org_id = int(parts[1])
                    await self.handle_set_logo(chat_id, org_id, file_id)
                    return
            
            await self.send_message(
                chat_id,
                "🖼 <b>Logotip rasmi qabul qilindi!</b>\n\n"
                "Ushbu logotip qaysi universitet/korxonaga tegishli ekanligini bildirish uchun, "
                "rasm izohiga (caption) quyidagicha yozib qaytadan yuboring:\n"
                "<code>/setlogo [OBYEKT_ID]</code>\n\n"
                "<i>Masalan: <code>/setlogo 1</code></i>\n"
                "Obyektlar ID sini bilish uchun '🏢 Obyektlar (Universitetlar)' tugmasini bosing."
            )
            return

        if not text:
            return

        logger.info(f"MasterBot buyruq ({chat_id}): {text}")

        if text.startswith("/start"):
            await self.handle_start(chat_id, from_user)
        elif text.startswith("/setappurl"):
            await self.handle_set_app_url(chat_id, text)
        elif text.startswith("📱 Mini App") or text.startswith("/miniapp"):
            await self.handle_open_miniapp(chat_id)
        elif text == "📱 Ilovalar & Akkauntlar (APK)" or text.startswith("/accounts") or text.startswith("/listaccounts"):
            await self.handle_list_accounts(chat_id)
        elif text in ["➕ Xodim / Tyutor Qo'shish", "➕ Tyutor / Kadr Qo'shish"]:
            await self.handle_add_account_prompt(chat_id)
        elif text.startswith("/newtutor"):
            await self.handle_create_tutor(chat_id, text)
        elif text.startswith("/newkadr"):
            await self.handle_create_kadr(chat_id, text)
        elif text.startswith("/newdirektor"):
            await self.handle_create_direktor(chat_id, text)
        elif text.startswith("/newbuxgalter"):
            await self.handle_create_buxgalter(chat_id, text)
        elif text.startswith("/delaccount"):
            await self.handle_delete_account(chat_id, text)
        elif text in ["🏢 Obyektlar Ro'yxati", "🏢 Obyektlar (Universitetlar)", "🏢 Obyektlar (Tashkilotlar)"]:
            await self.handle_list_organizations(chat_id)
        elif text == "👥 Foydalanuvchilar & Rollar":
            await self.handle_list_users(chat_id)
        elif text == "➕ Yangi Obyekt Qo'shish":
            await self.handle_add_org_prompt(chat_id)
        elif text.startswith("/neworg") or text.startswith("/newuniv") or text.startswith("/newoffice"):
            await self.handle_create_org(chat_id, text)
        elif text.startswith("/setcreds"):
            await self.handle_set_creds(chat_id, text)
        elif text.startswith("/setmodules"):
            await self.handle_set_modules(chat_id, text)
        elif text.startswith("/setlogo") or text.startswith("/logo"):
            await self.send_message(
                chat_id,
                "🖼 <b>Maxsus Logotip o'rnatish qo'llanmasi:</b>\n\n"
                "1. Botga universitet yoki korxona logotipi rasmini yuboring.\n"
                "2. Rasm izohiga (caption) <code>/setlogo [OBYEKT_ID]</code> deb yozing.\n"
                "<i>Masalan: <code>/setlogo 1</code></i>\n\n"
                "Shunda ushbu universitet dasturiga kirganda faqat shu logotip chiqadi."
            )
        elif text.startswith("/assign") or text == "⚡ Rol Biriktirish":
            await self.handle_assign_command(chat_id, text)
        elif text == "📊 Umumiy Tizim Monitoringi":
            from app.services.telegram_bot import telegram_bot
            await telegram_bot.handle_today_stats(chat_id)
        else:
            await self.send_message(
                chat_id,
                "Buyruq tushunilmadi. Menyudagi tugmalardan foydalaning yoki /start bosing."
            )

    async def _polling_loop(self):
        logger.info("Telegram Master Bot Polling ishga tushdi (@BurgoodAccsesCantrolMaster_bot)...")
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
                        logger.error(f"Telegram Master Bot Token xato: {res.text}")
                        await asyncio.sleep(60)
                    else:
                        await asyncio.sleep(3)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Telegram Master Bot Polling xatosi: {e}")
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
        logger.info("Telegram Master Bot Polling to'xtatildi.")

telegram_master_bot = TelegramMasterBotService(settings.TELEGRAM_MASTER_BOT_TOKEN)
