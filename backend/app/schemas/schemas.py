from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.models.models import UserRole, DirectionType, DeviceStatus

# Device Schemas
class DeviceBase(BaseModel):
    name: str
    ip_address: str
    port: int = 80
    username: str = "admin"
    direction: DirectionType = DirectionType.ENTRY
    universal_mode: Optional[str] = "smart_auto"  # "screen_status" yoki "smart_auto"
    universal_options: Optional[str] = "check_in,break_out,break_in,check_out"
    lunch_start: Optional[str] = "12:00"
    lunch_end: Optional[str] = "14:00"
    door_no: int = 1
    location: Optional[str] = None
    is_active: bool = True
    organization_id: Optional[int] = None

class DeviceCreate(DeviceBase):
    password: str

class DeviceUpdate(BaseModel):
    name: Optional[str] = None
    ip_address: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    direction: Optional[DirectionType] = None
    universal_mode: Optional[str] = None
    universal_options: Optional[str] = None
    lunch_start: Optional[str] = None
    lunch_end: Optional[str] = None
    door_no: Optional[int] = None
    location: Optional[str] = None
    is_active: Optional[bool] = None

class DeviceOut(DeviceBase):
    id: int
    status: DeviceStatus
    serial_number: Optional[str] = None
    model: Optional[str] = None
    firmware_version: Optional[str] = None
    last_seen: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

# Faculty Schemas
class FacultyBase(BaseModel):
    name: str
    code: Optional[str] = None

class FacultyCreate(FacultyBase):
    pass

class FacultyOut(FacultyBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Department Schemas
class DepartmentBase(BaseModel):
    name: str
    code: Optional[str] = None
    type: str = "department" # "department" (kafedra) yoki "division" (bo'lim)
    faculty_id: Optional[int] = None
    head_id: Optional[int] = None # Kafedra mudiri yoki Bo'lim boshlig'i
    head_title: Optional[str] = None

class DepartmentCreate(DepartmentBase):
    pass

class DepartmentOut(DepartmentBase):
    id: int
    faculty_name: Optional[str] = None
    head_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# Group Schemas
class GroupBase(BaseModel):
    name: str
    direction_name: Optional[str] = None # Ta'lim yo'nalishi
    course: int = 1
    faculty_id: Optional[int] = None
    department_id: Optional[int] = None
    tutor_id: Optional[int] = None # Tyutor

class GroupCreate(GroupBase):
    pass

class GroupUpdate(BaseModel):
    name: Optional[str] = None
    direction_name: Optional[str] = None
    course: Optional[int] = None
    faculty_id: Optional[int] = None
    department_id: Optional[int] = None
    tutor_id: Optional[int] = None

class GroupOut(GroupBase):
    id: int
    faculty_name: Optional[str] = None
    department_name: Optional[str] = None
    tutor_name: Optional[str] = None
    student_count: Optional[int] = 0
    created_at: datetime

    class Config:
        from_attributes = True

# User Schemas
class UserBase(BaseModel):
    employee_no: str
    full_name: str
    role: UserRole = UserRole.STUDENT
    position: Optional[str] = None # "Kafedra mudiri", "Dotsent", "Tyutor" va h.k.
    phone_number: Optional[str] = None
    card_number: Optional[str] = None
    group_id: Optional[int] = None
    group_name: Optional[str] = None
    department_id: Optional[int] = None
    is_active: bool = True

class UserCreate(UserBase):
    pass

class UserUpdate(BaseModel):
    employee_no: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    position: Optional[str] = None
    phone_number: Optional[str] = None
    card_number: Optional[str] = None
    group_id: Optional[int] = None
    group_name: Optional[str] = None
    department_id: Optional[int] = None
    photo_path: Optional[str] = None
    is_active: Optional[bool] = None

class UserOut(UserBase):
    id: int
    photo_path: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    department_name: Optional[str] = None
    direction_name: Optional[str] = None # Talabaning ta'lim yo'nalishi
    tutor_name: Optional[str] = None # Talaba guruhining tyutori

    class Config:
        from_attributes = True

# AccessLog Schemas
class AccessLogOut(BaseModel):
    id: int
    device_id: int
    user_id: Optional[int] = None
    employee_no: Optional[str] = None
    user_name: Optional[str] = None
    card_number: Optional[str] = None
    direction: DirectionType
    event_time: datetime
    event_type: str
    status: str
    snapshot_url: Optional[str] = None
    device_name: Optional[str] = None
    role: Optional[str] = None
    group_name: Optional[str] = None
    position: Optional[str] = None

    class Config:
        from_attributes = True

class DeviceTestResult(BaseModel):
    success: bool
    message: str
    device_info: Optional[dict] = None

class BatchSyncRequest(BaseModel):
    user_ids: List[int]
    device_ids: List[int]

# Shift Schemas
class ShiftBase(BaseModel):
    name: str
    start_time: str
    end_time: str
    lunch_start: Optional[str] = "12:00"
    lunch_end: Optional[str] = "13:00"
    late_tolerance_minutes: int = 15
    early_leave_tolerance_minutes: int = 15
    color: str = "#0084ff"

class ShiftCreate(ShiftBase):
    pass

class ShiftUpdate(BaseModel):
    name: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    lunch_start: Optional[str] = None
    lunch_end: Optional[str] = None
    late_tolerance_minutes: Optional[int] = None
    early_leave_tolerance_minutes: Optional[int] = None
    color: Optional[str] = None

class ShiftOut(ShiftBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Schedule Schemas
class ScheduleBase(BaseModel):
    name: str
    description: Optional[str] = None
    monday_shift_id: Optional[int] = None
    tuesday_shift_id: Optional[int] = None
    wednesday_shift_id: Optional[int] = None
    thursday_shift_id: Optional[int] = None
    friday_shift_id: Optional[int] = None
    saturday_shift_id: Optional[int] = None
    sunday_shift_id: Optional[int] = None

class ScheduleCreate(ScheduleBase):
    pass

class ScheduleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    monday_shift_id: Optional[int] = None
    tuesday_shift_id: Optional[int] = None
    wednesday_shift_id: Optional[int] = None
    thursday_shift_id: Optional[int] = None
    friday_shift_id: Optional[int] = None
    saturday_shift_id: Optional[int] = None
    sunday_shift_id: Optional[int] = None

class ScheduleOut(ScheduleBase):
    id: int
    created_at: datetime
    monday_shift: Optional[ShiftOut] = None
    tuesday_shift: Optional[ShiftOut] = None
    wednesday_shift: Optional[ShiftOut] = None
    thursday_shift: Optional[ShiftOut] = None
    friday_shift: Optional[ShiftOut] = None
    saturday_shift: Optional[ShiftOut] = None
    sunday_shift: Optional[ShiftOut] = None

    class Config:
        from_attributes = True

class ScheduleAssignRequest(BaseModel):
    schedule_id: Optional[int] = None
    user_ids: Optional[List[int]] = None
    group_ids: Optional[List[int]] = None
    department_ids: Optional[List[int]] = None

