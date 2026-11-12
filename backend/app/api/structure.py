from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Header
from sqlalchemy.orm import Session
from typing import List, Optional
import openpyxl
from io import BytesIO
from fastapi.responses import StreamingResponse

from app.core.database import get_db
from app.models.models import Faculty, Department, Group, User, UserRole, DepartmentType
from app.schemas.schemas import (
    FacultyCreate, FacultyOut,
    DepartmentCreate, DepartmentOut,
    GroupCreate, GroupUpdate, GroupOut,
    UserOut
)

router = APIRouter(prefix="/structure", tags=["University Structure"])


# ==============================================================================
# 1. FAKULTETLAR
# ==============================================================================
@router.get("/faculties", response_model=List[FacultyOut])
def get_faculties(x_organization_id: Optional[str] = Header(None), db: Session = Depends(get_db)):
    query = db.query(Faculty)
    if x_organization_id and x_organization_id.isdigit():
        query = query.filter(Faculty.organization_id == int(x_organization_id))
    return query.all()

@router.post("/faculties", response_model=FacultyOut)
def create_faculty(data: FacultyCreate, x_organization_id: Optional[str] = Header(None), db: Session = Depends(get_db)):
    existing = db.query(Faculty).filter(Faculty.name == data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Bu nomdagi fakultet allaqachon mavjud")
    fac = Faculty(**data.model_dump())
    if x_organization_id and x_organization_id.isdigit():
        fac.organization_id = int(x_organization_id)
    else:
        fac.organization_id = 1
    db.add(fac)
    db.commit()
    db.refresh(fac)
    return fac

# Template: Fakultetlar
@router.get("/faculties/template")
def download_faculties_template():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Fakultetlar"
    ws.append(["Fakultet Nomi", "Kodi"])
    ws.append(["Axborot Texnologiyalari Fakulteti", "ATF"])
    ws.append(["Iqtisodiyot Fakulteti", "IF"])
    for cell in ws[1]:
        cell.font = openpyxl.styles.Font(bold=True, color="FFFFFF")
        cell.fill = openpyxl.styles.PatternFill(start_color="1F497D", end_color="1F497D", fill_type="solid")
    out = BytesIO()
    wb.save(out)
    out.seek(0)
    return StreamingResponse(
        out, 
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
        headers={"Content-Disposition": "attachment; filename=fakultetlar_shablon.xlsx"}
    )

# Excel orqali Fakultetlarni massiv qo'shish
@router.post("/faculties/import-excel")
async def import_faculties_excel(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        content = await file.read()
        wb = openpyxl.load_workbook(BytesIO(content))
        ws = wb.active
        created_count = 0
        skipped_count = 0

        # Birinchi qator sarlavha deb hisoblanadi: [Nomi, Kodi]
        for row in ws.iter_rows(min_row=2, values_only=True):
            if not row or not row[0]:
                continue
            name = str(row[0]).strip()
            code = str(row[1]).strip() if len(row) > 1 and row[1] else None
            
            existing = db.query(Faculty).filter(Faculty.name == name).first()
            if not existing:
                fac = Faculty(name=name, code=code)
                db.add(fac)
                created_count += 1
            else:
                skipped_count += 1
        
        db.commit()
        return {"success": True, "created": created_count, "skipped": skipped_count}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Excel faylni o'qishda xatolik: {str(e)}")

@router.delete("/faculties/{faculty_id}")
def delete_faculty(faculty_id: int, db: Session = Depends(get_db)):
    fac = db.query(Faculty).filter(Faculty.id == faculty_id).first()
    if not fac:
        raise HTTPException(status_code=404, detail="Fakultet topilmadi")
    db.delete(fac)
    db.commit()
    return {"message": "Fakultet o'chirildi"}


# ==============================================================================
# 2. KAFEDRALAR VA BO'LIMLAR
# ==============================================================================
@router.get("/departments", response_model=List[DepartmentOut])
def get_departments(
    type: Optional[str] = None, 
    x_organization_id: Optional[str] = Header(None), 
    db: Session = Depends(get_db)
):
    query = db.query(Department)
    if x_organization_id and x_organization_id.isdigit():
        query = query.filter(Department.organization_id == int(x_organization_id))
    if type:
        query = query.filter(Department.type == type)
    departments = query.all()
    results = []
    for d in departments:
        head_name = d.head.full_name if d.head else None
        results.append(DepartmentOut(
            id=d.id,
            name=d.name,
            code=d.code,
            type=d.type.value if hasattr(d.type, 'value') else str(d.type),
            faculty_id=d.faculty_id,
            head_id=d.head_id,
            head_name=head_name,
            head_title=d.head_title,
            faculty_name=d.faculty.name if d.faculty else None,
            created_at=d.created_at
        ))
    return results

@router.post("/departments", response_model=DepartmentOut)
def create_department(data: DepartmentCreate, db: Session = Depends(get_db)):
    existing = db.query(Department).filter(Department.name == data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Bu nomdagi kafedra yoki bo'lim allaqachon mavjud")
    
    dep_dict = data.model_dump()
    dep_type = DepartmentType.DIVISION if dep_dict.get("type") == "division" else DepartmentType.DEPARTMENT
    dep_dict["type"] = dep_type

    dep = Department(**dep_dict)
    db.add(dep)
    db.commit()
    db.refresh(dep)
    
    head_name = dep.head.full_name if dep.head else None
    return DepartmentOut(
        id=dep.id,
        name=dep.name,
        code=dep.code,
        type=dep.type.value,
        faculty_id=dep.faculty_id,
        head_id=dep.head_id,
        head_name=head_name,
        head_title=dep.head_title,
        faculty_name=dep.faculty.name if dep.faculty else None,
        created_at=dep.created_at
    )

# Template: Kafedralar
@router.get("/departments/template")
def download_departments_template():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Kafedralar"
    ws.append(["Kafedra Nomi", "Kodi", "Fakultet Nomi"])
    ws.append(["Dasturiy Muhandislik kafedrasi", "DM", "Axborot Texnologiyalari Fakulteti"])
    ws.append(["Axborot Xavfsizligi kafedrasi", "AX", "Axborot Texnologiyalari Fakulteti"])
    for cell in ws[1]:
        cell.font = openpyxl.styles.Font(bold=True, color="FFFFFF")
        cell.fill = openpyxl.styles.PatternFill(start_color="1F497D", end_color="1F497D", fill_type="solid")
    out = BytesIO()
    wb.save(out)
    out.seek(0)
    return StreamingResponse(
        out, 
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
        headers={"Content-Disposition": "attachment; filename=kafedralar_shablon.xlsx"}
    )

# Template: Bo'limlar
@router.get("/divisions/template")
def download_divisions_template():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Bolimlar"
    ws.append(["Bo'lim Nomi", "Bo'lim Boshlig'i (F.I.SH)"])
    ws.append(["Rektorat", "Karimov Rustam Aliyevich"])
    ws.append(["O'quv-uslubiy bo'lim", "Olimov Bobur Mansurovich"])
    ws.append(["Kadrlar bo'limi", "Xoliqova Shahnoza Erkinovna"])
    for cell in ws[1]:
        cell.font = openpyxl.styles.Font(bold=True, color="FFFFFF")
        cell.fill = openpyxl.styles.PatternFill(start_color="1F497D", end_color="1F497D", fill_type="solid")
    out = BytesIO()
    wb.save(out)
    out.seek(0)
    return StreamingResponse(
        out, 
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
        headers={"Content-Disposition": "attachment; filename=bolimlar_shablon.xlsx"}
    )

# Excel orqali Kafedra va Bo'limlarni massiv qo'shish
@router.post("/departments/import-excel")
async def import_departments_excel(
    type: str = "department", # "department" yoki "division"
    file: UploadFile = File(...), 
    db: Session = Depends(get_db)
):
    try:
        content = await file.read()
        wb = openpyxl.load_workbook(BytesIO(content))
        ws = wb.active
        created_count = 0
        skipped_count = 0
        target_type = DepartmentType.DIVISION if type == "division" else DepartmentType.DEPARTMENT

        for row in ws.iter_rows(min_row=2, values_only=True):
            if not row or not row[0]:
                continue
            name = str(row[0]).strip()

            if type == "division":
                # Bo'limlar uchun: [Bo'lim Nomi, Bo'lim Boshlig'i (F.I.SH)]
                head_name = str(row[1]).strip() if len(row) > 1 and row[1] else None
                head_id = None
                if head_name:
                    head_user = db.query(User).filter(User.full_name.ilike(f"%{head_name}%")).first()
                    if head_user:
                        head_id = head_user.id

                existing = db.query(Department).filter(Department.name == name).first()
                if not existing:
                    dept = Department(
                        name=name,
                        type=DepartmentType.DIVISION,
                        head_id=head_id,
                        head_title="Bo'lim boshlig'i"
                    )
                    db.add(dept)
                    created_count += 1
                else:
                    if head_id:
                        existing.head_id = head_id
                        existing.head_title = "Bo'lim boshlig'i"
                    skipped_count += 1
            else:
                # Kafedralar uchun: [Kafedra Nomi, Kodi, Fakultet Nomi]
                code = str(row[1]).strip() if len(row) > 1 and row[1] else None
                faculty_name = str(row[2]).strip() if len(row) > 2 and row[2] else None
                faculty_id = None
                if faculty_name:
                    fac = db.query(Faculty).filter(Faculty.name.ilike(f"%{faculty_name}%")).first()
                    if fac:
                        faculty_id = fac.id

                existing = db.query(Department).filter(Department.name == name).first()
                if not existing:
                    dept = Department(
                        name=name,
                        code=code,
                        type=DepartmentType.DEPARTMENT,
                        faculty_id=faculty_id
                    )
                    db.add(dept)
                    created_count += 1
                else:
                    skipped_count += 1
        
        db.commit()
        return {"success": True, "created": created_count, "skipped": skipped_count}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Excel importda xatolik: {str(e)}")

@router.delete("/departments/{dept_id}")
def delete_department(dept_id: int, db: Session = Depends(get_db)):
    dep = db.query(Department).filter(Department.id == dept_id).first()
    if not dep:
        raise HTTPException(status_code=404, detail="Kafedra/Bo'lim topilmadi")
    db.delete(dep)
    db.commit()
    return {"message": "Kafedra/Bo'lim o'chirildi"}


# ==============================================================================
# 3. GURUHLAR VA TA'LIM YO'NALISHLARI (TYUTOR BILAN)
# ==============================================================================
@router.get("/groups", response_model=List[GroupOut])
def get_groups(x_organization_id: Optional[str] = Header(None), db: Session = Depends(get_db)):
    query = db.query(Group)
    if x_organization_id and x_organization_id.isdigit():
        query = query.filter(Group.organization_id == int(x_organization_id))
    groups = query.all()
    results = []
    for g in groups:
        st_count = db.query(User).filter(User.group_id == g.id).count()
        results.append(GroupOut(
            id=g.id,
            name=g.name,
            direction_name=g.direction_name,
            course=g.course,
            faculty_id=g.faculty_id,
            department_id=g.department_id,
            tutor_id=g.tutor_id,
            faculty_name=g.faculty.name if g.faculty else None,
            department_name=g.department.name if g.department else None,
            tutor_name=g.tutor.full_name if g.tutor else None,
            student_count=st_count,
            created_at=g.created_at
        ))
    return results

@router.post("/groups", response_model=GroupOut)
def create_group(data: GroupCreate, db: Session = Depends(get_db)):
    existing = db.query(Group).filter(Group.name == data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Bu nomdagi guruh allaqachon mavjud")
    grp = Group(**data.model_dump())
    db.add(grp)
    db.commit()
    db.refresh(grp)
    return GroupOut(
        id=grp.id,
        name=grp.name,
        direction_name=grp.direction_name,
        course=grp.course,
        faculty_id=grp.faculty_id,
        department_id=grp.department_id,
        tutor_id=grp.tutor_id,
        faculty_name=grp.faculty.name if grp.faculty else None,
        department_name=grp.department.name if grp.department else None,
        tutor_name=grp.tutor.full_name if grp.tutor else None,
        student_count=0,
        created_at=grp.created_at
    )

@router.put("/groups/{group_id}", response_model=GroupOut)
def update_group(group_id: int, data: GroupUpdate, db: Session = Depends(get_db)):
    """Guruh ma'lumotlarini (shu jumladan tyutorni) yangilash"""
    grp = db.query(Group).filter(Group.id == group_id).first()
    if not grp:
        raise HTTPException(status_code=404, detail="Guruh topilmadi")
    
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(grp, field, value)
    
    db.commit()
    db.refresh(grp)
    
    student_count = db.query(User).filter(User.group_id == grp.id).count()
    return GroupOut(
        id=grp.id,
        name=grp.name,
        direction_name=grp.direction_name,
        course=grp.course,
        faculty_id=grp.faculty_id,
        department_id=grp.department_id,
        tutor_id=grp.tutor_id,
        faculty_name=grp.faculty.name if grp.faculty else None,
        department_name=grp.department.name if grp.department else None,
        tutor_name=grp.tutor.full_name if grp.tutor else None,
        student_count=student_count,
        created_at=grp.created_at
    )

@router.put("/groups/{group_id}/assign-tutor")
def assign_tutor_to_group(group_id: int, tutor_id: Optional[int] = None, db: Session = Depends(get_db)):
    """Guruhga tezkor tyutor biriktirish yoki tyutorni o'zgartirish"""
    grp = db.query(Group).filter(Group.id == group_id).first()
    if not grp:
        raise HTTPException(status_code=404, detail="Guruh topilmadi")
    
    if tutor_id:
        tutor = db.query(User).filter(User.id == tutor_id).first()
        if not tutor:
            raise HTTPException(status_code=404, detail="Tyutor topilmadi")
        grp.tutor_id = tutor.id
    else:
        grp.tutor_id = None
        
    db.commit()
    db.refresh(grp)
    return {
        "success": True, 
        "group_id": grp.id, 
        "tutor_id": grp.tutor_id,
        "tutor_name": grp.tutor.full_name if grp.tutor else None
    }

# Template: Guruhlar
@router.get("/groups/template")
def download_groups_template():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Guruhlar"
    ws.append(["Guruh Nomi", "Ta'lim Yo'nalishi", "Kurs", "Kafedra Nomi"])
    ws.append(["941-21", "Dasturiy injiniring (kunduzgi)", 3, "Dasturiy Muhandislik kafedrasi"])
    ws.append(["942-21", "Kiberxavfsizlik muhandisligi", 3, "Axborot Xavfsizligi kafedrasi"])
    for cell in ws[1]:
        cell.font = openpyxl.styles.Font(bold=True, color="FFFFFF")
        cell.fill = openpyxl.styles.PatternFill(start_color="1F497D", end_color="1F497D", fill_type="solid")
    out = BytesIO()
    wb.save(out)
    out.seek(0)
    return StreamingResponse(
        out, 
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
        headers={"Content-Disposition": "attachment; filename=guruhlar_shablon.xlsx"}
    )

# Excel orqali Guruhlarni massiv qo'shish
@router.post("/groups/import-excel")
async def import_groups_excel(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        content = await file.read()
        wb = openpyxl.load_workbook(BytesIO(content))
        ws = wb.active
        created_count = 0
        skipped_count = 0

        # Qatorlar: [Guruh_Nomi, Yo'nalish_Nomi, Kurs, Kafedra_Nomi]
        for row in ws.iter_rows(min_row=2, values_only=True):
            if not row or not row[0]:
                continue
            name = str(row[0]).strip()
            direction = str(row[1]).strip() if len(row) > 1 and row[1] else None
            course = int(row[2]) if len(row) > 2 and row[2] else 1
            dept_name = str(row[3]).strip() if len(row) > 3 and row[3] else None
            
            dept_id = None
            fac_id = None
            if dept_name:
                dep = db.query(Department).filter(Department.name.ilike(f"%{dept_name}%")).first()
                if dep:
                    dept_id = dep.id
                    fac_id = dep.faculty_id

            existing = db.query(Group).filter(Group.name == name).first()
            if not existing:
                grp = Group(
                    name=name,
                    direction_name=direction,
                    course=course,
                    department_id=dept_id,
                    faculty_id=fac_id
                )
                db.add(grp)
                created_count += 1
            else:
                skipped_count += 1
        
        db.commit()
        return {"success": True, "created": created_count, "skipped": skipped_count}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Guruhlar Excel importida xatolik: {str(e)}")

@router.delete("/groups/{group_id}")
def delete_group(group_id: int, db: Session = Depends(get_db)):
    grp = db.query(Group).filter(Group.id == group_id).first()
    if not grp:
        raise HTTPException(status_code=404, detail="Guruh topilmadi")
    db.delete(grp)
    db.commit()
    return {"message": "Guruh o'chirildi"}


# ==============================================================================
# 4. POTENSIAL TYUTORLAR VA MUDIRLAR RO'YXATI
# ==============================================================================
@router.get("/potential-tutors", response_model=List[UserOut])
def get_potential_tutors(db: Session = Depends(get_db)):
    tutors = db.query(User).filter(User.role.in_([UserRole.TEACHER, UserRole.STAFF])).all()
    return [
        UserOut(
            id=t.id,
            employee_no=t.employee_no,
            full_name=t.full_name,
            role=t.role,
            position=t.position,
            phone_number=t.phone_number,
            card_number=t.card_number,
            department_id=t.department_id,
            department_name=t.department.name if t.department else None,
            is_active=t.is_active,
            created_at=t.created_at
        )
        for t in tutors
    ]
