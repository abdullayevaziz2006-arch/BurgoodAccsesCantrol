from fastapi import APIRouter, Depends, Query, Header, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
import openpyxl
from io import BytesIO

from app.core.database import get_db
from app.models.models import AccessLog, Device, User, DirectionType, UserRole
from app.schemas.schemas import AccessLogOut

router = APIRouter(prefix="/attendance", tags=["Attendance & Logs"])

@router.get("/logs", response_model=List[AccessLogOut])
def get_access_logs(
    skip: int = 0,
    limit: int = 100,
    device_id: Optional[int] = None,
    user_id: Optional[int] = None,
    direction: Optional[DirectionType] = None,
    start_date: Optional[str] = None, # "YYYY-MM-DD"
    end_date: Optional[str] = None,
    search: Optional[str] = None,
    x_organization_id: Optional[str] = Header(None),
    x_user_role: Optional[str] = Header(None),
    x_assigned_group_id: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    query = db.query(AccessLog).order_by(AccessLog.event_time.desc())
    
    if x_organization_id and x_organization_id.isdigit():
        query = query.filter(AccessLog.organization_id == int(x_organization_id))

    if x_user_role == "otdel_kadr":
        query = query.join(User, AccessLog.user_id == User.id, isouter=True).filter(
            (User.role != UserRole.STUDENT) | (AccessLog.user_id == None)
        )
    elif x_user_role == "tutor" and x_assigned_group_id and x_assigned_group_id.isdigit():
        query = query.join(User, AccessLog.user_id == User.id).filter(
            User.group_id == int(x_assigned_group_id)
        )

    if device_id:
        query = query.filter(AccessLog.device_id == device_id)
    if user_id:
        query = query.filter(AccessLog.user_id == user_id)
    if direction:
        query = query.filter(AccessLog.direction == direction)
    if search:
        query = query.filter(
            (AccessLog.user_name.ilike(f"%{search}%")) |
            (AccessLog.employee_no.ilike(f"%{search}%"))
        )
    if start_date:
        try:
            s_dt = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(AccessLog.event_time >= s_dt)
        except ValueError:
            pass
    if end_date:
        try:
            e_dt = datetime.strptime(f"{end_date} 23:59:59", "%Y-%m-%d %H:%M:%S")
            query = query.filter(AccessLog.event_time <= e_dt)
        except ValueError:
            pass

    logs = query.offset(skip).limit(limit).all()
    # Device nomini biriktirish
    results = []
    for log in logs:
        results.append(AccessLogOut(
            id=log.id,
            device_id=log.device_id,
            user_id=log.user_id,
            employee_no=log.employee_no,
            user_name=log.user_name,
            card_number=log.card_number,
            direction=log.direction,
            event_time=log.event_time,
            event_type=log.event_type,
            status=log.status,
            snapshot_url=log.snapshot_url,
            device_name=log.device.name if log.device else None
        ))
    return results

@router.get("/stats")
def get_attendance_stats(
    x_organization_id: Optional[str] = Header(None),
    x_user_role: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Bugungi umumiy statistika: kirganlar soni, chiqqanlar, faol qurilmalar"""
    today_start = datetime.combine(date.today(), datetime.min.time())
    
    user_q = db.query(User).filter(User.is_active == True)
    device_q = db.query(Device)
    log_q = db.query(AccessLog).filter(AccessLog.event_time >= today_start)

    if x_organization_id and x_organization_id.isdigit():
        org_id = int(x_organization_id)
        user_q = user_q.filter(User.organization_id == org_id)
        device_q = device_q.filter(Device.organization_id == org_id)
        log_q = log_q.filter(AccessLog.organization_id == org_id)

    if x_user_role == "otdel_kadr":
        user_q = user_q.filter(User.role != UserRole.STUDENT)
        log_q = log_q.join(User, AccessLog.user_id == User.id, isouter=True).filter(
            (User.role != UserRole.STUDENT) | (AccessLog.user_id == None)
        )

    total_users = user_q.count()
    total_devices = device_q.count()
    online_devices = device_q.filter(Device.status == "online").count()

    today_entries = log_q.filter(AccessLog.direction == DirectionType.ENTRY).count()
    today_exits = log_q.filter(AccessLog.direction == DirectionType.EXIT).count()

    # Bugun kelgan unikal foydalanuvchilar
    unique_present = log_q.filter(AccessLog.employee_no.isnot(None)).with_entities(AccessLog.employee_no).distinct().count()

    return {
        "total_users": total_users,
        "total_devices": total_devices,
        "online_devices": online_devices,
        "today_entries": today_entries,
        "today_exits": today_exits,
        "unique_present": unique_present
    }

@router.get("/export-excel")
def export_attendance_excel(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Davomat jurnalini Excel (XLSX) formatida yuklab berish"""
    query = db.query(AccessLog).order_by(AccessLog.event_time.desc())
    if start_date:
        query = query.filter(AccessLog.event_time >= datetime.strptime(start_date, "%Y-%m-%d"))
    if end_date:
        query = query.filter(AccessLog.event_time <= datetime.strptime(f"{end_date} 23:59:59", "%Y-%m-%d %H:%M:%S"))

    logs = query.limit(5000).all()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Davomat Jurnali"

    # Sarlavhalar
    headers = ["ID", "Vaqt", "Talaba/Xodim ID", "F.I.SH", "Yo'nalish (Kirish/Chiqish)", "Qurilma (Turniket)", "Holati", "Usul"]
    ws.append(headers)

    for cell in ws[1]:
        cell.font = openpyxl.styles.Font(bold=True, color="FFFFFF")
        cell.fill = openpyxl.styles.PatternFill(start_color="1F497D", end_color="1F497D", fill_type="solid")

    for log in logs:
        ws.append([
            log.id,
            log.event_time.strftime("%Y-%m-%d %H:%M:%S"),
            log.employee_no or "-",
            log.user_name or "Noma'lum",
            "KIRISH" if log.direction == DirectionType.ENTRY else "CHIQISH",
            log.device.name if log.device else f"Qurilma #{log.device_id}",
            log.status,
            log.event_type
        ])

    output = BytesIO()
    wb.save(output)
    output.seek(0)

    filename = f"davomat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/export-tabel-excel")
def export_tabel_excel(
    target_date: Optional[str] = None,
    x_organization_id: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Buxgalteriya va Kadrlar uchun Ish Vaqti Tabelini (Timesheet) Excel formatida chiqarish"""
    from datetime import date as dt_date
    t_date_str = target_date or dt_date.today().strftime("%Y-%m-%d")
    s_dt = datetime.strptime(t_date_str, "%Y-%m-%d")
    e_dt = datetime.strptime(f"{t_date_str} 23:59:59", "%Y-%m-%d %H:%M:%S")

    user_q = db.query(User).filter(User.is_active == True, User.role != UserRole.STUDENT)
    if x_organization_id and x_organization_id.isdigit():
        user_q = user_q.filter(User.organization_id == int(x_organization_id))
    staff_members = user_q.all()

    log_q = db.query(AccessLog).filter(AccessLog.event_time >= s_dt, AccessLog.event_time <= e_dt)
    if x_organization_id and x_organization_id.isdigit():
        log_q = log_q.filter(AccessLog.organization_id == int(x_organization_id))
    daily_logs = log_q.order_by(AccessLog.event_time.asc()).all()

    user_logs = {}
    for log in daily_logs:
        emp = log.employee_no
        if emp:
            if emp not in user_logs:
                user_logs[emp] = []
            user_logs[emp].append(log)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"Tabel_{t_date_str}"

    ws.merge_cells("A1:I1")
    title_cell = ws["A1"]
    title_cell.value = f"XODIMLAR ISH VAQTI TABELI (KUNLIK) — {t_date_str}"
    title_cell.font = openpyxl.styles.Font(bold=True, size=13, color="FFFFFF")
    title_cell.fill = openpyxl.styles.PatternFill(start_color="102A45", end_color="102A45", fill_type="solid")
    title_cell.alignment = openpyxl.styles.Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 30

    headers = ["№", "Tabel ID", "F.I.SH", "Bo'lim", "Lavozimi", "Birinchi Kirish", "Oxirgi Chiqish", "Ishlagan Vaqti", "Holati"]
    ws.append(headers)

    for cell in ws[2]:
        cell.font = openpyxl.styles.Font(bold=True, color="FFFFFF")
        cell.fill = openpyxl.styles.PatternFill(start_color="1F497D", end_color="1F497D", fill_type="solid")
        cell.alignment = openpyxl.styles.Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[2].height = 24

    for i, u in enumerate(staff_members, 1):
        logs = user_logs.get(u.employee_no, [])
        first_in = "-"
        last_out = "-"
        worked_str = "-"
        status = "Kelmagan"

        if logs:
            entries = [l.event_time for l in logs if l.direction == DirectionType.ENTRY]
            exits = [l.event_time for l in logs if l.direction == DirectionType.EXIT]
            
            if entries:
                first_in_dt = min(entries)
                first_in = first_in_dt.strftime("%H:%M:%S")
                if first_in_dt.time() > datetime.strptime("09:15:00", "%H:%M:%S").time():
                    status = "Kechikkan"
                else:
                    status = "Kelgan (Vaqtida)"
            else:
                first_in_dt = min(l.event_time for l in logs)
                first_in = first_in_dt.strftime("%H:%M:%S")
                status = "Kelgan"

            if exits:
                last_out_dt = max(exits)
                last_out = last_out_dt.strftime("%H:%M:%S")
            else:
                last_out_dt = max(l.event_time for l in logs)
                last_out = last_out_dt.strftime("%H:%M:%S")

            diff = last_out_dt - first_in_dt
            hours = int(diff.total_seconds() // 3600)
            minutes = int((diff.total_seconds() % 3600) // 60)
            worked_str = f"{hours} soat {minutes} daq" if hours > 0 or minutes > 0 else "0 daq"

        ws.append([
            i,
            u.employee_no,
            u.full_name,
            u.department.name if u.department else (u.group_name or "-"),
            u.position or "Xodim",
            first_in,
            last_out,
            worked_str,
            status
        ])

    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = openpyxl.utils.get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

    output = BytesIO()
    wb.save(output)
    output.seek(0)

    filename = f"tabel_{t_date_str}.xlsx"
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# ========================================================
# HIKVISION HTTP ALARM LISTENER (2-USUL)
# Turniketning o'zidan to'g'ridan-to'g'ri o'tish hodisalarini qabul qilish
# ========================================================
from app.services.hikvision_listener import handle_hikvision_http_event

@router.post("/hikvision-alarm")
@router.post("/hikvision-event")
async def receive_hikvision_http_alarm(request: Request, db: Session = Depends(get_db)):
    """Hikvision Face ID / Turniketlardan to'g'ridan-to'g'ri HTTP orqali jonli hodisalarni qabul qilish"""
    return await handle_hikvision_http_event(request, db)
