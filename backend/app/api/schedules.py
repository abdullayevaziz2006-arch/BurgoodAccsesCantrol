from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.models.models import Shift, Schedule, User, Group, Department
from app.schemas.schemas import (
    ShiftCreate, ShiftUpdate, ShiftOut,
    ScheduleCreate, ScheduleUpdate, ScheduleOut,
    ScheduleAssignRequest
)

router = APIRouter(prefix="/schedules", tags=["Schedules & Shifts"])

# ========================================================
# 1. SMENALAR (SHIFTS) CRUD
# ========================================================

@router.get("/shifts", response_model=List[ShiftOut])
def get_all_shifts(db: Session = Depends(get_db)):
    """Barcha smenalar (ish vaqti) ro'yxatini olish"""
    return db.query(Shift).order_by(Shift.id.asc()).all()

@router.post("/shifts", response_model=ShiftOut, status_code=status.HTTP_201_CREATED)
def create_shift(shift_in: ShiftCreate, db: Session = Depends(get_db)):
    """Yangi smena yaratish"""
    shift = Shift(
        name=shift_in.name,
        start_time=shift_in.start_time,
        end_time=shift_in.end_time,
        lunch_start=shift_in.lunch_start or "12:00",
        lunch_end=shift_in.lunch_end or "13:00",
        late_tolerance_minutes=shift_in.late_tolerance_minutes,
        early_leave_tolerance_minutes=shift_in.early_leave_tolerance_minutes,
        color=shift_in.color
    )
    db.add(shift)
    db.commit()
    db.refresh(shift)
    return shift

@router.put("/shifts/{shift_id}", response_model=ShiftOut)
def update_shift(shift_id: int, shift_in: ShiftUpdate, db: Session = Depends(get_db)):
    """Smenani tahrirlash"""
    shift = db.query(Shift).filter(Shift.id == shift_id).first()
    if not shift:
        raise HTTPException(status_code=404, detail="Smena topilmadi")

    update_data = shift_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(shift, field, value)

    db.commit()
    db.refresh(shift)
    return shift

@router.delete("/shifts/{shift_id}")
def delete_shift(shift_id: int, db: Session = Depends(get_db)):
    """Smenani o'chirish"""
    shift = db.query(Shift).filter(Shift.id == shift_id).first()
    if not shift:
        raise HTTPException(status_code=404, detail="Smena topilmadi")

    db.delete(shift)
    db.commit()
    return {"message": "Smena o'chirildi"}

# ========================================================
# 2. HAFTALIK JADVALLAR (SCHEDULES) CRUD
# ========================================================

@router.get("", response_model=List[ScheduleOut])
def get_all_schedules(db: Session = Depends(get_db)):
    """Barcha haftalik jadvallar ro'yxatini olish"""
    return db.query(Schedule).order_by(Schedule.id.asc()).all()

@router.post("", response_model=ScheduleOut, status_code=status.HTTP_201_CREATED)
def create_schedule(sch_in: ScheduleCreate, db: Session = Depends(get_db)):
    """Yangi haftalik jadval yaratish"""
    schedule = Schedule(
        name=sch_in.name,
        description=sch_in.description,
        monday_shift_id=sch_in.monday_shift_id,
        tuesday_shift_id=sch_in.tuesday_shift_id,
        wednesday_shift_id=sch_in.wednesday_shift_id,
        thursday_shift_id=sch_in.thursday_shift_id,
        friday_shift_id=sch_in.friday_shift_id,
        saturday_shift_id=sch_in.saturday_shift_id,
        sunday_shift_id=sch_in.sunday_shift_id
    )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return schedule

@router.put("/{schedule_id}", response_model=ScheduleOut)
def update_schedule(schedule_id: int, sch_in: ScheduleUpdate, db: Session = Depends(get_db)):
    """Haftalik jadvalni tahrirlash"""
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Jadval topilmadi")

    update_data = sch_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(schedule, field, value)

    db.commit()
    db.refresh(schedule)
    return schedule

