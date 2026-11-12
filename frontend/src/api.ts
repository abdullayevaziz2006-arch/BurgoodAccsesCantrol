import axios from 'axios';
import { 
  Device, User, AccessLog, DashboardStats, Faculty, Department, Group, 
  Shift, Schedule, ScheduleAssignmentsSummary, AuthResponse, BrandingInfo 
} from './types';

export const api = axios.create({
  baseURL: '/api/v1',
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('burgood_token');
  if (token) {
    config.headers['Authorization'] = `Bearer ${token}`;
  }
  const orgStr = localStorage.getItem('burgood_org');
  if (orgStr) {
    try {
      const org = JSON.parse(orgStr);
      if (org && org.id) {
        config.headers['X-Organization-Id'] = String(org.id);
      }
    } catch {}
  }
  const userStr = localStorage.getItem('burgood_user');
  if (userStr) {
    try {
      const user = JSON.parse(userStr);
      if (user && user.role) {
        config.headers['X-User-Role'] = String(user.role);
      }
      if (user && user.assigned_group_id) {
        config.headers['X-Assigned-Group-Id'] = String(user.assigned_group_id);
      }
      if (user && user.assigned_faculty_id) {
        config.headers['X-Assigned-Faculty-Id'] = String(user.assigned_faculty_id);
      }
    } catch {}
  }
  return config;
});

export const getStats = () => api.get<DashboardStats>('/attendance/stats').then(res => res.data);
export const getLogs = (params?: any) => api.get<AccessLog[]>('/attendance/logs', { params }).then(res => res.data);
export const exportLogsExcel = () => window.open('/api/v1/attendance/export-excel', '_blank');

export const getDevices = () => api.get<Device[]>('/devices/').then(res => res.data);
export const createDevice = (data: any) => api.post<Device>('/devices/', data).then(res => res.data);
export const updateDevice = (id: number, data: any) => api.put<Device>(`/devices/${id}`, data).then(res => res.data);
export const deleteDevice = (id: number) => api.delete(`/devices/${id}`).then(res => res.data);
export const testDevice = (id: number) => api.post<{ success: boolean; message: string; device_info?: any }>(`/devices/${id}/test`).then(res => res.data);
export const openDoorRemote = (id: number) => api.post<{ success: boolean; message: string }>(`/devices/${id}/open-door`).then(res => res.data);
export const captureFaceFromDevice = (deviceId: number) => 
  api.post<{ success: boolean; image_data_url: string; device_id: number; device_name: string; size_bytes: number }>(`/devices/${deviceId}/capture-face`).then(res => res.data);
export const getDeviceCredentials = (deviceId: number) => 
  api.get<{ id: number; name: string; ip_address: string; port: number; username: string; password?: string }>(`/devices/${deviceId}/credentials`).then(res => res.data);
export const importFromTerminal = (deviceId: number) => 
  api.post<{ success: boolean; imported: number; updated: number; faces_imported: number; total: number; message: string }>(`/devices/${deviceId}/import-from-terminal`).then(res => res.data);
export const batchImportWithFaces = (data: { users: any[] }) =>
  api.post<{ success: boolean; created: number; updated: number; photos_linked: number; total: number; message: string }>(`/users/batch-import-with-faces`, data).then(res => res.data);

export const getUsers = (params?: any) => api.get<User[]>('/users/', { params }).then(res => res.data);
export const createUser = (data: any) => api.post<User>('/users/', data).then(res => res.data);
export const updateUser = (id: number, data: any) => api.put<User>(`/users/${id}`, data).then(res => res.data);
export const deleteUser = (id: number, syncDelete: boolean = true) => api.delete(`/users/${id}`, { params: { sync_delete: syncDelete } }).then(res => res.data);
export const uploadUserPhoto = (id: number, file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  return api.post<{ success: boolean; photo_path: string }>(`/users/${id}/upload-photo`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }).then(res => res.data);
};
export const uploadUserPhotoBase64 = (id: number, imageDataUrl: string) =>
  api.post<{ success: boolean; photo_path: string }>(`/users/${id}/upload-photo-base64`, { image_data_url: imageDataUrl }).then(res => res.data);

export const captureUserPhotoFromDevice = (userId: number, deviceId: number) =>
  api.post<{ success: boolean; photo_path: string; message: string }>(`/users/${userId}/capture-from-device/${deviceId}`).then(res => res.data);

export const syncUserToDevice = (userId: number, deviceId: number) => 
  api.post<{ success: boolean; user_sync: string; face_sync: string }>(`/users/${userId}/sync-to-device/${deviceId}`).then(res => res.data);
export const syncUserToAll = (userId: number) => 
  api.post<{ results: any[] }>(`/users/${userId}/sync-to-all`).then(res => res.data);
export const batchSyncUsersToDevices = (userIds: number[], deviceIds: number[]) =>
  api.post<{
    success: boolean;
    total_users: number;
    total_devices: number;
    total_faces_uploaded?: number;
    total_failures?: number;
    details: { 
      device_id: number; 
      device_name: string; 
      success_count: number; 
      fail_count: number;
      faces_uploaded?: number;
      errors?: string[];
    }[];
  }>('/users/batch-sync-to-devices', { user_ids: userIds, device_ids: deviceIds }).then(res => res.data);

// University Academic Structure API
export const getFaculties = () => api.get<Faculty[]>('/structure/faculties').then(res => res.data);
export const createFaculty = (data: any) => api.post<Faculty>('/structure/faculties', data).then(res => res.data);
export const deleteFaculty = (id: number) => api.delete(`/structure/faculties/${id}`).then(res => res.data);

