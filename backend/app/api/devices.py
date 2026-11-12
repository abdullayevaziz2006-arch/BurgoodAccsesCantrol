from fastapi import APIRouter, Depends, HTTPException, Query, Header, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import os
import uuid

from app.core.database import get_db
from app.models.models import Device, DeviceStatus, User, Organization
from app.schemas.schemas import DeviceCreate, DeviceUpdate, DeviceOut, DeviceTestResult
from app.services.hikvision_isapi import HikvisionISAPI

router = APIRouter(prefix="/devices", tags=["Devices"])

@router.get("/", response_model=List[DeviceOut])
def get_devices(x_organization_id: Optional[str] = Header(None), db: Session = Depends(get_db)):
    query = db.query(Device)
    if x_organization_id and x_organization_id.isdigit():
        org_id = int(x_organization_id)
        # Shu tashkilotga biriktirilgan yoki umumiy (hech kimga biriktirilmagan) qurilmalarni ko'rsatish
        query = query.filter((Device.organization_id == org_id) | (Device.organization_id == None))
    return query.all()

@router.get("/{device_id}", response_model=DeviceOut)
def get_device(device_id: int, db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Qurilma topilmadi")
    return device

@router.get("/{device_id}/credentials")
def get_device_credentials(device_id: int, db: Session = Depends(get_db)):
    """Lokal sinxronizatsiya va terminaldan tortib olish uchun maxsus ulanish ma'lumotlari"""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Qurilma topilmadi")
    return {
        "id": device.id,
        "name": device.name,
        "ip_address": device.ip_address,
        "port": device.port,
        "username": device.username,
        "password": device.password
    }

@router.post("/", response_model=DeviceOut)
async def create_device(
    device_in: DeviceCreate, 
    x_organization_id: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    # IP tekshirish
    existing = db.query(Device).filter(Device.ip_address == device_in.ip_address).first()
    if existing:
        raise HTTPException(status_code=400, detail="Bu IP manzilga ega qurilma allaqachon mavjud")
    
    org_id = None
    if device_in.organization_id:
        org_id = device_in.organization_id
    elif x_organization_id and x_organization_id.isdigit():
        org_id = int(x_organization_id)

    # Terminal bilan aloqani tekshirish
    isapi = HikvisionISAPI(
        ip=device_in.ip_address,
        port=device_in.port,
        username=device_in.username,
        password=device_in.password
    )
    try:
        success, info = await isapi.get_device_info()
    except Exception as err:
        logger.warning(f"ISAPI get_device_info xatolik: {err}")
        success, info = False, {}
    
    new_device = Device(
        name=device_in.name,
        ip_address=device_in.ip_address,
        port=device_in.port,
        username=device_in.username,
        password=device_in.password,
        direction=device_in.direction,
        universal_mode=device_in.universal_mode or "smart_auto",
        universal_options=device_in.universal_options or "check_in,break_out,break_in,check_out",
        lunch_start=device_in.lunch_start or "12:00",
        lunch_end=device_in.lunch_end or "14:00",
        door_no=device_in.door_no,
        location=device_in.location,
        is_active=device_in.is_active,
        organization_id=org_id,
        status=DeviceStatus.ONLINE if success else DeviceStatus.OFFLINE,
        serial_number=info.get("serialNumber") if success else None,
        model=info.get("model") if success else None,
        firmware_version=info.get("firmwareVersion") if success else None,
        last_seen=datetime.utcnow() if success else None
    )
    db.add(new_device)
    db.commit()
    db.refresh(new_device)

    # Agar universal bo'lsa, terminalga maxsus xush kelibsiz xabari va 4 ta holat tugmalarini sozlash
    if new_device.direction == DirectionType.UNIVERSAL and success:
        try:
            await isapi.set_custom_prompt(success_text="Xush kelibsiz")
            raw_opts = new_device.universal_options or "check_in,break_out,break_in,check_out"
            opts = [o.strip() for o in raw_opts.split(",") if o.strip()]
            await isapi.configure_attendance_status_keys(opts)
        except Exception:
            pass

    return new_device

@router.put("/{device_id}", response_model=DeviceOut)
async def update_device(device_id: int, device_in: DeviceUpdate, db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Qurilma topilmadi")
    
    update_data = device_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(device, field, value)
    
    db.commit()
    db.refresh(device)

    # Agar universal o'rnatilgan bo'lsa terminalga sozlash
    if device.direction == DirectionType.UNIVERSAL:
        try:
            isapi = HikvisionISAPI(
                ip=device.ip_address,
                port=device.port,
                username=device.username,
                password=device.password
            )
            await isapi.set_custom_prompt(success_text="Xush kelibsiz")
            raw_opts = device.universal_options or "check_in,break_out,break_in,check_out"
            opts = [o.strip() for o in raw_opts.split(",") if o.strip()]
            await isapi.configure_attendance_status_keys(opts)
        except Exception:
            pass

    return device

@router.delete("/{device_id}")
def delete_device(device_id: int, db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Qurilma topilmadi")
    
    db.delete(device)
    db.commit()
    return {"message": "Qurilma muvaffaqiyatli o'chirildi"}

@router.post("/{device_id}/test", response_model=DeviceTestResult)
async def test_device_connection(device_id: int, db: Session = Depends(get_db)):
    """Terminal ulanishini testlash va ISAPI ma'lumotlarini yangilash"""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Qurilma topilmadi")
    
    isapi = HikvisionISAPI(
        ip=device.ip_address,
        port=device.port,
        username=device.username,
        password=device.password
    )
    try:
        success, info = await isapi.get_device_info()
    except Exception as err:
        success, info = False, {"error": str(err)}
    if success:
        device.status = DeviceStatus.ONLINE
        device.serial_number = info.get("serialNumber")
        device.model = info.get("model")
        device.firmware_version = info.get("firmwareVersion")
        device.last_seen = datetime.utcnow()
        db.commit()
        return DeviceTestResult(
            success=True,
            message="Terminal bilan muvaffaqiyatli bog'lanildi!",
            device_info=info
        )
    else:
        # Agar bulutli server lokal IP ga to'g'ridan-to'g'ri ulana olmasa,
        # lekin terminal so'nggi 5 daqiqa (300 soniya) ichida serverga HTTP event / heartbeat yuborgan bo'lsa
        if device.last_seen:
            diff_seconds = (datetime.utcnow() - device.last_seen).total_seconds()
            if diff_seconds < 300:
                device.status = DeviceStatus.ONLINE
                db.commit()
                return DeviceTestResult(
                    success=True,
                    message=f"Terminal bilan aloqa a'lo darajada! (HTTP oqimi orqali oxirgi signal: {int(diff_seconds)} soniya oldin)",
                    device_info={
                        "model": device.model or "Hikvision Terminal",
                        "serialNumber": device.serial_number or "HTTP Listener Active"
                    }
                )
        device.status = DeviceStatus.OFFLINE
        db.commit()
        return DeviceTestResult(
            success=False,
            message=f"Terminal bilan ulanib bo'lmadi: {info.get('error')}",
            device_info=None
        )

@router.post("/{device_id}/mark-online")
def mark_device_online(device_id: int, db: Session = Depends(get_db)):
    """Lokal bridge yoki terminal hodisalari orqali qurilmani ONLINE deb belgilash"""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Qurilma topilmadi")
    device.status = DeviceStatus.ONLINE
    device.last_seen = datetime.utcnow()
    db.commit()
    return {"success": True, "status": "online"}

@router.post("/{device_id}/open-door")
async def open_door_remotely(device_id: int, db: Session = Depends(get_db)):
    """Turniket eshigini masofadan ochish (ISAPI Remote Open)"""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Qurilma topilmadi")
    
    isapi = HikvisionISAPI(
        ip=device.ip_address,
        port=device.port,
        username=device.username,
        password=device.password
    )
    success, msg = await isapi.remote_door_control(door_no=device.door_no, cmd="open")
    if not success:
        raise HTTPException(status_code=400, detail=f"Eshikni ochishda xatolik: {msg}")
    
    return {"success": True, "message": f"{device.name} eshigi muvaffaqiyatli ochildi"}

@router.get("/{device_id}/snapshot")
async def get_device_snapshot(device_id: int, db: Session = Depends(get_db)):
    """Face ID terminali kamerasidan jonli rasm olish (JPEG formatda)"""
    from fastapi.responses import Response
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Qurilma topilmadi")
    
    isapi = HikvisionISAPI(
        ip=device.ip_address,
        port=device.port,
        username=device.username,
        password=device.password
    )
    ok, img_bytes, msg = await isapi.take_snapshot()
    if not ok or not img_bytes:
        raise HTTPException(status_code=400, detail=msg)
    
    return Response(content=img_bytes, media_type="image/jpeg")

@router.post("/{device_id}/capture-face")
async def capture_face_from_device(device_id: int, db: Session = Depends(get_db)):
    """Terminal kamerasidan tezkor rasm olib base64 formatida qaytarish"""
    import base64
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Qurilma topilmadi")
    
    isapi = HikvisionISAPI(
        ip=device.ip_address,
        port=device.port,
        username=device.username,
        password=device.password
    )
    ok, img_bytes, msg = await isapi.take_snapshot()
    if not ok or not img_bytes:
        raise HTTPException(status_code=400, detail=msg)
    
    b64_str = base64.b64encode(img_bytes).decode('utf-8')
    data_url = f"data:image/jpeg;base64,{b64_str}"
    
    return {
        "success": True,
        "image_data_url": data_url,
        "device_id": device.id,
        "device_name": device.name,
        "size_bytes": len(img_bytes)
    }

@router.post("/{device_id}/import-from-terminal")
async def import_from_terminal(
    device_id: int, 
    request: Request,
    db: Session = Depends(get_db),
    x_organization_id: Optional[str] = Header(None)
):
    """Terminaldagi barcha xodimlarni va ularning yuz rasmlarini o'qib olib, bazaga saqlash"""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Qurilma topilmadi")
    
    org_id = device.organization_id
    if not org_id and x_organization_id and x_organization_id.isdigit():
        org_id = int(x_organization_id)
    if not org_id:
        first_org = db.query(Organization).first()
        org_id = first_org.id if first_org else None

    isapi = HikvisionISAPI(
        ip=device.ip_address,
        port=device.port,
        username=device.username,
        password=device.password
    )
    
    success, users_list, msg = await isapi.get_all_users()
    if not success or not users_list:
        raise HTTPException(status_code=400, detail=msg or "Terminaldan xodimlar topilmadi yoki ulanishda xatolik!")

    imported_count = 0
    updated_count = 0
    faces_count = 0

    uploads_dir = os.path.join(os.getcwd(), "uploads", "faces")
    os.makedirs(uploads_dir, exist_ok=True)

    for item in users_list:
        emp_no = item["employee_no"]
        name = item["name"]
        has_face = item.get("has_face", False)

        # Bazada borligini tekshiramiz
        existing = db.query(User).filter(User.employee_no == emp_no).first()
        if existing:
            user = existing
            if not user.full_name or user.full_name.startswith("Xodim #"):
                user.full_name = name
            updated_count += 1
        else:
            user = User(
                full_name=name,
                employee_no=emp_no,
                role="staff",
                is_active=True,
                organization_id=org_id
            )
            db.add(user)
            db.flush()
            imported_count += 1

        # Rasm yuklab olish (har gal terminaldan yangi surat kelganda yangilaymiz)
        if has_face:
            face_url = item.get("face_url")
            face_ok, face_bytes, _ = await isapi.get_face_picture(emp_no, face_url=face_url)
            if face_ok and face_bytes:
                filename = f"user_{user.id}_{uuid.uuid4().hex[:8]}.jpg"
                file_path = os.path.join(uploads_dir, filename)
                try:
                    with open(file_path, "wb") as f:
                        f.write(face_bytes)
                    user.photo_path = f"/uploads/faces/{filename}"
                    faces_count += 1
                except Exception:
                    pass

    db.commit()
    return {
        "success": True,
        "imported": imported_count,
        "updated": updated_count,
        "faces_imported": faces_count,
        "total": len(users_list),
        "message": f"Muvaffaqiyatli: {imported_count} ta yangi xodim qo'shildi, {updated_count} ta yangilandi, {faces_count} ta yuz rasmi saqlandi!"
    }

