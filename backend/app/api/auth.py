from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
import logging

from app.core.database import get_db
from app.models.models import Organization, User, SystemAccount

logger = logging.getLogger("auth")
router = APIRouter(prefix="/auth", tags=["Auth"])

class LoginRequest(BaseModel):
    username: str
    password: str
    app_type: Optional[str] = None  # "android", "desktop", etc.

class LoginResponse(BaseModel):
    success: bool
    token: str
    organization: Optional[Dict[str, Any]] = None
    user: Dict[str, Any]

@router.post("/login", response_model=LoginResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    u = req.username.strip()
    p = req.password.strip()
    app_type = (req.app_type or "").strip().lower()
    logger.info(f"🔑 Kirish urinishi: username='{u}', app_type='{app_type}'")

    # 1. Shaxsiy Foydalanuvchi akkauntini (SystemAccount) tekshirish (katta-kichik harfga qaramasdan)
    account = db.query(SystemAccount).filter(
        func.lower(SystemAccount.username) == u.lower(),
        SystemAccount.password == p,
        SystemAccount.is_active == True
    ).first()

    if account:
        org = account.organization
        modules = [m.strip() for m in (account.allowed_modules or "attendance,staff").split(",") if m.strip()]
        allowed_apps = [a.strip() for a in (account.allowed_apps or "desktop,android,bot").split(",") if a.strip()]

        # 1. Ruxsat berilgan dasturlar (allowed_apps) qat'iy nazorati
        allowed_apps = [a.strip().lower() for a in (account.allowed_apps or "desktop,android,bot").split(",") if a.strip()]

        if app_type == "android":
            if "android" not in allowed_apps:
                logger.warning(f"⛔ Mobil ilovaga (APK) kirish rad etildi: {u} (allowed_apps={allowed_apps})")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Sizning akkauntingizga mobil ilovadan (APK) foydalanishga ruxsat berilmagan!"
                )
        else:
            # Desktop dastur yoki Web brauzer
            if "desktop" not in allowed_apps:
                logger.warning(f"⛔ Desktop dasturiga kirish rad etildi: {u} (allowed_apps={allowed_apps})")
                if "bot" in allowed_apps and "android" not in allowed_apps:
                    detail_msg = "Sizning akkauntingizga kompyuter dasturidan (Desktop) foydalanishga ruxsat berilmagan! Sizga faqat Telegram Bot biriktirilgan."
                elif "android" in allowed_apps:
                    detail_msg = "Sizning akkauntingizga kompyuter dasturidan (Desktop) foydalanishga ruxsat berilmagan! Faqat mobil ilova (APK) orqali kiring."
                else:
                    detail_msg = "Sizning akkauntingizga kompyuter dasturidan (Desktop) foydalanishga ruxsat berilmagan!"
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=detail_msg
                )
        
        org_data = None
        if org:
            org_data = {
                "id": org.id,
                "name": org.name,
                "code": org.code,
                "logo_url": org.logo_url,
                "org_type": getattr(org, "org_type", "university") or "university",
                "modules": modules
            }
        else:
            first_org = db.query(Organization).first()
            if first_org:
                org_data = {
                    "id": first_org.id,
                    "name": first_org.name,
                    "code": first_org.code,
                    "logo_url": first_org.logo_url,
                    "org_type": getattr(first_org, "org_type", "university") or "university",
                    "modules": modules
                }

        return {
            "success": True,
            "token": f"user_token_{account.id}",
            "organization": org_data,
            "user": {
                "id": account.id,
                "username": account.username,
                "role": account.role,
                "full_name": account.full_name,
                "allowed_apps": allowed_apps,
                "allowed_modules": modules,
                "assigned_group_id": account.assigned_group_id,
                "assigned_faculty_id": account.assigned_faculty_id
            }
        }

    # 2. Tashkilot / Obyekt adminini tekshirish (katta-kichik harfga qaramasdan)
    org = db.query(Organization).filter(
        func.lower(Organization.admin_username) == u.lower(),
        Organization.admin_password == p,
        Organization.is_active == True
    ).first()

    if org:
        if app_type == "android":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tashkilot ma'muriyati faqat kompyuter (desktop) orqali kirishi mumkin. Mobil ilovadan foydalanish cheklangan!"
            )

        modules = [m.strip() for m in (org.modules_enabled or "attendance,students,staff,structure,schedules").split(",") if m.strip()]
        return {
            "success": True,
            "token": f"org_token_{org.id}",
            "organization": {
                "id": org.id,
                "name": org.name,
                "code": org.code,
                "logo_url": org.logo_url,
                "org_type": getattr(org, "org_type", "university") or "university",
                "modules": modules
            },
            "user": {
                "username": org.admin_username,
                "role": "admin",
                "full_name": f"{org.name} Administratori"
            }
        }

    # 3. Standart tizim superadmini (admin / admin123)
    if u.lower() == "admin" and p == "admin123":
        if app_type == "android":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bosh administrator faqat kompyuter (desktop) orqali kirishi mumkin. Mobil ilovadan foydalanish cheklangan!"
            )

        first_org = db.query(Organization).first()
        org_data = None
        if first_org:
            modules = [m.strip() for m in (first_org.modules_enabled or "attendance,students,staff,structure,schedules").split(",") if m.strip()]
            org_data = {
                "id": first_org.id,
                "name": first_org.name,
                "code": first_org.code,
                "logo_url": first_org.logo_url,
                "org_type": getattr(first_org, "org_type", "university") or "university",
                "modules": modules
            }
        return {
            "success": True,
            "token": "master_admin_token",
            "organization": org_data,
            "user": {
                "username": "admin",
                "role": "superadmin",
                "full_name": "Bosh Administrator"
            }
        }

    logger.warning(f"❌ Noto'g'ri login yoki parol kiritildi: username='{u}'")
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Login yoki parol noto'g'ri!")

