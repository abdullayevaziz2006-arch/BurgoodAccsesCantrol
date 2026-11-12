import os
import shutil
import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.models.models import (
    Organization, TelegramUser, Group, Faculty, User, SystemAccount
)

logger = logging.getLogger("master_api")
router = APIRouter(prefix="/master", tags=["Master Admin Mini App"])

# -------------------------------------------------------------
# Pydantic Schemas
# -------------------------------------------------------------
class OrgCreateRequest(BaseModel):
    name: str
    code: Optional[str] = None
    address: Optional[str] = None
    org_type: str = "university" # "university" yoki "company"
    admin_username: str = "admin"
    admin_password: str = "admin123"
    modules_enabled: Optional[str] = None

class OrgUpdateRequest(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    address: Optional[str] = None
    org_type: Optional[str] = None
    admin_username: Optional[str] = None
    admin_password: Optional[str] = None
    modules_enabled: Optional[str] = None
    is_active: Optional[bool] = None

class UserRoleUpdateRequest(BaseModel):
    role: str # "otdel_kadr", "tutor", "dekan", "admin", "superadmin", "rejected"
    organization_id: Optional[int] = None
    assigned_group_id: Optional[int] = None
    assigned_faculty_id: Optional[int] = None

class AccountCreateRequest(BaseModel):
    full_name: str
    username: Optional[str] = None
    password: Optional[str] = None
    role: str = "otdel_kadr" # otdel_kadr, tutor, dekan, admin, operator
    organization_id: Optional[int] = None
    assigned_group_id: Optional[int] = None
    assigned_faculty_id: Optional[int] = None
    allowed_apps: str = "desktop,android,bot"
    allowed_modules: str = "attendance,staff"
    telegram_chat_id: Optional[str] = None
    phone_number: Optional[str] = None

class AccountUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    organization_id: Optional[int] = None
    assigned_group_id: Optional[int] = None
    assigned_faculty_id: Optional[int] = None
    allowed_apps: Optional[str] = None
    allowed_modules: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    phone_number: Optional[str] = None
    is_active: Optional[bool] = None

# -------------------------------------------------------------
# Endpoints
# -------------------------------------------------------------
@router.get("/overview")
def get_master_overview(db: Session = Depends(get_db)):
    org_count = db.query(Organization).count()
    users_count = db.query(User).filter(User.is_active == True).count()
    telegram_users_count = db.query(TelegramUser).count()
    pending_users_count = db.query(TelegramUser).filter(TelegramUser.role == "pending").count()
    
    return {
        "status": "online",
        "organizations_count": org_count,
        "total_people_count": users_count,
        "bot_users_count": telegram_users_count,
        "pending_users_count": pending_users_count,
    }

@router.get("/options")
def get_form_options(db: Session = Depends(get_db)):
    groups = db.query(Group).order_by(Group.name).all()
    faculties = db.query(Faculty).order_by(Faculty.name).all()
    orgs = db.query(Organization).order_by(Organization.name).all()

    return {
        "groups": [{"id": g.id, "name": g.name} for g in groups],
        "faculties": [{"id": f.id, "name": f.name} for f in faculties],
        "organizations": [{"id": o.id, "name": o.name, "org_type": getattr(o, "org_type", "university") or "university"} for o in orgs],
    }

# -------------------------------------------------------------
# Organizations Management
# -------------------------------------------------------------
@router.get("/organizations")
def list_organizations(db: Session = Depends(get_db)):
    orgs = db.query(Organization).order_by(Organization.id.desc()).all()
    result = []
    for o in orgs:
        bot_users = db.query(TelegramUser).filter(TelegramUser.organization_id == o.id).count()
        result.append({
            "id": o.id,
            "name": o.name,
            "code": o.code or "",
            "address": o.address or "",
            "org_type": getattr(o, "org_type", "university") or "university",
            "admin_username": o.admin_username or "admin",
            "admin_password": o.admin_password or "admin123",
            "modules_enabled": o.modules_enabled or ("dashboard,staff,structure,attendance,tabel,settings" if getattr(o, "org_type", "") == "company" else "dashboard,students,staff,structure,attendance,settings"),
            "logo_url": o.logo_url or "",
            "is_active": o.is_active,
            "bot_users_count": bot_users,
            "created_at": o.created_at.strftime("%Y-%m-%d %H:%M") if o.created_at else ""
        })
    return result

@router.post("/organizations")
def create_organization(req: OrgCreateRequest, db: Session = Depends(get_db)):
    existing = db.query(Organization).filter(Organization.name == req.name.strip()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Bunday nomli tashkilot allaqachon mavjud!")

    org_type = req.org_type.strip().lower() if req.org_type else "university"
    if req.modules_enabled and req.modules_enabled.strip():
        modules = req.modules_enabled.strip()
    else:
        if org_type == "company":
            modules = "dashboard,staff,structure,attendance,tabel,settings"
        else:
            modules = "dashboard,students,staff,structure,attendance,settings"

    org = Organization(
        name=req.name.strip(),
        code=req.code.strip() if req.code else req.name[:4].upper(),
        address=req.address.strip() if req.address else "",
        org_type=org_type,
        admin_username=req.admin_username.strip() if req.admin_username else "admin",
        admin_password=req.admin_password.strip() if req.admin_password else "admin123",
        modules_enabled=modules,
        is_active=True
    )
    db.add(org)
    db.commit()
    db.refresh(org)
    return {"success": True, "message": "Obyekt muvaffaqiyatli yaratildi!", "organization": org}

@router.put("/organizations/{org_id}")
def update_organization(org_id: int, req: OrgUpdateRequest, db: Session = Depends(get_db)):
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Obyekt topilmadi!")

    if req.name is not None:
        org.name = req.name.strip()
    if req.code is not None:
        org.code = req.code.strip()
    if req.address is not None:
        org.address = req.address.strip()
    if req.org_type is not None:
        org.org_type = req.org_type.strip().lower()
        if req.modules_enabled is None:
            if org.org_type in ["company", "office", "business"]:
                org.modules_enabled = "dashboard,staff,structure,attendance,tabel,settings"
            else:
                org.modules_enabled = "dashboard,students,staff,structure,attendance,settings"
    if req.admin_username is not None:
        org.admin_username = req.admin_username.strip()
    if req.admin_password is not None:
        org.admin_password = req.admin_password.strip()
    if req.modules_enabled is not None:
        org.modules_enabled = req.modules_enabled.strip()
    if req.is_active is not None:
        org.is_active = req.is_active

    db.commit()
    return {"success": True, "message": "Obyekt ma'lumotlari yangilandi!"}

@router.post("/organizations/{org_id}/logo")
async def upload_organization_logo(org_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Obyekt topilmadi!")

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    ext = os.path.splitext(file.filename)[1] or ".png"
    filename = f"org_{org_id}_logo{ext}"
    dest_path = os.path.join(settings.UPLOAD_DIR, filename)

    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    org.logo_url = f"/uploads/{filename}"
    db.commit()

    return {"success": True, "logo_url": org.logo_url, "message": "Logotip muvaffaqiyatli yuklandi!"}

@router.delete("/organizations/{org_id}")
def delete_organization(org_id: int, db: Session = Depends(get_db)):
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Obyekt topilmadi!")

    db.delete(org)
    db.commit()
    return {"success": True, "message": "Obyekt o'chirildi!"}

# -------------------------------------------------------------
# Telegram Bot Users & RBAC Management
# -------------------------------------------------------------
@router.get("/users")
def list_telegram_users(db: Session = Depends(get_db)):
    users = db.query(TelegramUser).order_by(TelegramUser.created_at.desc()).all()
    res = []
    for u in users:
        res.append({
            "id": u.id,
            "chat_id": u.chat_id,
            "first_name": u.first_name or "",
            "last_name": u.last_name or "",
            "username": u.username or "",
            "role": u.role,
            "organization_id": u.organization_id,
            "organization_name": u.organization.name if u.organization else "",
            "assigned_group_id": u.assigned_group_id,
            "assigned_group_name": u.assigned_group.name if u.assigned_group else "",
            "assigned_faculty_id": u.assigned_faculty_id,
            "assigned_faculty_name": u.assigned_faculty.name if u.assigned_faculty else "",
            "is_active": u.is_active,
            "created_at": u.created_at.strftime("%Y-%m-%d %H:%M") if u.created_at else ""
        })
    return res

@router.post("/users/{chat_id}/role")
async def update_user_role(chat_id: str, req: UserRoleUpdateRequest, db: Session = Depends(get_db)):
    user = db.query(TelegramUser).filter(TelegramUser.chat_id == str(chat_id)).first()
    if not user:
        user = TelegramUser(chat_id=str(chat_id), role=req.role, is_active=True)
        db.add(user)
    else:
        user.role = req.role
        user.is_active = (req.role != "rejected")

    if req.organization_id is not None:
        user.organization_id = req.organization_id if req.organization_id > 0 else None

    if req.role == "tutor":
        user.assigned_group_id = req.assigned_group_id if req.assigned_group_id and req.assigned_group_id > 0 else None
        user.assigned_faculty_id = None
    elif req.role == "dekan":
        user.assigned_faculty_id = req.assigned_faculty_id if req.assigned_faculty_id and req.assigned_faculty_id > 0 else None
        user.assigned_group_id = None
    else:
        user.assigned_group_id = None
        user.assigned_faculty_id = None

    db.commit()

    # Foydalanuvchiga Telegram Client Bot orqali yangilanish xabari yuborish
    try:
        from app.services.telegram_bot import telegram_bot
        role_titles = {
            "otdel_kadr": "💼 Otdel Kadr (HR - Faqat xodimlar)",
            "tutor": f"🎓 Tyutor",
            "dekan": "🏛 Dekan",
            "admin": "👑 Rektor / Rahbariyat",
            "superadmin": "👑 SuperAdmin",
            "rejected": "❌ Bloklangan"
        }
        if req.role == "rejected":
            await telegram_bot.send_message(chat_id, "❌ Sizning akkauntingiz administrator tomonidan bloklandi.")
        else:
            msg = (
                f"🎉 <b>Akkauntingiz yangilandi!</b>\n\n"
                f"📌 <b>Yangi rolingiz:</b> {role_titles.get(req.role, req.role)}\n"
                f"Quyidagi menyu orqali tegishli ma'lumotlarni ko'rishingiz mumkin:"
            )
            await telegram_bot.send_message(chat_id, msg, reply_markup=telegram_bot.get_keyboard_for_user(user))
    except Exception as e:
        logger.warning(f"Client botga bildirishnoma yuborishda xatolik: {e}")

    return {"success": True, "message": "Foydalanuvchi roli va huquqlari muvaffaqiyatli saqlandi!"}

# -------------------------------------------------------------
# System User Accounts (Desktop, APK, Bot login/password & permissions)
# -------------------------------------------------------------
@router.get("/accounts")
def list_system_accounts(db: Session = Depends(get_db)):
    accounts = db.query(SystemAccount).order_by(SystemAccount.created_at.desc()).all()
    res = []
    for a in accounts:
        res.append({
            "id": a.id,
            "full_name": a.full_name,
            "username": a.username,
            "password": a.password,
            "role": a.role,
            "organization_id": a.organization_id,
            "organization_name": a.organization.name if a.organization else "",
            "assigned_group_id": a.assigned_group_id,
            "assigned_group_name": a.assigned_group.name if a.assigned_group else "",
            "assigned_faculty_id": a.assigned_faculty_id,
            "assigned_faculty_name": a.assigned_faculty.name if a.assigned_faculty else "",
            "allowed_apps": a.allowed_apps or "desktop,android,bot",
            "allowed_modules": a.allowed_modules or "attendance,staff",
            "telegram_chat_id": a.telegram_chat_id or "",
            "phone_number": a.phone_number or "",
            "is_active": a.is_active,
            "created_at": a.created_at.strftime("%Y-%m-%d %H:%M") if a.created_at else ""
        })
    return res

@router.post("/accounts")
async def create_system_account(req: AccountCreateRequest, db: Session = Depends(get_db)):
    username = (req.username or "").strip()
    password = (req.password or "").strip()
    
    # Agar foydalanuvchiga faqat Bot ruxsati berilgan bo'lsa va login/parol kiritilmagan bo'lsa
    if not username:
        import uuid
        username = f"bot_{uuid.uuid4().hex[:8]}"
    if not password:
        import secrets
        password = secrets.token_urlsafe(8)

    existing = db.query(SystemAccount).filter(SystemAccount.username == username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ushbu login band! Boshqa login tanlang.")

    account = SystemAccount(
        full_name=req.full_name.strip(),
        username=username,
        password=password,
        role=req.role,
        organization_id=req.organization_id if req.organization_id and req.organization_id > 0 else None,
        assigned_group_id=req.assigned_group_id if req.assigned_group_id and req.assigned_group_id > 0 else None,
        assigned_faculty_id=req.assigned_faculty_id if req.assigned_faculty_id and req.assigned_faculty_id > 0 else None,
        allowed_apps=req.allowed_apps or "desktop,android,bot",
        allowed_modules=req.allowed_modules or "attendance,staff",
        telegram_chat_id=req.telegram_chat_id.strip() if req.telegram_chat_id else None,
        phone_number=req.phone_number.strip() if req.phone_number else None,
        is_active=True
    )
    db.add(account)
    db.commit()
    db.refresh(account)

    # Agar telegram_chat_id berilgan bo'lsa, TelegramUser ni ham yangilash
    if account.telegram_chat_id:
        t_user = db.query(TelegramUser).filter(TelegramUser.chat_id == account.telegram_chat_id).first()
        if not t_user:
            t_user = TelegramUser(
                chat_id=account.telegram_chat_id,
                first_name=account.full_name,
                role=account.role,
                organization_id=account.organization_id,
                assigned_group_id=account.assigned_group_id,
                assigned_faculty_id=account.assigned_faculty_id,
                is_active=True
            )
            db.add(t_user)
        else:
            t_user.role = account.role
            t_user.organization_id = account.organization_id
            t_user.assigned_group_id = account.assigned_group_id
            t_user.assigned_faculty_id = account.assigned_faculty_id
            t_user.is_active = True
        db.commit()

    return {"success": True, "account_id": account.id, "message": "Yangi foydalanuvchi akkaunti muvaffaqiyatli yaratildi!"}

@router.put("/accounts/{account_id}")
async def update_system_account(account_id: int, req: AccountUpdateRequest, db: Session = Depends(get_db)):
    account = db.query(SystemAccount).filter(SystemAccount.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Akkaunt topilmadi!")

    if req.username is not None and req.username.strip() != account.username:
        chk = db.query(SystemAccount).filter(SystemAccount.username == req.username.strip(), SystemAccount.id != account_id).first()
        if chk:
            raise HTTPException(status_code=400, detail="Ushbu login band!")
        account.username = req.username.strip()

    if req.full_name is not None:
        account.full_name = req.full_name.strip()
    if req.password is not None and req.password.strip():
        account.password = req.password.strip()
    if req.role is not None:
        account.role = req.role
    if req.organization_id is not None:
        account.organization_id = req.organization_id if req.organization_id > 0 else None
    if req.assigned_group_id is not None:
        account.assigned_group_id = req.assigned_group_id if req.assigned_group_id > 0 else None
    if req.assigned_faculty_id is not None:
        account.assigned_faculty_id = req.assigned_faculty_id if req.assigned_faculty_id > 0 else None
    if req.allowed_apps is not None:
        account.allowed_apps = req.allowed_apps
    if req.allowed_modules is not None:
        account.allowed_modules = req.allowed_modules
    if req.telegram_chat_id is not None:
        account.telegram_chat_id = req.telegram_chat_id.strip() or None
    if req.phone_number is not None:
        account.phone_number = req.phone_number.strip() or None
    if req.is_active is not None:
        account.is_active = req.is_active

    db.commit()

    # Agar telegram_chat_id bo'lsa, TelegramUser ni ham yangilash yoki yaratish
    if account.telegram_chat_id:
        t_user = db.query(TelegramUser).filter(TelegramUser.chat_id == account.telegram_chat_id).first()
        if not t_user:
            t_user = TelegramUser(
                chat_id=account.telegram_chat_id,
                first_name=account.full_name,
                role=account.role,
                organization_id=account.organization_id,
                assigned_group_id=account.assigned_group_id,
                assigned_faculty_id=account.assigned_faculty_id,
                is_active=account.is_active
            )
            db.add(t_user)
        else:
            t_user.role = account.role
            t_user.organization_id = account.organization_id
            t_user.assigned_group_id = account.assigned_group_id
            t_user.assigned_faculty_id = account.assigned_faculty_id
            t_user.is_active = account.is_active
        db.commit()

    return {"success": True, "message": "Akkaunt muvaffaqiyatli yangilandi!"}

@router.delete("/accounts/{account_id}")
def delete_system_account(account_id: int, db: Session = Depends(get_db)):
    account = db.query(SystemAccount).filter(SystemAccount.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Akkaunt topilmadi!")

    db.delete(account)
    db.commit()
    return {"success": True, "message": "Akkaunt o'chirildi!"}

