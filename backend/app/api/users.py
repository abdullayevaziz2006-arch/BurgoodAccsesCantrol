from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil
import time
import logging
import uuid
import base64

logger = logging.getLogger(__name__)

from app.core.database import get_db
from app.core.config import settings
from app.models.models import User, UserRole, Device, Organization
from app.schemas.schemas import UserCreate, UserUpdate, UserOut, BatchSyncRequest
from app.services.hikvision_isapi import HikvisionISAPI

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/", response_model=List[UserOut])
def get_users(
    skip: int = 0, 
    limit: int = 100, 
    role: Optional[UserRole] = None, 
    search: Optional[str] = None,
    x_organization_id: Optional[str] = Header(None),
    x_user_role: Optional[str] = Header(None),
    x_assigned_group_id: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    query = db.query(User)
    if x_organization_id and x_organization_id.isdigit():
        query = query.filter(User.organization_id == int(x_organization_id))

    if x_user_role == "otdel_kadr":
        query = query.filter(User.role != UserRole.STUDENT)
    elif x_user_role == "tutor" and x_assigned_group_id and x_assigned_group_id.isdigit():
        query = query.filter(User.group_id == int(x_assigned_group_id))

    if role:
        query = query.filter(User.role == role)
    if search:
        query = query.filter(
            (User.full_name.ilike(f"%{search}%")) | 
            (User.employee_no.ilike(f"%{search}%")) |
            (User.group_name.ilike(f"%{search}%"))
        )
    users = query.offset(skip).limit(limit).all()
    results = []
    for u in users:
        group_name = u.group.name if u.group else u.group_name
        direction_name = u.group.direction_name if u.group else None
        tutor_name = u.group.tutor.full_name if (u.group and u.group.tutor) else None
        dept_name = u.department.name if u.department else None

        results.append(UserOut(
            id=u.id,
            employee_no=u.employee_no,
            full_name=u.full_name,
            role=u.role,
            position=u.position,
            phone_number=u.phone_number,
            card_number=u.card_number,
            group_id=u.group_id,
            group_name=group_name,
            direction_name=direction_name,
            tutor_name=tutor_name,
            department_id=u.department_id,
            department_name=dept_name,
            photo_path=u.photo_path,
            is_active=u.is_active,
            created_at=u.created_at,
            updated_at=u.updated_at
        ))
    return results

# Talabalar Excel Shablonini (Template) yuklab olish
@router.get("/template-students-excel")
def download_students_template():
    import openpyxl
    from io import BytesIO
    from fastapi.responses import StreamingResponse

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Talabalar Shablon"

    headers = [
        "ID_Raqam (Talaba ID)", 
        "F.I.SH", 
        "Guruh Raqami", 
        "Fakultet Nomi", 
        "Kafedra Nomi", 
        "Telefon Raqami",
        "Rasm Kodi"
    ]
    ws.append(headers)

    # Namuna qatorlari (.jpg qo'shimchasi shart emas, faqat rasm kodi)
    ws.append(["391001", "Akmal Jo'rayev", "941-21", "Axborot Texnologiyalari Fakulteti", "Dasturiy Muhandislik kafedrasi", "+998901234567", "391001"])
    ws.append(["391002", "Madina Karimova", "942-21", "Axborot Texnologiyalari Fakulteti", "Dasturiy Muhandislik kafedrasi", "+998912345678", "391002"])

    # Dizayn
    for cell in ws[1]:
        cell.font = openpyxl.styles.Font(bold=True, color="FFFFFF")
        cell.fill = openpyxl.styles.PatternFill(start_color="1F497D", end_color="1F497D", fill_type="solid")

    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=talabalar_shablon.xlsx"}
    )

