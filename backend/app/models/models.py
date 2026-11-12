import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
from app.core.database import Base

class UserRole(str, enum.Enum):
    STUDENT = "student"
    TEACHER = "teacher"
    STAFF = "staff"
    GUEST = "guest"

class DirectionType(str, enum.Enum):
    ENTRY = "entry"          # Kirish (Ishga kelish)
    EXIT = "exit"            # Chiqish (Ishdan ketish)
    UNIVERSAL = "universal"  # Universal (Bitta terminal - Kirish, Tushlik, Chiqish)
    BREAK_OUT = "break_out"  # Tushlikka chiqish
    BREAK_IN = "break_in"    # Tushlikdan qaytish
    UNKNOWN = "unknown"

class DeviceStatus(str, enum.Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    ERROR = "error"

class DepartmentType(str, enum.Enum):
    DEPARTMENT = "department"  # Kafedra
    DIVISION = "division"      # Ma'muriy bo'lim (Rektorat, O'quv bo'limi, Dekanat, Buxgalteriya va h.k.)

# Smena / Ish vaqti modeli
class Shift(Base):
    __tablename__ = "shifts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False) # "Standart Xodimlar", "1-Smena Talabalar", "Kechki Smena"
    start_time = Column(String(10), nullable=False) # "08:30"
    end_time = Column(String(10), nullable=False) # "17:30"
    lunch_start = Column(String(10), nullable=True, default="12:00") # "12:00"
    lunch_end = Column(String(10), nullable=True, default="13:00") # "13:00"
    late_tolerance_minutes = Column(Integer, default=15) # Kechikish chegarasi (daqiqa)
    early_leave_tolerance_minutes = Column(Integer, default=15) # Barvaqt ketish chegarasi (daqiqa)
    color = Column(String(20), default="#0084ff")
    created_at = Column(DateTime, default=datetime.utcnow)

# Haftalik Jadval (Har bir kun uchun qaysi smena biriktirilganligi)
class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False) # "5 kunlik ish grafigi (Xodimlar)", "6 kunlik o'qish (Talabalar)"
    description = Column(String(255), nullable=True)

    # 7 kunlik smena IDlari (None bo'lsa -> Dam olish kuni)
    monday_shift_id = Column(Integer, ForeignKey("shifts.id", ondelete="SET NULL"), nullable=True)
    tuesday_shift_id = Column(Integer, ForeignKey("shifts.id", ondelete="SET NULL"), nullable=True)
    wednesday_shift_id = Column(Integer, ForeignKey("shifts.id", ondelete="SET NULL"), nullable=True)
    thursday_shift_id = Column(Integer, ForeignKey("shifts.id", ondelete="SET NULL"), nullable=True)
    friday_shift_id = Column(Integer, ForeignKey("shifts.id", ondelete="SET NULL"), nullable=True)
    saturday_shift_id = Column(Integer, ForeignKey("shifts.id", ondelete="SET NULL"), nullable=True)
    sunday_shift_id = Column(Integer, ForeignKey("shifts.id", ondelete="SET NULL"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Day-by-day shift relationships
    monday_shift = relationship("Shift", foreign_keys=[monday_shift_id])
    tuesday_shift = relationship("Shift", foreign_keys=[tuesday_shift_id])
    wednesday_shift = relationship("Shift", foreign_keys=[wednesday_shift_id])
    thursday_shift = relationship("Shift", foreign_keys=[thursday_shift_id])
    friday_shift = relationship("Shift", foreign_keys=[friday_shift_id])
    saturday_shift = relationship("Shift", foreign_keys=[saturday_shift_id])
    sunday_shift = relationship("Shift", foreign_keys=[sunday_shift_id])

# Fakultet
class Faculty(Base):
    __tablename__ = "faculties"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False, unique=True)
    code = Column(String(50), nullable=True)
    dean_name = Column(String(150), nullable=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    departments = relationship("Department", back_populates="faculty")
    groups = relationship("Group", back_populates="faculty")

# Kafedra yoki Bo'lim
class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False, unique=True)
    code = Column(String(50), nullable=True)
    type = Column(Enum(DepartmentType), default=DepartmentType.DEPARTMENT)
    faculty_id = Column(Integer, ForeignKey("faculties.id"), nullable=True)
    
    # Kafedra mudiri yoki Bo'lim boshlig'i
    head_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    head_title = Column(String(100), nullable=True)
    
    # Biriktirilgan ish grafigi
    schedule_id = Column(Integer, ForeignKey("schedules.id", ondelete="SET NULL"), nullable=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    faculty = relationship("Faculty", back_populates="departments")
    groups = relationship("Group", back_populates="department")
    users = relationship("User", foreign_keys="User.department_id", back_populates="department")
    head = relationship("User", foreign_keys=[head_id], post_update=True)
    schedule = relationship("Schedule", foreign_keys=[schedule_id])

# Guruh
class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    direction_name = Column(String(200), nullable=True)
    course = Column(Integer, default=1)
    faculty_id = Column(Integer, ForeignKey("faculties.id"), nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    tutor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Guruhga biriktirilgan dars / smena grafigi
    schedule_id = Column(Integer, ForeignKey("schedules.id", ondelete="SET NULL"), nullable=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    faculty = relationship("Faculty", back_populates="groups")
    department = relationship("Department", back_populates="groups")
    tutor = relationship("User", foreign_keys=[tutor_id], back_populates="tutored_groups")
    students = relationship("User", foreign_keys="User.group_id", back_populates="group")
    schedule = relationship("Schedule", foreign_keys=[schedule_id])

class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    ip_address = Column(String(50), nullable=False, unique=True)
    port = Column(Integer, default=80)
    username = Column(String(50), default="admin")
    password = Column(String(100), nullable=False)
    direction = Column(Enum(DirectionType), default=DirectionType.ENTRY)
    universal_mode = Column(String(50), default="smart_auto") # "screen_status" yoki "smart_auto"
    universal_options = Column(String(200), default="check_in,break_out,break_in,check_out")
    lunch_start = Column(String(10), default="12:00")
    lunch_end = Column(String(10), default="14:00")
    door_no = Column(Integer, default=1)
    location = Column(String(200), nullable=True)
    status = Column(Enum(DeviceStatus), default=DeviceStatus.OFFLINE)
    serial_number = Column(String(100), nullable=True)
    model = Column(String(100), nullable=True)
    firmware_version = Column(String(100), nullable=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True)
    is_active = Column(Boolean, default=True)
    last_seen = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    access_logs = relationship("AccessLog", back_populates="device")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    employee_no = Column(String(50), unique=True, index=True, nullable=False)
    full_name = Column(String(150), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.STUDENT)
    position = Column(String(100), nullable=True)
    phone_number = Column(String(30), nullable=True)
    card_number = Column(String(50), nullable=True)
    photo_path = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Xodim yoki talaba tegishli bo'lim/kafedra
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    department = relationship("Department", foreign_keys=[department_id], back_populates="users")

    # Talaba tegishli bo'lgan guruh
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=True)
    group = relationship("Group", foreign_keys=[group_id], back_populates="students")
    
    group_name = Column(String(50), nullable=True)

    # Agar xodim Tyutor bo'lsa, u rahbarlik qiladigan guruhlar
    tutored_groups = relationship("Group", foreign_keys="Group.tutor_id", back_populates="tutor")

    # Shaxsiy biriktirilgan jadval (agar bo'lim yoki guruh jadvalidan farq qilsa)
    schedule_id = Column(Integer, ForeignKey("schedules.id", ondelete="SET NULL"), nullable=True)
    schedule = relationship("Schedule", foreign_keys=[schedule_id])
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    access_logs = relationship("AccessLog", back_populates="user")

class AccessLog(Base):
    __tablename__ = "access_logs"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="SET NULL"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    employee_no = Column(String(50), nullable=True)
    user_name = Column(String(150), nullable=True)
    card_number = Column(String(50), nullable=True)
    direction = Column(Enum(DirectionType), default=DirectionType.ENTRY)
    event_time = Column(DateTime, default=datetime.utcnow, index=True)
    event_type = Column(String(50), default="Face Match")
    status = Column(String(50), default="Success")
    snapshot_url = Column(String(255), nullable=True)
    raw_event = Column(Text, nullable=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True)

    device = relationship("Device", back_populates="access_logs")
    user = relationship("User", back_populates="access_logs")

# Tashkilot / Universitet / Filial modeli
class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False, unique=True) # Masalan: "Urganch Davlat Universiteti"
    code = Column(String(50), nullable=True)
    address = Column(String(200), nullable=True)
    org_type = Column(String(50), default="university") # "university" (Ta'lim / Maktab) yoki "company" (Idora / Tashkilot)
    admin_username = Column(String(100), default="admin")
    admin_password = Column(String(100), default="admin123")
    modules_enabled = Column(String(255), default="attendance,students,staff,structure,schedules")
    logo_url = Column(String(255), nullable=True)
    license_key = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class TelegramUser(Base):
    __tablename__ = "telegram_users"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(String(50), unique=True, index=True, nullable=False)
    username = Column(String(100), nullable=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    
    # Rol: "superadmin", "admin", "otdel_kadr", "tutor", "dekan", "pending"
    role = Column(String(50), default="pending")
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True)
    
    # Agar rol Tyutor bo'lsa, qaysi guruh unga biriktirilgan
    assigned_group_id = Column(Integer, ForeignKey("groups.id", ondelete="SET NULL"), nullable=True)
    
    # Agar rol Dekan bo'lsa, qaysi fakultet unga biriktirilgan
    assigned_faculty_id = Column(Integer, ForeignKey("faculties.id", ondelete="SET NULL"), nullable=True)

    is_active = Column(Boolean, default=True)
    notifications_enabled = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    organization = relationship("Organization")
    assigned_group = relationship("Group")
    assigned_faculty = relationship("Faculty")

# Tizim Foydalanuvchilari (Desktop, Android APK va Bot uchun login/parol, rollar va ruxsatlar)
class SystemAccount(Base):
    __tablename__ = "system_accounts"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(150), nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    password = Column(String(100), nullable=False)
    role = Column(String(50), default="otdel_kadr") # otdel_kadr, tutor, dekan, admin, operator
    
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True)
    assigned_group_id = Column(Integer, ForeignKey("groups.id", ondelete="SET NULL"), nullable=True)
    assigned_faculty_id = Column(Integer, ForeignKey("faculties.id", ondelete="SET NULL"), nullable=True)
    
    # Ruxsat berilgan dasturlar: "desktop,android,bot"
    allowed_apps = Column(String(200), default="desktop,android,bot")
    # Ruxsat berilgan modullar: "dashboard,attendance,staff,students,structure,settings"
    allowed_modules = Column(String(255), default="attendance,staff")
    
    telegram_chat_id = Column(String(50), nullable=True)
    phone_number = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    organization = relationship("Organization")
    assigned_group = relationship("Group")
    assigned_faculty = relationship("Faculty")