@router.get("/branding")
def get_branding(db: Session = Depends(get_db)):
    return {
        "name": "Burgood Access Control",
        "code": "BURGOOD",
        "logo_url": "/burgood_shield.png"
    }

@router.get("/me")
def get_me(request: Request, db: Session = Depends(get_db)):
    auth_header = request.headers.get("Authorization") or ""
    token = ""
    if auth_header.startswith("Bearer "):
        token = auth_header.replace("Bearer ", "").strip()
    
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token talab qilinadi")

    if token == "master_admin_token":
        first_org = db.query(Organization).first()
        modules = [m.strip() for m in (first_org.modules_enabled or "attendance,students,staff,structure,schedules,settings").split(",") if m.strip()] if first_org else ["attendance", "staff", "settings"]
        return {
            "success": True,
            "user": {
                "username": "admin",
                "role": "superadmin",
                "full_name": "Bosh Administrator",
                "allowed_modules": modules
            }
        }

    if token.startswith("user_token_"):
        try:
            account_id = int(token.replace("user_token_", ""))
            account = db.query(SystemAccount).filter(SystemAccount.id == account_id).first()
            if account and account.is_active:
                modules = [m.strip() for m in (account.allowed_modules or "attendance,staff").split(",") if m.strip()]
                allowed_apps = [a.strip() for a in (account.allowed_apps or "").split(",") if a.strip()]
                org_data = None
                if account.organization:
                    org_data = {
                        "id": account.organization.id,
                        "name": account.organization.name,
                        "code": account.organization.code,
                        "logo_url": account.organization.logo_url,
                        "org_type": getattr(account.organization, "org_type", "university") or "university",
                        "modules": modules
                    }
                return {
                    "success": True,
                    "organization": org_data,
                    "user": {
                        "id": account.id,
                        "username": account.username,
                        "role": account.role,
                        "full_name": account.full_name,
                        "allowed_modules": modules,
                        "allowed_apps": allowed_apps,
                        "assigned_group_id": account.assigned_group_id,
                        "assigned_faculty_id": account.assigned_faculty_id
                    }
                }
        except Exception:
            pass

    if token.startswith("org_token_"):
        try:
            org_id = int(token.replace("org_token_", ""))
            org = db.query(Organization).filter(Organization.id == org_id).first()
            if org and org.is_active:
                modules = [m.strip() for m in (org.modules_enabled or "attendance,students,staff,structure,schedules,settings").split(",") if m.strip()]
                return {
                    "success": True,
                    "organization": {
                        "id": org.id,
                        "name": org.name,
                        "code": org.code,
                        "logo_url": org.logo_url,
                        "org_type": getattr(org, "org_type", "university") or "university",
                        "modules": modules
                    },
                    "user": {
                        "username": org.admin_username,
                        "role": "admin",
                        "full_name": f"{org.name} Administratori",
                        "allowed_modules": modules
                    }
                }
        except Exception:
            pass

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Yaroqsiz token")
