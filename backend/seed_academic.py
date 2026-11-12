from app.core.database import SessionLocal
from app.models.models import Faculty, Department, Group, User, UserRole

def seed_academic():
    db = SessionLocal()

    # 1. Fakultetlar
    f1 = db.query(Faculty).filter(Faculty.name == "Axborot Texnologiyalari Fakulteti").first()
    if not f1:
        f1 = Faculty(name="Axborot Texnologiyalari Fakulteti", code="ATF")
        db.add(f1)
        db.commit()
        db.refresh(f1)

    f2 = db.query(Faculty).filter(Faculty.name == "Iqtisodiyot va Boshqaruv Fakulteti").first()
    if not f2:
        f2 = Faculty(name="Iqtisodiyot va Boshqaruv Fakulteti", code="IBF")
        db.add(f2)
        db.commit()
        db.refresh(f2)

    # 2. Kafedralar / Bo'limlar
    d1 = db.query(Department).filter(Department.name == "Dasturiy Muhandislik kafedrasi").first()
    if not d1:
        d1 = Department(name="Dasturiy Muhandislik kafedrasi", code="DM", faculty_id=f1.id)
        db.add(d1)
    
    d2 = db.query(Department).filter(Department.name == "Axborot Xavfsizligi kafedrasi").first()
    if not d2:
        d2 = Department(name="Axborot Xavfsizligi kafedrasi", code="AX", faculty_id=f1.id)
        db.add(d2)

    d3 = db.query(Department).filter(Department.name == "Rektorat va O'quv-uslubiy bo'lim").first()
    if not d3:
        d3 = Department(name="Rektorat va O'quv-uslubiy bo'lim", code="O'UB", faculty_id=None)
        db.add(d3)

    db.commit()

    # 3. Tyutorlar / Xodimlar (rahbarlar)
    tutor1 = db.query(User).filter(User.employee_no == "390010").first()
    if not tutor1:
        tutor1 = User(
            employee_no="390010",
            full_name="Olimov Bobur Mansurovich",
            role=UserRole.STAFF,
            position="Katta Tyutor (Guruh rahbari)",
            phone_number="+998 90 555 11 22",
            department_id=d1.id
        )
        db.add(tutor1)
        db.commit()
        db.refresh(tutor1)

    tutor2 = db.query(User).filter(User.employee_no == "390011").first()
    if not tutor2:
        tutor2 = User(
            employee_no="390011",
            full_name="Xoliqova Shahnoza Erkinovna",
            role=UserRole.TEACHER,
            position="Tyutor / Katta o'qituvchi",
            phone_number="+998 91 444 33 22",
            department_id=d1.id
        )
        db.add(tutor2)
        db.commit()
        db.refresh(tutor2)

    # 4. Guruhlar (Yo'nalish va Tyutor biriktirilgan)
    g1 = db.query(Group).filter(Group.name == "941-21").first()
    if not g1:
        g1 = Group(
            name="941-21",
            direction_name="Dasturiy injiniring (kunduzgi)",
            course=3,
            faculty_id=f1.id,
            department_id=d1.id,
            tutor_id=tutor1.id
        )
        db.add(g1)
    
    g2 = db.query(Group).filter(Group.name == "942-21").first()
    if not g2:
        g2 = Group(
            name="942-21",
            direction_name="Kiberxavfsizlik muhandisligi",
            course=3,
            faculty_id=f1.id,
            department_id=d2.id,
            tutor_id=tutor2.id
        )
        db.add(g2)

    db.commit()

    # Talabalarni guruhga bog'lash
    st1 = db.query(User).filter(User.employee_no == "391001").first()
    if st1:
        st1.group_id = g1.id
        st1.department_id = d1.id

    st2 = db.query(User).filter(User.employee_no == "391002").first()
    if st2:
        st2.group_id = g2.id
        st2.department_id = d2.id

    db.commit()
    print("Fakultet, Kafedra, Guruh, Ta'lim yo'nalishi va Tyutorlar yaratildi!")
    db.close()

if __name__ == "__main__":
    seed_academic()