# Xodimlar Excel Shablonini (Template) yuklab olish
@router.get("/template-staff-excel")
def download_staff_template():
    import openpyxl
    from io import BytesIO
    from fastapi.responses import StreamingResponse

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Xodimlar Shablon"

    headers = [
        "Tabel_ID", 
        "F.I.SH", 
        "Bo'lim yoki Kafedra", 
        "Lavozimi", 
        "Turi (teacher yoki staff)", 
        "Telefon",
        "Rasm Kodi"
    ]
    ws.append(headers)

    ws.append(["390010", "Olimov Bobur Mansurovich", "Dasturiy Muhandislik kafedrasi", "Katta Tyutor", "staff", "+998905551122", "390010"])
    ws.append(["390011", "Xoliqova Shahnoza Erkinovna", "Dasturiy Muhandislik kafedrasi", "Dotsent", "teacher", "+998914443322", "390011"])

    for cell in ws[1]:
        cell.font = openpyxl.styles.Font(bold=True, color="FFFFFF")
        cell.fill = openpyxl.styles.PatternFill(start_color="1F497D", end_color="1F497D", fill_type="solid")

    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=xodimlar_shablon.xlsx"}
    )

# Excel va ZIP orqali Talabalarni massiv qo'shish
@router.post("/import-students-excel")
async def import_students_excel(
    file: UploadFile = File(...), 
    zip_file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    import openpyxl
    import zipfile
    import time
    from io import BytesIO
    from app.models.models import Group, Faculty, Department

    try:
        # 1. Agar rasmlar ZIP arxivi yuborilgan bo'lsa, uni xotirada ochamiz
        zip_photos = {}
        if zip_file and zip_file.filename:
            zip_bytes = await zip_file.read()
            if len(zip_bytes) > 0:
                try:
                    with zipfile.ZipFile(BytesIO(zip_bytes)) as zf:
                        for member in zf.namelist():
                            if member.endswith('/') or '__MACOSX' in member:
                                continue
                            base_name = os.path.basename(member).strip().lower()
                            name_no_ext = os.path.splitext(base_name)[0].strip().lower()
                            file_data = zf.read(member)
                            zip_photos[base_name] = (base_name, file_data)
                            zip_photos[name_no_ext] = (base_name, file_data)
                except Exception as ze:
                    pass

        # 2. Excel faylini o'qiymiz
        content = await file.read()
        wb = openpyxl.load_workbook(BytesIO(content))
        ws = wb.active
        created_count = 0
        skipped_count = 0
        photos_linked = 0

        # Ustunlar: [ID_Raqam, F.I.SH, Guruh_Raqami, Fakultet_Nomi, Kafedra_Nomi, Telefon, Rasm_Kodi]
        for row in ws.iter_rows(min_row=2, values_only=True):
            if not row or not row[0] or not row[1]:
                continue
            emp_no = str(row[0]).strip()
            full_name = str(row[1]).strip()
            group_name = str(row[2]).strip() if len(row) > 2 and row[2] else None
            faculty_name = str(row[3]).strip() if len(row) > 3 and row[3] else None
            dept_name = str(row[4]).strip() if len(row) > 4 and row[4] else None
            phone = str(row[5]).strip() if len(row) > 5 and row[5] else None
            photo_code = str(row[6]).strip() if len(row) > 6 and row[6] else None

            # Rasm qidirish (ZIP arxivdan)
            matched_photo = None
            if zip_photos:
                if photo_code:
                    p_key = photo_code.lower()
                    p_key_no_ext = os.path.splitext(p_key)[0]
                    matched_photo = zip_photos.get(p_key) or zip_photos.get(p_key_no_ext)
                if not matched_photo:
                    matched_photo = zip_photos.get(emp_no.lower())

            saved_photo_path = None
            if matched_photo:
                orig_filename, img_bytes = matched_photo
                ext = os.path.splitext(orig_filename)[1] or ".jpg"
                filename = f"user_{emp_no}_{int(time.time())}{ext}"
                target_path = os.path.join(settings.UPLOAD_DIR, filename)
                with open(target_path, "wb") as f_out:
                    f_out.write(img_bytes)
                saved_photo_path = f"/uploads/{filename}"
                photos_linked += 1

            existing = db.query(User).filter(User.employee_no == emp_no).first()
            if existing:
                if saved_photo_path:
                    existing.photo_path = saved_photo_path
                skipped_count += 1
                continue

            # Fakultet va kafedrani topish
            fac_id = None
            if faculty_name:
                fac = db.query(Faculty).filter(Faculty.name.ilike(f"%{faculty_name}%")).first()
                if fac:
                    fac_id = fac.id

            dept_id = None
            if dept_name:
                dept = db.query(Department).filter(Department.name.ilike(f"%{dept_name}%")).first()
                if dept:
                    dept_id = dept.id

            # Guruhni topish yoki avtomatik yangi guruh ochish
            grp = None
            if group_name:
                grp = db.query(Group).filter(Group.name.ilike(f"%{group_name}%")).first()
                if not grp:
                    grp = Group(
                        name=group_name,
                        faculty_id=fac_id,
                        department_id=dept_id,
                        direction_name="Bakalavr"
                    )
                    db.add(grp)
                    db.commit()
                    db.refresh(grp)

            user = User(
                employee_no=emp_no,
                full_name=full_name,
                role=UserRole.STUDENT,
                group_id=grp.id if grp else None,
                group_name=group_name,
                department_id=dept_id or (grp.department_id if grp else None),
                phone_number=phone,
                photo_path=saved_photo_path,
                is_active=True
            )
            db.add(user)
            created_count += 1

        db.commit()
        return {
            "success": True, 
            "created": created_count, 
            "skipped": skipped_count,
            "photos_linked": photos_linked
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Talabalar massiv yuklashida xatolik: {str(e)}")

# Excel va ZIP orqali Xodimlarni massiv qo'shish
@router.post("/import-staff-excel")
async def import_staff_excel(
    file: UploadFile = File(...), 
    zip_file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    import openpyxl
    import zipfile
    import time
    from io import BytesIO
    from app.models.models import Department

    try:
        zip_photos = {}
        if zip_file and zip_file.filename:
            zip_bytes = await zip_file.read()
            if len(zip_bytes) > 0:
                try:
                    with zipfile.ZipFile(BytesIO(zip_bytes)) as zf:
                        for member in zf.namelist():
                            if member.endswith('/') or '__MACOSX' in member:
                                continue
                            base_name = os.path.basename(member).strip().lower()
                            name_no_ext = os.path.splitext(base_name)[0].strip().lower()
                            file_data = zf.read(member)
                            zip_photos[base_name] = (base_name, file_data)
                            zip_photos[name_no_ext] = (base_name, file_data)
                except Exception as ze:
                    pass

        content = await file.read()
        wb = openpyxl.load_workbook(BytesIO(content))
        ws = wb.active
        created_count = 0
        skipped_count = 0
        photos_linked = 0

        # Qatorlar: [Tabel_ID, F.I.SH, Kafedra_Yoki_Bo'lim, Lavozimi, Turi, Telefon, Rasm_Kodi]
        for row in ws.iter_rows(min_row=2, values_only=True):
            if not row or not row[0] or not row[1]:
                continue
            emp_no = str(row[0]).strip()
            full_name = str(row[1]).strip()
            dept_name = str(row[2]).strip() if len(row) > 2 and row[2] else None
            position = str(row[3]).strip() if len(row) > 3 and row[3] else "Xodim"
            role_type = str(row[4]).strip().lower() if len(row) > 4 and row[4] else "teacher"
            phone = str(row[5]).strip() if len(row) > 5 and row[5] else None
            photo_code = str(row[6]).strip() if len(row) > 6 and row[6] else None

            # Rasm qidirish (ZIP arxivdan)
            matched_photo = None
            if zip_photos:
                if photo_code:
                    p_key = photo_code.lower()
                    p_key_no_ext = os.path.splitext(p_key)[0]
                    matched_photo = zip_photos.get(p_key) or zip_photos.get(p_key_no_ext)
                if not matched_photo:
                    matched_photo = zip_photos.get(emp_no.lower())

            saved_photo_path = None
            if matched_photo:
                orig_filename, img_bytes = matched_photo
                ext = os.path.splitext(orig_filename)[1] or ".jpg"
                filename = f"user_{emp_no}_{int(time.time())}{ext}"
                target_path = os.path.join(settings.UPLOAD_DIR, filename)
                with open(target_path, "wb") as f_out:
                    f_out.write(img_bytes)
                saved_photo_path = f"/uploads/{filename}"
                photos_linked += 1

            existing = db.query(User).filter(User.employee_no == emp_no).first()
            if existing:
                if saved_photo_path:
                    existing.photo_path = saved_photo_path
                skipped_count += 1
                continue

            dept = None
            if dept_name:
                dept = db.query(Department).filter(Department.name.ilike(f"%{dept_name}%")).first()

            role = UserRole.TEACHER if "o'qituvchi" in role_type or "teacher" in role_type or "dotsent" in position.lower() or "mudir" in position.lower() else UserRole.STAFF

            user = User(
                employee_no=emp_no,
                full_name=full_name,
                role=role,
                position=position,
                department_id=dept.id if dept else None,
                group_name=dept.name if dept else dept_name,
                phone_number=phone,
                photo_path=saved_photo_path,
                is_active=True
            )
            db.add(user)
            created_count += 1

        db.commit()
        return {
            "success": True, 
            "created": created_count, 
            "skipped": skipped_count,
            "photos_linked": photos_linked
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Xodimlar massiv yuklashida xatolik: {str(e)}")

class BatchUserItem(BaseModel):
    employee_no: str
    name: str
    photo_base64: Optional[str] = None
    role: Optional[str] = "staff"

class BatchImportRequest(BaseModel):
    users: List[BatchUserItem]

@router.post("/batch-import-with-faces")
async def batch_import_with_faces(
    req: BatchImportRequest,
    db: Session = Depends(get_db),
    x_organization_id: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None)
):
    org_id = None
    if x_organization_id and x_organization_id.isdigit():
        org_id = int(x_organization_id)
    
    # 1. Token ichidan tashkilot ID sini aniqlash
    if not org_id and authorization and authorization.startswith("Bearer "):
        try:
            token = authorization.split(" ")[1]
            from jose import jwt
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            token_org = payload.get("org_id") or payload.get("organization_id")
            if token_org:
                org_id = int(token_org)
        except Exception:
            pass

    # 2. Agar token yoki headerda bo'lmasa, faol turniketga qarashli tashkilotni olamiz (masalan test tashkiloti, id: 5)
    if not org_id:
        active_dev = db.query(Device).filter(Device.is_active == True).order_by(Device.id.desc()).first()
        if active_dev and active_dev.organization_id:
            org_id = active_dev.organization_id
        else:
            last_org = db.query(Organization).order_by(Organization.id.desc()).first()
            org_id = last_org.id if last_org else 1

    uploads_dir = os.path.join(os.getcwd(), "uploads", "faces")
    os.makedirs(uploads_dir, exist_ok=True)

    created_count = 0
    updated_count = 0
    photos_count = 0

    for item in req.users:
        emp_no = str(item.employee_no).strip()
        name = str(item.name).strip() or f"Xodim #{emp_no}"
        
        # Avval shu tashkilotda xodim bormi tekshiramiz
        user = db.query(User).filter(User.employee_no == emp_no, User.organization_id == org_id).first()
        if user:
            if not user.full_name or user.full_name.startswith("Xodim #"):
                user.full_name = name
            user.role = UserRole.STAFF
            updated_count += 1
        else:
            # Agar boshqa tashkilotda (masalan oldingi testda) qolib ketgan bo'lsa, shu yangi tashkilotga o'tkazamiz
            existing_user = db.query(User).filter(User.employee_no == emp_no).first()
            if existing_user:
                existing_user.organization_id = org_id
                existing_user.role = UserRole.STAFF
                if not existing_user.full_name or existing_user.full_name.startswith("Xodim #"):
                    existing_user.full_name = name
                user = existing_user
                updated_count += 1
            else:
                user = User(
                    full_name=name,
                    employee_no=emp_no,
                    role=UserRole.STAFF,
                    is_active=True,
                    organization_id=org_id
                )
                db.add(user)
                db.flush()
                created_count += 1

        if item.photo_base64:
            try:
                b64_data = item.photo_base64
                if "," in b64_data:
                    b64_data = b64_data.split(",", 1)[1]
                img_bytes = base64.b64decode(b64_data)
                filename = f"user_{user.id}_{uuid.uuid4().hex[:8]}.jpg"
                file_path = os.path.join(uploads_dir, filename)
                with open(file_path, "wb") as f:
                    f.write(img_bytes)
                user.photo_path = f"/uploads/faces/{filename}"
                photos_count += 1
            except Exception:
                pass

    db.commit()
    return {
        "success": True,
        "created": created_count,
        "updated": updated_count,
        "photos_linked": photos_count,
        "total": len(req.users),
        "message": f"Muvaffaqiyatli: {created_count} ta yangi xodim qo'shildi, {updated_count} ta yangilandi, {photos_count} ta yuz rasmi saqlandi!"
    }

# Tanlangan foydalanuvchilarni tanlangan terminallarga massiv sinxronizatsiya qilish
@router.post("/batch-sync-to-devices")
async def batch_sync_users_to_devices(
    req: BatchSyncRequest,
    db: Session = Depends(get_db)
):
    """Tanlangan talabalar/xodimlarni tanlangan terminallarga ISAPI orqali o'tkazish"""
    users = db.query(User).filter(User.id.in_(req.user_ids)).all()
    devices = db.query(Device).filter(Device.id.in_(req.device_ids)).all()

    if not users:
        raise HTTPException(status_code=400, detail="Hech qanday foydalanuvchi tanlanmagan")
    if not devices:
        raise HTTPException(status_code=400, detail="Hech qanday terminal tanlanmagan")

    # Foydalanuvchilar rasmlarini o'qib olish
    user_images = {}
    for u in users:
        if u.photo_path:
            local_filename = os.path.basename(u.photo_path)
            full_path = os.path.join(settings.UPLOAD_DIR, local_filename)
            if os.path.exists(full_path):
                with open(full_path, "rb") as f:
                    user_images[u.id] = f.read()

    details = []
    total_faces_uploaded = 0
    total_failures = 0

    for dev in devices:
        isapi = HikvisionISAPI(dev.ip_address, dev.port, dev.username, dev.password)
        dev_success = 0
        dev_fail = 0
        dev_faces = 0
        dev_errors = []

        for u in users:
            u_ok, u_msg = await isapi.set_user_info(u.employee_no, u.full_name)
            img_bytes = user_images.get(u.id)
            f_ok, f_msg = (False, "Rasm yo'q")
            if u_ok and img_bytes:
                f_ok, f_msg = await isapi.upload_face_picture(u.employee_no, img_bytes)
                if f_ok:
                    dev_faces += 1
                    total_faces_uploaded += 1
                else:
                    dev_errors.append(f"{u.full_name} ({u.employee_no}): Yuz rasmini yuklashda xatolik - {f_msg}")
            elif not u_ok:
                dev_errors.append(f"{u.full_name} ({u.employee_no}): Ma'lumotlarni yuborishda xatolik - {u_msg}")

            if u_ok:
                dev_success += 1
            else:
                dev_fail += 1
                total_failures += 1

        details.append({
            "device_id": dev.id,
            "device_name": dev.name,
            "success_count": dev_success,
            "fail_count": dev_fail,
            "faces_uploaded": dev_faces,
            "errors": dev_errors
        })

    return {
        "success": total_failures == 0,
        "total_users": len(users),
        "total_devices": len(devices),
        "total_faces_uploaded": total_faces_uploaded,
        "total_failures": total_failures,
        "details": details
    }

@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")
    group_name = user.group.name if user.group else user.group_name
    direction_name = user.group.direction_name if user.group else None
    tutor_name = user.group.tutor.full_name if (user.group and user.group.tutor) else None
    dept_name = user.department.name if user.department else None

    return UserOut(
        id=user.id,
        employee_no=user.employee_no,
        full_name=user.full_name,
        role=user.role,
        position=user.position,
        phone_number=user.phone_number,
        card_number=user.card_number,
        group_id=user.group_id,
        group_name=group_name,
        direction_name=direction_name,
        tutor_name=tutor_name,
        department_id=user.department_id,
        department_name=dept_name,
        photo_path=user.photo_path,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at
    )

@router.post("/", response_model=UserOut)
def create_user(
    user_in: UserCreate, 
    x_organization_id: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    org_id = int(x_organization_id) if (x_organization_id and x_organization_id.isdigit()) else 5
    
    # Faqat shu tashkilot doirasida ID raqam mavjudligini tekshiramiz
    existing = db.query(User).filter(User.employee_no == user_in.employee_no, User.organization_id == org_id).first()
    if existing:
        raise HTTPException(
            status_code=400, 
            detail=f"'{user_in.employee_no}' ID (Tabel) raqamli xodim allaqachon mavjud ({existing.full_name})! Iltimos, boshqa yangi ID raqam kiriting."
        )
    
    user_data = user_in.model_dump()
    new_user = User(**user_data)
    new_user.organization_id = org_id
    if not new_user.role or new_user.role == UserRole.STUDENT:
        new_user.role = UserRole.STAFF
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return get_user(new_user.id, db)

@router.put("/{user_id}", response_model=UserOut)
async def update_user(user_id: int, user_in: UserUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")
    
    old_emp_no = user.employee_no

    # Agar Tabel ID o'zgartirilayotgan bo'lsa, band emasligini tekshiramiz
    if user_in.employee_no and user_in.employee_no != old_emp_no:
        existing = db.query(User).filter(User.employee_no == user_in.employee_no, User.id != user_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Bu ID raqamli xodim/talaba allaqachon mavjud")

    for field, val in user_in.model_dump(exclude_unset=True).items():
        setattr(user, field, val)
    
    db.commit()
    db.refresh(user)

    # Avtomatik ravishda barcha faol terminallarda ham yangilash
    devices = db.query(Device).filter(Device.is_active == True).all()
    user_image_bytes = None
    if user.photo_path:
        local_filename = os.path.basename(user.photo_path)
        full_path = os.path.join(settings.UPLOAD_DIR, local_filename)
        if os.path.exists(full_path):
            try:
                with open(full_path, "rb") as f:
                    user_image_bytes = f.read()
            except Exception:
                pass

    for dev in devices:
        try:
            isapi = HikvisionISAPI(dev.ip_address, dev.port, dev.username, dev.password)
            if user_in.employee_no and user_in.employee_no != old_emp_no:
                # Agar ID o'zgargan bo'lsa, eski ID ni o'chirib, yangisini kiritamiz
                await isapi.delete_user(old_emp_no)
                await isapi.set_user_info(user.employee_no, user.full_name)
                if user_image_bytes:
                    await isapi.upload_face_picture(user.employee_no, user_image_bytes)
            else:
                # Ism yoki boshqa ma'lumot o'zgarganda terminaldagi ma'lumotni yangilaymiz
                await isapi.set_user_info(user.employee_no, user.full_name)
        except Exception:
            pass

    return get_user(user.id, db)

@router.delete("/{user_id}")
async def delete_user(user_id: int, sync_delete: bool = True, db: Session = Depends(get_db)):
    """Foydalanuvchini bazadan va xohishga ko'ra barcha terminallardan o'chirish"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")
    
    emp_no = user.employee_no
    db.delete(user)
    db.commit()

    # Terminallardan ham ISAPI orqali o'chirish
    if sync_delete:
        devices = db.query(Device).filter(Device.is_active == True).all()
        for dev in devices:
            try:
                isapi = HikvisionISAPI(dev.ip_address, dev.port, dev.username, dev.password)
                await isapi.delete_user(emp_no)
            except Exception:
                pass

    return {"message": "Foydalanuvchi muvaffaqiyatli o'chirildi"}

@router.post("/{user_id}/upload-photo")
async def upload_user_photo(
    user_id: int, 
    file: UploadFile = File(...), 
    db: Session = Depends(get_db)
):
    """Foydalanuvchi fotosuratini saqlash va terminallarga avtomatik yuborish"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")
    
    # Rasmni diskka saqlash
    ext = os.path.splitext(file.filename)[1] or ".jpg"
    filename = f"user_{user.employee_no}_{user.id}_{int(time.time())}{ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    user.photo_path = f"/uploads/{filename}"
    db.commit()
    db.refresh(user)

    # Faol terminallarga yangi yuz rasmini yuborish
    try:
        with open(file_path, "rb") as f:
            img_bytes = f.read()
        devices = db.query(Device).filter(Device.is_active == True).all()
        for dev in devices:
            isapi = HikvisionISAPI(dev.ip_address, dev.port, dev.username, dev.password)
            await isapi.set_user_info(user.employee_no, user.full_name)
            await isapi.upload_face_picture(user.employee_no, img_bytes)
    except Exception as e:
        logger.warning(f"Terminalga rasm yuborishda xatolik: {e}")

    return {"success": True, "photo_path": user.photo_path}

class PhotoBase64Request(BaseModel):
    image_data_url: str

@router.post("/{user_id}/upload-photo-base64")
async def upload_user_photo_base64(
    user_id: int, 
    req: PhotoBase64Request, 
    db: Session = Depends(get_db)
):
    """Base64 (veb-kamera yoki Face ID dan olingan) suratni saqlash va terminalga yuborish"""
    import base64
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")
    
    data_url = req.image_data_url
    if "," in data_url:
        data_url = data_url.split(",", 1)[1]
    
    try:
        img_bytes = base64.b64decode(data_url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Base64 dekodlashda xatolik: {e}")

    filename = f"user_{user.employee_no}_{user.id}_{int(time.time())}.jpg"
    file_path = os.path.join(settings.UPLOAD_DIR, filename)

    with open(file_path, "wb") as f:
        f.write(img_bytes)

    user.photo_path = f"/uploads/{filename}"
    db.commit()
    db.refresh(user)

    # Faol terminallarga yuborish
    try:
        devices = db.query(Device).filter(Device.is_active == True).all()
        for dev in devices:
            isapi = HikvisionISAPI(dev.ip_address, dev.port, dev.username, dev.password)
            await isapi.set_user_info(user.employee_no, user.full_name)
            await isapi.upload_face_picture(user.employee_no, img_bytes)
    except Exception as e:
        logger.warning(f"Terminalga rasm yuborishda xatolik: {e}")

    return {"success": True, "photo_path": user.photo_path}

@router.post("/{user_id}/capture-from-device/{device_id}")
async def capture_user_photo_from_device(
    user_id: int, 
    device_id: int, 
    db: Session = Depends(get_db)
):
    """Face ID terminali kamerasidan rasm tushirib foydalanuvchiga biriktirish va terminalga yuklash"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")
    
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Terminal topilmadi")
    
    isapi = HikvisionISAPI(device.ip_address, device.port, device.username, device.password)
    ok, img_bytes, msg = await isapi.take_snapshot()
    if not ok or not img_bytes:
        raise HTTPException(status_code=400, detail=f"Terminaldan rasm olishda xatolik: {msg}")

    filename = f"user_{user.employee_no}_{user.id}_{int(time.time())}.jpg"
    file_path = os.path.join(settings.UPLOAD_DIR, filename)

    with open(file_path, "wb") as f:
        f.write(img_bytes)

    user.photo_path = f"/uploads/{filename}"
    db.commit()
    db.refresh(user)

    # Terminallarga yuz rasmini yozish
    devices = db.query(Device).filter(Device.is_active == True).all()
    for dev in devices:
        dev_isapi = HikvisionISAPI(dev.ip_address, dev.port, dev.username, dev.password)
        await dev_isapi.set_user_info(user.employee_no, user.full_name)
        await dev_isapi.upload_face_picture(user.employee_no, img_bytes)

    return {
        "success": True,
        "photo_path": user.photo_path,
        "message": f"{device.name} kamerasidan rasm muvaffaqiyatli saqlandi va terminalga yuklandi"
    }


@router.post("/{user_id}/sync-to-device/{device_id}")
async def sync_user_to_device(
    user_id: int, 
    device_id: int, 
    db: Session = Depends(get_db)
):
    """Talaba/Xodim va uning yuz rasmini ma'lum bir terminalga ISAPI orqali yuborish"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")
    
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Qurilma topilmadi")
    
    isapi = HikvisionISAPI(device.ip_address, device.port, device.username, device.password)
    
    # 1. Foydalanuvchi ma'lumotlarini terminalga yozish
    u_ok, u_msg = await isapi.set_user_info(user.employee_no, user.full_name)
    if not u_ok:
        raise HTTPException(status_code=400, detail=f"Terminalga foydalanuvchini yozishda xatolik: {u_msg}")
    
    # 2. Agar rasm mavjud bo'lsa, yuz rasmini yuborish
    face_ok = False
    face_msg = "Rasm mavjud emas"
    if user.photo_path:
        local_filename = os.path.basename(user.photo_path)
        full_path = os.path.join(settings.UPLOAD_DIR, local_filename)
        if os.path.exists(full_path):
            with open(full_path, "rb") as f:
                img_bytes = f.read()
            face_ok, face_msg = await isapi.upload_face_picture(user.employee_no, img_bytes)

    return {
        "success": True,
        "user_sync": u_msg,
        "face_sync": face_msg if user.photo_path else "Rasm yuklanmagan"
    }

@router.post("/{user_id}/sync-to-all")
async def sync_user_to_all_devices(
    user_id: int, 
    db: Session = Depends(get_db)
):
    """Foydalanuvchi va yuz rasmini barcha faol terminallarga birdaniga sinxronizatsiya qilish"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")
    
    devices = db.query(Device).filter(Device.is_active == True).all()
    results = []

    # Rasmni o'qib olish (agar bo'lsa)
    img_bytes = None
    if user.photo_path:
        local_filename = os.path.basename(user.photo_path)
        full_path = os.path.join(settings.UPLOAD_DIR, local_filename)
        if os.path.exists(full_path):
            with open(full_path, "rb") as f:
                img_bytes = f.read()

    for dev in devices:
        isapi = HikvisionISAPI(dev.ip_address, dev.port, dev.username, dev.password)
        u_ok, u_msg = await isapi.set_user_info(user.employee_no, user.full_name)
        f_ok, f_msg = (False, "Rasm yo'q")
        if u_ok and img_bytes:
            f_ok, f_msg = await isapi.upload_face_picture(user.employee_no, img_bytes)
        
        results.append({
            "device_id": dev.id,
            "device_name": dev.name,
            "user_status": "Success" if u_ok else f"Fail ({u_msg})",
            "face_status": "Success" if f_ok else f"Fail/Skip ({f_msg})"
        })

    return {"results": results}

