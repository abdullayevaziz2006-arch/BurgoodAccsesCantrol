export interface Device {
  id: number;
  name: string;
  ip_address: string;
  port: number;
  username: string;
  direction: 'entry' | 'exit' | 'universal';
  universal_mode?: 'screen_status' | 'smart_auto';
  universal_options?: string;
  lunch_start?: string;
  lunch_end?: string;
  door_no: number;
  location?: string;
  status: 'online' | 'offline' | 'error';
  serial_number?: string;
  model?: string;
  firmware_version?: string;
  last_seen?: string;
  is_active: boolean;
  created_at: string;
}

export interface Faculty {
  id: number;
  name: string;
  code?: string;
  created_at: string;
}

export interface Department {
  id: number;
  name: string;
  code?: string;
  type: 'department' | 'division';
  faculty_id?: number;
  faculty_name?: string;
  head_id?: number;
  head_name?: string;
  head_title?: string;
  created_at: string;
}

export interface Group {
  id: number;
  name: string;
  direction_name?: string; // Ta'lim yo'nalishi
  course: number;
  faculty_id?: number;
  department_id?: number;
  tutor_id?: number;
  faculty_name?: string;
  department_name?: string;
  tutor_name?: string;
  student_count?: number;
  created_at: string;
}

export interface User {
  id: number;
  employee_no: string;
  full_name: string;
  role: 'student' | 'teacher' | 'staff' | 'guest';
  position?: string; // "Kafedra mudiri", "Dotsent", "Tyutor", "Dekan"
  phone_number?: string;
  card_number?: string;
  group_id?: number;
  group_name?: string;
  direction_name?: string; // Ta'lim yo'nalishi
  tutor_name?: string; // Guruh tyutori
  department_id?: number;
  department_name?: string;
  photo_path?: string;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

export interface AccessLog {
  id: number;
  device_id: number;
  device_name?: string;
  user_id?: number;
  employee_no?: string;
  user_name?: string;
  card_number?: string;
  direction: 'entry' | 'exit' | 'universal' | 'break_out' | 'break_in' | 'unknown';
  event_time: string;
  event_type: string;
  status: string;
  snapshot_url?: string;
  photo_path?: string;
  role?: string;
  group_name?: string;
  position?: string;
}

export interface DashboardStats {
  total_users: number;
  total_devices: number;
  online_devices: number;
  today_entries: number;
  today_exits: number;
  unique_present: number;
}

export interface Shift {
  id: number;
  name: string;
  start_time: string;
  end_time: string;
  lunch_start?: string;
  lunch_end?: string;
  late_tolerance_minutes: number;
  early_leave_tolerance_minutes: number;
  color: string;
  created_at: string;
}

export interface Schedule {
  id: number;
  name: string;
  description?: string;
  monday_shift_id?: number | null;
  tuesday_shift_id?: number | null;
  wednesday_shift_id?: number | null;
  thursday_shift_id?: number | null;
  friday_shift_id?: number | null;
  saturday_shift_id?: number | null;
  sunday_shift_id?: number | null;
  monday_shift?: Shift | null;
  tuesday_shift?: Shift | null;
  wednesday_shift?: Shift | null;
  thursday_shift?: Shift | null;
  friday_shift?: Shift | null;
  saturday_shift?: Shift | null;
  sunday_shift?: Shift | null;
  created_at: string;
}

export interface ScheduleAssignmentsSummary {
  groups: Array<{
    id: number;
    name: string;
    direction_name?: string;
    schedule_id?: number | null;
    schedule_name: string;
  }>;
  staff: Array<{
    id: number;
    employee_no: string;
    full_name: string;
    role: string;
    position?: string;
    department_name?: string;
    schedule_id?: number | null;
    schedule_name: string;
  }>;
  departments: Array<{
    id: number;
    name: string;
    type: string;
    schedule_id?: number | null;
    schedule_name: string;
  }>;
}

export interface OrganizationInfo {
  id: number;
  name: string;
  code?: string;
  logo_url?: string;
  org_type?: 'university' | 'company' | 'office' | 'business' | string;
  modules: string[];
}

export interface UserInfo {
  id?: number;
  username: string;
  role: string;
  full_name: string;
  allowed_apps?: string[];
  allowed_modules?: string[];
  assigned_group_id?: number | null;
  assigned_faculty_id?: number | null;
}

export interface AuthResponse {
  success: boolean;
  token: string;
  organization?: OrganizationInfo;
  user: UserInfo;
}

export interface BrandingInfo {
  name: string;
  code?: string;
  logo_url?: string;
}