@router.delete("/{schedule_id}")
def delete_schedule(schedule_id: int, db: Session = Depends(get_db)):
    """Haftalik jadvalni o'chirish"""
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Jadval topilmadi")

    db.delete(schedule)
    db.commit()
    return {"message": "Jadval o'chirildi"}

# ========================================================
# 3. JADVAL BIRIKTIRISH (ASSIGNMENT)
# ========================================================

@router.post("/assign")
def assign_schedule(payload: ScheduleAssignRequest, db: Session = Depends(get_db)):
    """
    Jadvalni tanlangan xodimlar, talabalar, guruhlar yoki bo'limlarga biriktirish.
    schedule_id = None bo'lsa, jadval biriktiruvini bekor qiladi.
    """
    schedule = None
    if payload.schedule_id is not None:
        schedule = db.query(Schedule).filter(Schedule.id == payload.schedule_id).first()
        if not schedule:
            raise HTTPException(status_code=404, detail="Belgilangan jadval topilmadi")

    updated_users_count = 0
    updated_groups_count = 0
    updated_depts_count = 0

    # 1. Foydalanuvchilarga biriktirish
    if payload.user_ids:
        users = db.query(User).filter(User.id.in_(payload.user_ids)).all()
        for u in users:
            u.schedule_id = payload.schedule_id
            updated_users_count += 1

    # 2. Guruhlarga biriktirish (Guruhning o'ziga va shu guruhdagi barcha talabalarga)
    if payload.group_ids:
        groups = db.query(Group).filter(Group.id.in_(payload.group_ids)).all()
        for g in groups:
            g.schedule_id = payload.schedule_id
            updated_groups_count += 1
            # Shu guruhdagi barcha talabalarga ham yangilanadi (agar shaxsiy o'zgartirilmagan bo'lsa)
            students = db.query(User).filter(User.group_id == g.id).all()
            for s in students:
                s.schedule_id = payload.schedule_id
                updated_users_count += 1

    # 3. Bo'lim/Kafedralarga biriktirish (Bo'limning o'ziga va uning barcha xodimlariga)
    if payload.department_ids:
        depts = db.query(Department).filter(Department.id.in_(payload.department_ids)).all()
        for d in depts:
            d.schedule_id = payload.schedule_id
            updated_depts_count += 1
            dept_users = db.query(User).filter(User.department_id == d.id).all()
            for du in dept_users:
                du.schedule_id = payload.schedule_id
                updated_users_count += 1

    db.commit()
    return {
        "success": True,
        "message": "Jadval muvaffaqiyatli biriktirildi",
        "updated_users": updated_users_count,
        "updated_groups": updated_groups_count,
        "updated_departments": updated_depts_count
    }

@router.get("/assignments")
def get_assignments_summary(db: Session = Depends(get_db)):
    """Biriktirilgan jadvallar ro'yxatini olish"""
    schedules = {s.id: s.name for s in db.query(Schedule).all()}

    # Guruhlar
    groups = db.query(Group).all()
    group_list = [
        {
            "id": g.id,
            "name": g.name,
            "direction_name": g.direction_name,
            "schedule_id": g.schedule_id,
            "schedule_name": schedules.get(g.schedule_id, "Biriktirilmagan")
        }
        for g in groups
    ]

    # Xodimlar
    staff = db.query(User).filter(User.role != "student").all()
    staff_list = [
        {
            "id": u.id,
            "employee_no": u.employee_no,
            "full_name": u.full_name,
            "role": u.role.value if hasattr(u.role, 'value') else u.role,
            "position": u.position,
            "department_name": u.department.name if u.department else None,
            "schedule_id": u.schedule_id,
            "schedule_name": schedules.get(u.schedule_id, "Biriktirilmagan")
        }
        for u in staff
    ]

    # Bo'limlar
    depts = db.query(Department).all()
    dept_list = [
        {
            "id": d.id,
            "name": d.name,
            "type": d.type.value if hasattr(d.type, 'value') else d.type,
            "schedule_id": d.schedule_id,
            "schedule_name": schedules.get(d.schedule_id, "Biriktirilmagan")
        }
        for d in depts
    ]

    return {
        "groups": group_list,
        "staff": staff_list,
        "departments": dept_list
    }