export const getDepartments = () => api.get<Department[]>('/structure/departments').then(res => res.data);
export const createDepartment = (data: any) => api.post<Department>('/structure/departments', data).then(res => res.data);
export const deleteDepartment = (id: number) => api.delete(`/structure/departments/${id}`).then(res => res.data);

export const getGroups = () => api.get<Group[]>('/structure/groups').then(res => res.data);
export const createGroup = (data: any) => api.post<Group>('/structure/groups', data).then(res => res.data);
export const updateGroup = (id: number, data: any) => api.put<Group>(`/structure/groups/${id}`, data).then(res => res.data);
export const assignTutorToGroup = (groupId: number, tutorId: number | null) => 
  api.put<{ success: boolean; group_id: number; tutor_id: number | null; tutor_name: string | null }>(
    `/structure/groups/${groupId}/assign-tutor`, 
    null, 
    { params: { tutor_id: tutorId } }
  ).then(res => res.data);
export const deleteGroup = (id: number) => api.delete(`/structure/groups/${id}`).then(res => res.data);

export const getPotentialTutors = () => api.get<User[]>('/structure/potential-tutors').then(res => res.data);

// Excel Import Helpers
const uploadExcelHelper = (url: string, file: File, params?: any) => {
  const formData = new FormData();
  formData.append('file', file);
  return api.post<{ success: boolean; created: number; skipped: number }>(url, formData, {
    params,
    headers: { 'Content-Type': 'multipart/form-data' }
  }).then(res => res.data);
};

export const importFacultiesExcel = (file: File) => uploadExcelHelper('/structure/faculties/import-excel', file);
export const importDepartmentsExcel = (file: File, type: string = 'department') => uploadExcelHelper('/structure/departments/import-excel', file, { type });
export const importGroupsExcel = (file: File) => uploadExcelHelper('/structure/groups/import-excel', file);

export const importStudentsExcel = (file: File, zipFile?: File | null) => {
  const formData = new FormData();
  formData.append('file', file);
  if (zipFile) {
    formData.append('zip_file', zipFile);
  }
  return api.post<{ success: boolean; created: number; skipped: number; photos_linked?: number }>('/users/import-students-excel', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }).then(res => res.data);
};

export const importStaffExcel = (file: File, zipFile?: File | null) => {
  const formData = new FormData();
  formData.append('file', file);
  if (zipFile) {
    formData.append('zip_file', zipFile);
  }
  return api.post<{ success: boolean; created: number; skipped: number; photos_linked?: number }>('/users/import-staff-excel', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }).then(res => res.data);
};

// Excel Template Downloads
export const downloadStudentsTemplate = () => window.open('/api/v1/users/template-students-excel', '_blank');
export const downloadStaffTemplate = () => window.open('/api/v1/users/template-staff-excel', '_blank');
export const downloadFacultiesTemplate = () => window.open('/api/v1/structure/faculties/template', '_blank');
export const downloadDepartmentsTemplate = () => window.open('/api/v1/structure/departments/template', '_blank');
export const downloadDivisionsTemplate = () => window.open('/api/v1/structure/divisions/template', '_blank');
export const downloadGroupsTemplate = () => window.open('/api/v1/structure/groups/template', '_blank');

// Shifts & Schedules APIs
export const getShifts = () => api.get<Shift[]>('/schedules/shifts').then(res => res.data);
export const createShift = (data: Partial<Shift>) => api.post<Shift>('/schedules/shifts', data).then(res => res.data);
export const updateShift = (id: number, data: Partial<Shift>) => api.put<Shift>(`/schedules/shifts/${id}`, data).then(res => res.data);
export const deleteShift = (id: number) => api.delete(`/schedules/shifts/${id}`).then(res => res.data);

export const getSchedules = () => api.get<Schedule[]>('/schedules').then(res => res.data);
export const createSchedule = (data: Partial<Schedule>) => api.post<Schedule>('/schedules', data).then(res => res.data);
export const updateSchedule = (id: number, data: Partial<Schedule>) => api.put<Schedule>(`/schedules/${id}`, data).then(res => res.data);
export const deleteSchedule = (id: number) => api.delete(`/schedules/${id}`).then(res => res.data);

export const assignSchedule = (data: { schedule_id?: number | null; user_ids?: number[]; group_ids?: number[]; department_ids?: number[] }) => 
  api.post('/schedules/assign', data).then(res => res.data);

export const getScheduleAssignments = () => api.get<ScheduleAssignmentsSummary>('/schedules/assignments').then(res => res.data);

// Auth & Branding APIs
export const loginUser = (username: string, password: string) =>
  api.post<AuthResponse>('/auth/login', { username, password, app_type: 'desktop' }).then(res => res.data);

export const getBranding = () =>
  api.get<BrandingInfo>('/auth/branding').then(res => res.data);

export const getMe = () =>
  api.get<{ success: boolean; user: any; organization?: any }>('/auth/me').then(res => res.data);

export const exportTabelExcel = (year?: number, month?: number) => {
  const params = new URLSearchParams();
  if (year) params.append('year', year.toString());
  if (month) params.append('month', month.toString());
  window.open(`/api/v1/attendance/export-tabel-excel?${params.toString()}`, '_blank');
};

export const getOrganizations = () => 
  api.get<any[]>('/master/organizations').then(res => res.data);

export const updateOrganization = (id: number, data: any) => 
  api.put(`/master/organizations/${id}`, data).then(res => res.data);

export const createOrganization = (data: any) => 
  api.post('/master/organizations', data).then(res => res.data);

export default api;


