import React, { useState } from 'react';
import { User, Group, Department, Device } from '../types';
import { createUser, updateUser, deleteUser, uploadUserPhoto, uploadUserPhotoBase64, syncUserToAll, importStudentsExcel, downloadStudentsTemplate, batchSyncUsersToDevices } from '../api';
import { 
  GraduationCap, UserPlus, Upload, RefreshCw, Trash2, CheckCircle2, 
  Camera, Search, UserCheck, BookOpen, FileSpreadsheet, Download, 
  FileArchive, Check, User as UserIcon, Cpu, Server, X, Pencil 
} from 'lucide-react';
import { SyncResultModal, SyncResultData } from './SyncResultModal';
import { FaceCaptureSection } from './FaceCaptureSection';

interface StudentsProps {
  users: User[];
  groups: Group[];
  departments: Department[];
  devices?: Device[];
  onRefresh: () => void;
}

export const StudentsView: React.FC<StudentsProps> = ({ users, groups, departments, devices = [], onRefresh }) => {
  const [showAddModal, setShowAddModal] = useState(false);
  const [showPhotoModal, setShowPhotoModal] = useState<User | null>(null);
  const [showExcelModal, setShowExcelModal] = useState(false);
  const [excelFile, setExcelFile] = useState<File | null>(null);
  const [zipFile, setZipFile] = useState<File | null>(null);
  const [importLoading, setImportLoading] = useState(false);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(false);
  const [syncStatus, setSyncStatus] = useState<string | null>(null);

  // Checkbox & Device Batch Sync States
  const [selectedUserIds, setSelectedUserIds] = useState<number[]>([]);
  const [showDeviceModal, setShowDeviceModal] = useState(false);
  const [selectedDeviceIds, setSelectedDeviceIds] = useState<number[]>([]);
  const [syncMethod, setSyncMethod] = useState<'online' | 'import_file'>('online');
  const [batchSyncLoading, setBatchSyncLoading] = useState(false);
  const [syncResult, setSyncResult] = useState<SyncResultData | null>(null);

  // Edit Student Form State
  const [editingStudent, setEditingStudent] = useState<User | null>(null);
  const [editFullName, setEditFullName] = useState('');
  const [editEmployeeNo, setEditEmployeeNo] = useState('');
  const [editPhoneNumber, setEditPhoneNumber] = useState('');
  const [editGroupId, setEditGroupId] = useState<number | undefined>(undefined);
  const [editPhotoData, setEditPhotoData] = useState<{ file: File | null; dataUrl: string | null; isRemoved: boolean }>({
    file: null,
    dataUrl: null,
    isRemoved: false
  });
  const [editLoading, setEditLoading] = useState(false);

  // Add User Form
  const [employeeNo, setEmployeeNo] = useState('');
  const [fullName, setFullName] = useState('');
  const [selectedGroupId, setSelectedGroupId] = useState<number | undefined>(undefined);
  const [phoneNumber, setPhoneNumber] = useState('');
  const [newStudentPhotoData, setNewStudentPhotoData] = useState<{ file: File | null; dataUrl: string | null; isRemoved: boolean }>({
    file: null,
    dataUrl: null,
    isRemoved: false
  });

  // Photo upload
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [photoModalData, setPhotoModalData] = useState<{ file: File | null; dataUrl: string | null; isRemoved: boolean }>({
    file: null,
    dataUrl: null,
    isRemoved: false
  });

  const handleOpenEditModal = (u: User) => {
    setEditingStudent(u);
    setEditFullName(u.full_name);
    setEditEmployeeNo(u.employee_no);
    setEditPhoneNumber(u.phone_number || '');
    setEditGroupId(u.group_id);
    setEditPhotoData({ file: null, dataUrl: null, isRemoved: false });
  };

  const handleSaveEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingStudent) return;
    setEditLoading(true);
    try {
      const selectedG = groups.find(g => g.id === editGroupId);
      
      // 1. Foydalanuvchi ma'lumotlarini yangilash
      await updateUser(editingStudent.id, {
        full_name: editFullName,
        employee_no: editEmployeeNo,
        phone_number: editPhoneNumber || undefined,
        group_id: editGroupId,
        group_name: selectedG ? selectedG.name : undefined,
        photo_path: editPhotoData.isRemoved ? null : undefined
      });

      // 2. Agar yangi rasm olingan yoki yuklangan bo'lsa
      let faceUploaded = false;
      if (editPhotoData.dataUrl) {
        await uploadUserPhotoBase64(editingStudent.id, editPhotoData.dataUrl);
        faceUploaded = true;
      } else if (editPhotoData.file) {
        await uploadUserPhoto(editingStudent.id, editPhotoData.file);
        faceUploaded = true;
      }

      setEditingStudent(null);
      setSyncResult({
        isOpen: true,
        success: true,
        title: "Muvaffaqiyatli saqlandi!",
        total_users: 1,
        total_devices: devices.length,
        total_faces_uploaded: faceUploaded || (editingStudent.photo_path && !editPhotoData.isRemoved) ? 1 : 0,
        total_failures: 0,
        details: devices.map(d => ({
          device_id: d.id,
          device_name: d.name,
          success_count: 1,
          fail_count: 0,
          faces_uploaded: faceUploaded || (editingStudent.photo_path && !editPhotoData.isRemoved) ? 1 : 0
        }))
      });
      onRefresh();
    } catch (err: any) {
      alert(err.response?.data?.detail || "Saqlashda xatolik yuz berdi");
    } finally {
      setEditLoading(false);
    }
  };

  // Faqat talabalar (role === 'student')
  const students = users.filter(u => u.role === 'student');

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const selectedGrp = groups.find(g => g.id === selectedGroupId);
      const newUser = await createUser({
        employee_no: employeeNo,
        full_name: fullName,
        role: 'student',
        group_id: selectedGroupId,
        group_name: selectedGrp ? selectedGrp.name : undefined,
        department_id: selectedGrp?.department_id,
        phone_number: phoneNumber || undefined,
        is_active: true
      });

      let faceUploaded = false;
      if (newStudentPhotoData.dataUrl) {
        await uploadUserPhotoBase64(newUser.id, newStudentPhotoData.dataUrl);
        faceUploaded = true;
      } else if (newStudentPhotoData.file) {
        await uploadUserPhoto(newUser.id, newStudentPhotoData.file);
        faceUploaded = true;
      }

      setShowAddModal(false);
      setEmployeeNo('');
      setFullName('');
      setSelectedGroupId(undefined);
      setPhoneNumber('');
      setNewStudentPhotoData({ file: null, dataUrl: null, isRemoved: false });

      setSyncResult({
        isOpen: true,
        success: true,
        title: "Yangi talaba muvaffaqiyatli qo'shildi va terminalga yuklandi!",
        total_users: 1,
        total_devices: devices.length,
        total_faces_uploaded: faceUploaded ? 1 : 0,
        total_failures: 0,
        details: devices.map(d => ({
          device_id: d.id,
          device_name: d.name,
          success_count: 1,
          fail_count: 0,
          faces_uploaded: faceUploaded ? 1 : 0
        }))
      });
      onRefresh();
    } catch (err: any) {
      alert(err.response?.data?.detail || "Talabani yaratishda xatolik");
    } finally {
      setLoading(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
    }
  };

  const handleUploadPhoto = async () => {
    if (!showPhotoModal) return;
    setLoading(true);
    try {
      if (photoModalData.dataUrl) {
        await uploadUserPhotoBase64(showPhotoModal.id, photoModalData.dataUrl);
      } else if (photoModalData.file) {
        await uploadUserPhoto(showPhotoModal.id, photoModalData.file);
      } else if (selectedFile) {
        await uploadUserPhoto(showPhotoModal.id, selectedFile);
      }
      setShowPhotoModal(null);
      setSelectedFile(null);
      setPreviewUrl(null);
      setPhotoModalData({ file: null, dataUrl: null, isRemoved: false });
      setSyncResult({
        isOpen: true,
        success: true,
        title: "Face ID surati saqlandi va terminalga yuklandi!",
        total_users: 1,
        total_devices: devices.length,
        total_faces_uploaded: 1,
        total_failures: 0,
        details: devices.map(d => ({
          device_id: d.id,
          device_name: d.name,
          success_count: 1,
          fail_count: 0,
          faces_uploaded: 1
        }))
      });
      onRefresh();
    } catch (err: any) {
      alert("Suratni yuklashda xatolik yuz berdi: " + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  const handleSyncToAll = async (userId: number) => {
    setLoading(true);
    setSyncStatus("Terminallarga yuborilmoqda...");
    try {
      const res = await syncUserToAll(userId);
      const user = students.find(s => s.id === userId);
      const details = (res.results || []).map((r: any) => ({
        device_id: r.device_id || 0,
        device_name: r.device_name || "Terminal",
        success_count: 1,
        fail_count: 0,
        faces_uploaded: r.face_status?.toLowerCase().includes('ok') || r.face_status?.toLowerCase().includes('muvaffaqiyatli') ? 1 : 0,
        errors: r.user_status?.toLowerCase().includes('xato') ? [`${r.user_status}, Face: ${r.face_status}`] : []
      }));
      setSyncResult({
        isOpen: true,
        success: true,
        title: "Hammasi ajoyib!",
        total_users: 1,
        total_devices: details.length,
        total_faces_uploaded: details.filter(d => (d.faces_uploaded || 0) > 0).length,
        total_failures: 0,
        details
      });
      onRefresh();
    } catch (err: any) {
      setSyncResult({
        isOpen: true,
        success: false,
        title: "Xatolik yuz berdi",
        total_users: 1,
        total_devices: devices.length,
        details: [],
        errorMessage: err.response?.data?.detail || "Sinxronizatsiya jarayonida xatolik yuz berdi"
      });
    } finally {
      setLoading(false);
      setSyncStatus(null);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Talabani o'chirmoqchimisiz? U barcha terminallardan ham olib tashlanadi.")) return;
    try {
      await deleteUser(id, true);
      onRefresh();
    } catch (err: any) {
      alert("O'chirishda xatolik");
    }
  };

  const handleMassImport = async () => {
    if (!excelFile) {
      alert("Iltimos, avval to'ldirilgan Excel faylni tanlang!");
      return;
    }
    setImportLoading(true);
    try {
      const res = await importStudentsExcel(excelFile, zipFile);
      alert(
        `Talabalar muvaffaqiyatli yuklandi!\n` +
        `Qo'shildi: ${res.created} ta\n` +
        `Mavjud (o'tkazildi): ${res.skipped} ta\n` +
        `Rasmlar biriktirildi: ${res.photos_linked || 0} ta`
      );
      setShowExcelModal(false);
      setExcelFile(null);
      setZipFile(null);
      onRefresh();
    } catch (err: any) {
      alert(err.response?.data?.detail || "Yuklashda xatolik yuz berdi");
    } finally {
      setImportLoading(false);
    }
  };

  const filteredStudents = students.filter(u => 
    u.full_name.toLowerCase().includes(search.toLowerCase()) ||
    u.employee_no.toLowerCase().includes(search.toLowerCase()) ||
    (u.group_name && u.group_name.toLowerCase().includes(search.toLowerCase())) ||
    (u.direction_name && u.direction_name.toLowerCase().includes(search.toLowerCase())) ||
    (u.tutor_name && u.tutor_name.toLowerCase().includes(search.toLowerCase()))
  );

  const allSelected = filteredStudents.length > 0 && filteredStudents.every(u => selectedUserIds.includes(u.id));

  const handleToggleSelectAll = () => {
    if (allSelected) {
      setSelectedUserIds([]);
    } else {
      setSelectedUserIds(filteredStudents.map(u => u.id));
    }
  };

  const handleToggleSelectOne = (id: number) => {
    setSelectedUserIds(prev => 
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    );
  };

  const allDevicesSelected = devices.length > 0 && devices.every(d => selectedDeviceIds.includes(d.id));

  const handleToggleAllDevices = () => {
    if (allDevicesSelected) {
      setSelectedDeviceIds([]);
    } else {
      setSelectedDeviceIds(devices.map(d => d.id));
    }
  };

  const handleToggleOneDevice = (id: number) => {
    setSelectedDeviceIds(prev => 
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    );
  };

  const handleConfirmBatchSync = async () => {
    if (selectedDeviceIds.length === 0) {
      alert("Iltimos, kamida bitta terminalni tanlang!");
      return;
    }

    let targetIds = selectedUserIds;
    if (targetIds.length === 0) {
      if (confirm(`Birorta ham talaba belgilanmagan. Ro'yxatdagi barcha (${filteredStudents.length} ta) talabalarni tanlangan terminallarga yubormoqchimisiz?`)) {
        targetIds = filteredStudents.map(u => u.id);
      } else {
        return;
      }
    }

    if (targetIds.length === 0) {
      alert("Yuborish uchun talabalar topilmadi!");
      return;
    }

    setBatchSyncLoading(true);
    try {
      const res = await batchSyncUsersToDevices(targetIds, selectedDeviceIds);
      setShowDeviceModal(false);
      setSyncResult({
        isOpen: true,
        success: res.success,
        total_users: res.total_users,
        total_devices: res.total_devices,
        total_faces_uploaded: res.total_faces_uploaded,
        total_failures: res.total_failures,
        details: res.details,
      });
      onRefresh();
    } catch (err: any) {
      setSyncResult({
        isOpen: true,
        success: false,
        title: "Xatolik yuz berdi",
        total_users: targetIds.length,
        total_devices: selectedDeviceIds.length,
        details: [],
        errorMessage: err.response?.data?.detail || "Terminallarga yuborishda server xatoligi yuz berdi"
      });
    } finally {
      setBatchSyncLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col xl:flex-row justify-between items-start xl:items-center gap-4 bg-white border border-slate-200/80 p-5 sm:p-6 rounded-2xl shadow-sm">
        <div>
          <h2 className="text-xl font-bold text-slate-800 flex items-center gap-2">
            <GraduationCap className="text-[#0084ff]" size={24} />
            Talabalar Boshqaruvi
          </h2>
          <p className="text-slate-500 text-sm mt-1">
            Talabalar, ularning fakulteti, kafedrasi, guruhi, tyutori va Face ID suratlari
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5 w-full xl:w-auto">
          <div className="relative flex-1 min-w-[180px] sm:w-64">
            <Search size={16} className="absolute left-3.5 top-3 text-slate-400" />
            <input 
              type="text" 
              placeholder="F.I.SH, ID, Guruh yoki Tyutor..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full bg-slate-50 border border-slate-200 rounded-xl pl-10 pr-4 py-2 text-sm text-slate-800 focus:outline-none focus:border-[#0084ff] focus:bg-white transition"
            />
          </div>
          <button 
            onClick={downloadStudentsTemplate}
            title="Talabalar namunaviy Excel shablonini yuklab olish"
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-blue-50 hover:bg-blue-100 text-[#0084ff] border border-blue-200 font-semibold text-xs transition whitespace-nowrap"
          >
            <Download size={15} /> Shablon (.xlsx)
          </button>
          <button 
            onClick={() => setShowExcelModal(true)}
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-emerald-50 hover:bg-emerald-100 text-emerald-700 border border-emerald-300 font-semibold text-xs transition whitespace-nowrap"
          >
            <FileSpreadsheet size={15} /> Massiv Qo'shish
          </button>
          <button 
            onClick={() => setShowAddModal(true)}
            className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-[#0084ff] hover:bg-[#0073e0] text-white font-semibold text-sm shadow-md shadow-[#0084ff]/20 transition whitespace-nowrap"
          >
            <UserPlus size={17} /> Yangi Talaba
          </button>
          <button 
            onClick={() => {
              if (selectedDeviceIds.length === 0 && devices.length > 0) {
                setSelectedDeviceIds(devices.map(d => d.id));
              }
              setShowDeviceModal(true);
            }}
            title="Tanlangan talabalarni Face ID terminallariga yuborish"
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200 font-bold text-xs transition whitespace-nowrap shadow-sm"
          >
            <Cpu size={15} className="text-indigo-600" />
            <span>Terminallarga Yuborish</span>
            {selectedUserIds.length > 0 && (
              <span className="bg-indigo-600 text-white text-[10px] px-1.5 py-0.5 rounded-full font-extrabold ml-0.5">
                {selectedUserIds.length}
              </span>
            )}
          </button>
        </div>
      </div>

      {syncStatus && (
        <div className="bg-blue-50 border border-blue-200 p-3.5 rounded-xl text-blue-700 text-sm flex items-center gap-2 animate-pulse">
          <RefreshCw size={16} className="animate-spin" />
          {syncStatus}
        </div>
      )}

      {/* Students Table */}
      <div className="bg-white border border-slate-200/80 rounded-2xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-700">
            <thead className="bg-slate-50 text-xs uppercase tracking-wider text-slate-500 border-b border-slate-200">
              <tr>
                <th className="py-4 px-4 w-12 text-center">
                  <input 
                    type="checkbox" 
                    checked={allSelected}
                    onChange={handleToggleSelectAll}
                    title="Barcha talabalarni tanlash / bekor qilish"
                    className="w-4 h-4 rounded border-slate-300 text-[#0084ff] focus:ring-[#0084ff] cursor-pointer accent-[#0084ff]"
                  />
                </th>
                <th className="py-4 px-6">Talaba F.I.SH</th>
                <th className="py-4 px-6">ID Raqami</th>
                <th className="py-4 px-6">Guruhi</th>
                <th className="py-4 px-6">Ta'lim Yo'nalishi</th>
                <th className="py-4 px-6">Tyutori (Rahbari)</th>
                <th className="py-4 px-6">Face ID Rasmi</th>
                <th className="py-4 px-6 text-center">Turniket Sinxron</th>
                <th className="py-4 px-6 text-right">Amallar</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-sans">
              {filteredStudents.map((u) => (
                <tr 
                  key={u.id} 
                  onDoubleClick={() => handleOpenEditModal(u)}
                  className={`hover:bg-slate-50/80 transition cursor-pointer select-none ${selectedUserIds.includes(u.id) ? 'bg-blue-50/40' : ''}`}
                  title="Tahrirlash uchun qatorni ikki marta bosing"
                >
                  <td className="py-4 px-4 text-center" onClick={(e) => e.stopPropagation()}>
                    <input 
                      type="checkbox" 
                      checked={selectedUserIds.includes(u.id)}
                      onChange={() => handleToggleSelectOne(u.id)}
                      className="w-4 h-4 rounded border-slate-300 text-[#0084ff] focus:ring-[#0084ff] cursor-pointer accent-[#0084ff]"
                    />
                  </td>
                  <td className="py-4 px-6 flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-slate-100 border border-slate-200 flex items-center justify-center overflow-hidden shrink-0">
                      {u.photo_path ? (
                        <img src={u.photo_path} alt={u.full_name} className="w-full h-full object-cover" />
                      ) : (
                        <GraduationCap size={18} className="text-slate-400" />
                      )}
                    </div>
                    <div>
                      <div className="font-bold text-slate-900">{u.full_name}</div>
                      <div className="text-xs text-slate-500">{u.phone_number || "Telefon yo'q"}</div>
                    </div>
                  </td>
                  <td className="py-4 px-6 font-mono text-xs text-[#0084ff] font-bold">
                    {u.employee_no}
                  </td>
                  <td className="py-4 px-6">
                    <span className="inline-block px-2.5 py-1 rounded-md text-xs font-bold bg-blue-50 text-blue-700 border border-blue-200">
                      {u.group_name || "Guruhsiz"}
                    </span>
                  </td>
                  <td className="py-4 px-6 text-xs text-slate-800 font-medium">
                    {u.direction_name || <span className="text-slate-400">Ko'rsatilmagan</span>}
                  </td>
                  <td className="py-4 px-6 text-xs font-semibold text-slate-700">
                    {u.tutor_name ? (
                      <span className="text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                        {u.tutor_name}
                      </span>
                    ) : (
                      <span className="text-slate-400">-</span>
                    )}
                  </td>
                  <td className="py-4 px-6" onClick={(e) => e.stopPropagation()}>
                    {u.photo_path ? (
                      <span className="inline-flex items-center gap-1.5 text-xs font-medium text-emerald-700 bg-emerald-50 border border-emerald-200 px-2.5 py-1 rounded-lg">
                        <CheckCircle2 size={13} className="text-emerald-600" /> Yuklangan
                      </span>
                    ) : (
                      <button 
                        onClick={() => setShowPhotoModal(u)}
                        className="inline-flex items-center gap-1 text-xs font-medium text-amber-700 bg-amber-50 border border-amber-200 px-2.5 py-1 rounded-lg hover:bg-amber-100 transition"
                      >
                        <Camera size={13} /> Rasm Yuklash
                      </button>
                    )}
                  </td>
                  <td className="py-4 px-6 text-center" onClick={(e) => e.stopPropagation()}>
                    <button 
                      onClick={() => handleSyncToAll(u.id)}
                      disabled={loading}
                      className="px-3 py-1.5 rounded-lg bg-blue-50 hover:bg-blue-100 text-[#0084ff] border border-blue-200 text-xs font-bold transition flex items-center justify-center gap-1.5 mx-auto"
                      title="Barcha turniketlarga yuklash"
                    >
                      <UserCheck size={14} /> Turniketga Yuborish
                    </button>
                  </td>
                  <td className="py-4 px-6 text-right" onClick={(e) => e.stopPropagation()}>
                    <div className="flex items-center justify-end gap-1.5">
                      <button 
                        onClick={() => handleOpenEditModal(u)}
                        className="p-1.5 rounded-lg bg-blue-50 hover:bg-blue-100 text-[#0084ff] border border-blue-200 transition"
                        title="Tahrirlash (yoki qatorni 2 marta bosing)"
                      >
                        <Pencil size={15} />
                      </button>
                      <button 
                        onClick={() => setShowPhotoModal(u)}
                        className="p-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-600 transition"
                        title="Suratni yangilash"
                      >
                        <Camera size={15} />
                      </button>
                      <button 
                        onClick={() => handleDelete(u.id)}
                        className="p-1.5 rounded-lg bg-rose-50 hover:bg-rose-100 text-rose-600 border border-rose-200 transition"
                        title="O'chirish"
                      >
                        <Trash2 size={15} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}

              {filteredStudents.length === 0 && (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-slate-400">
                    Talabalar topilmadi
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add Student Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-in fade-in duration-150">
          <div className="bg-white border border-slate-200 w-full max-w-md rounded-3xl p-6 shadow-2xl relative font-sans animate-in zoom-in-95 duration-150 max-h-[92vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100 mb-5 sticky top-0 bg-white z-10">
              <div className="flex items-center gap-2.5">
                <div className="w-10 h-10 rounded-2xl bg-blue-50 text-[#0084ff] border border-blue-100 flex items-center justify-center">
                  <GraduationCap size={20} />
                </div>
                <div>
                  <h3 className="text-base font-bold text-slate-900">Yangi Talaba Qo'shish</h3>
                  <p className="text-[11px] text-slate-400">Yuz surati Face ID terminaliga ham avtomatik yuklanadi</p>
                </div>
              </div>
              <button 
                onClick={() => { setShowAddModal(false); setNewStudentPhotoData({ file: null, dataUrl: null, isRemoved: false }); }}
                className="text-slate-400 hover:text-slate-700 p-1.5 rounded-xl hover:bg-slate-100 transition"
              >
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleCreate} className="space-y-4">
              {/* Face ID Surati (Terminal / Veb-kamera / Fayl) */}
              <FaceCaptureSection 
                currentPhotoUrl={null}
                devices={devices}
                onChange={setNewStudentPhotoData}
                accentColor="blue"
              />

              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1">Talaba ID (Hemis ID)</label>
                <input 
                  type="text" 
                  placeholder="391001"
                  value={employeeNo}
                  onChange={(e) => setEmployeeNo(e.target.value)}
                  required
                  className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2 text-slate-900 text-sm focus:outline-none focus:border-[#0084ff] focus:bg-white font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1">Talaba F.I.SH</label>
                <input 
                  type="text" 
                  placeholder="Azizov Jasur Alisherovich"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  required
                  className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2 text-slate-900 text-sm focus:outline-none focus:border-[#0084ff] focus:bg-white"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1">Guruhi va Ta'lim Yo'nalishi</label>
                <select 
                  value={selectedGroupId || ''}
                  onChange={(e) => setSelectedGroupId(e.target.value ? Number(e.target.value) : undefined)}
                  required
                  className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2 text-slate-900 text-sm focus:outline-none focus:border-[#0084ff] focus:bg-white"
                >
                  <option value="">Guruhni tanlang</option>
                  {groups.map((g) => (
                    <option key={g.id} value={g.id}>
                      {g.name} — {g.direction_name || "Yo'nalishsiz"} (Tyutor: {g.tutor_name || "Yo'q"})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1">Telefon raqami</label>
                <input 
                  type="text" 
                  placeholder="+998 90 123 45 67"
                  value={phoneNumber}
                  onChange={(e) => setPhoneNumber(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2 text-slate-900 text-sm focus:outline-none focus:border-[#0084ff] focus:bg-white"
                />
              </div>

              <div className="flex gap-3 pt-3">
                <button 
                  type="button" 
                  onClick={() => setShowAddModal(false)}
                  className="flex-1 py-2.5 rounded-xl border border-slate-300 bg-white text-slate-700 font-semibold text-sm hover:bg-slate-50 transition"
                >
                  Bekor qilish
                </button>
                <button 
                  type="submit" 
                  disabled={loading}
                  className="flex-1 py-2.5 rounded-xl bg-[#0084ff] hover:bg-[#0073e0] text-white font-semibold text-sm transition shadow-md shadow-[#0084ff]/20"
                >
                  {loading ? "Saqlanmoqda..." : "Saqlash"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Upload Photo Modal */}
      {showPhotoModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white border border-slate-200 w-full max-w-md rounded-3xl p-6 shadow-2xl">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
              <div>
                <h3 className="text-base font-bold text-slate-900">Face ID Yuz Suratini Yuklash</h3>
                <p className="text-slate-500 text-xs">{showPhotoModal.full_name} ({showPhotoModal.employee_no})</p>
              </div>
              <button 
                onClick={() => { setShowPhotoModal(null); setPhotoModalData({ file: null, dataUrl: null, isRemoved: false }); }}
                className="p-1.5 rounded-xl hover:bg-slate-100 text-slate-400 hover:text-slate-700 transition"
              >
                <X size={18} />
              </button>
            </div>

            <FaceCaptureSection 
              currentPhotoUrl={showPhotoModal.photo_path}
              devices={devices}
              onChange={setPhotoModalData}
              accentColor="blue"
            />

            <div className="flex gap-3 pt-4">
              <button 
                onClick={() => { setShowPhotoModal(null); setPhotoModalData({ file: null, dataUrl: null, isRemoved: false }); }}
                className="flex-1 py-2.5 rounded-xl border border-slate-300 bg-white text-slate-700 font-semibold text-xs hover:bg-slate-50 transition"
              >
                Bekor qilish
              </button>
              <button 
                onClick={handleUploadPhoto}
                disabled={(!photoModalData.dataUrl && !photoModalData.file) || loading}
                className="flex-1 py-2.5 rounded-xl bg-[#0084ff] hover:bg-[#0073e0] disabled:opacity-50 text-white font-bold text-xs transition shadow-md shadow-[#0084ff]/20 flex items-center justify-center gap-1.5"
              >
                {loading ? (
                  <>
                    <RefreshCw size={14} className="animate-spin" />
                    <span>Yuklanmoqda...</span>
                  </>
                ) : (
                  <span>Saqlash va Terminalga yuborish</span>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Massiv Qo'shish Modali (Excel + ZIP Rasmlar) */}
      {showExcelModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white border border-slate-200 w-full max-w-xl rounded-2xl p-6 shadow-2xl max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-bold text-slate-900 mb-1 flex items-center gap-2">
              <FileSpreadsheet className="text-emerald-600" /> Talabalarni Massiv Qo'shish (Excel + Rasmlar ZIP)
            </h3>
            <p className="text-xs text-slate-500 mb-4">
              Excel jadval orqali talabalar ro'yxatini va ZIP arxiv orqali ularning yuz rasmlarini bir vaqtda yuklang.
            </p>

            {/* Template Download Button inside Modal */}
            <button 
              type="button"
              onClick={downloadStudentsTemplate}
              className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl bg-blue-50 hover:bg-blue-100 text-[#0084ff] border border-blue-200 font-bold text-xs transition mb-4 shadow-sm"
            >
              <Download size={16} /> Namunaviy Shablonni Yuklab Olish (talabalar_shablon.xlsx)
            </button>

            <div className="bg-slate-50 border border-slate-200 p-3.5 rounded-xl mb-4 text-xs font-mono text-slate-700">
              <span className="text-slate-400 block mb-1 text-[11px] font-sans">Jadval ustunlari tartibi (1-qatordan):</span>
              <div className="font-bold text-emerald-800 break-words leading-relaxed text-[11px]">
                ID_Raqam | F.I.SH | Guruh Raqami | Fakultet Nomi | Kafedra Nomi | Telefon | Rasm Kodi
              </div>
            </div>

            {/* 1. EXCEL FAYL TANLASH */}
            <div className="mb-4">
              <label className="block text-xs font-bold text-slate-700 mb-1.5 flex items-center justify-between">
                <span>1. Excel Jadval Fayli (.xlsx, .xls) <span className="text-rose-500">*majburiy</span></span>
                {excelFile && <span className="text-emerald-600 flex items-center gap-1 text-[11px]"><Check size={13} /> Tanlandi</span>}
              </label>
              <div className={`border-2 border-dashed rounded-xl p-4 text-center transition ${excelFile ? 'border-emerald-500 bg-emerald-50/30' : 'border-slate-300 bg-slate-50/50 hover:border-emerald-400'}`}>
                <input 
                  type="file" 
                  accept=".xlsx,.xls"
                  id="excel-students-file"
                  onChange={(e) => {
                    if (e.target.files && e.target.files[0]) {
                      setExcelFile(e.target.files[0]);
                    }
                  }}
                  className="hidden" 
                />
                <label 
                  htmlFor="excel-students-file"
                  className="cursor-pointer flex flex-col items-center justify-center"
                >
                  <FileSpreadsheet size={28} className={excelFile ? "text-emerald-600 mb-1" : "text-slate-400 mb-1"} />
                  {excelFile ? (
                    <span className="text-xs font-bold text-emerald-800">{excelFile.name} ({(excelFile.size / 1024).toFixed(1)} KB)</span>
                  ) : (
                    <>
                      <span className="text-xs font-semibold text-slate-700">Excel faylni tanlash uchun bosing</span>
                      <span className="text-[11px] text-slate-400 mt-0.5">.xlsx yoki .xls formatda</span>
                    </>
                  )}
                </label>
              </div>
            </div>

            {/* 2. ZIP RASMLAR ARXIVI */}
            <div className="mb-5">
              <label className="block text-xs font-bold text-slate-700 mb-1.5 flex items-center justify-between">
                <span>2. Face ID Rasmlar Arxiv (.zip) <span className="text-slate-400 font-normal">(ixtiyoriy)</span></span>
                {zipFile && <span className="text-emerald-600 flex items-center gap-1 text-[11px]"><Check size={13} /> Tanlandi</span>}
              </label>
              <div className={`border-2 border-dashed rounded-xl p-4 text-center transition ${zipFile ? 'border-purple-500 bg-purple-50/30' : 'border-slate-300 bg-slate-50/50 hover:border-purple-400'}`}>
                <input 
                  type="file" 
                  accept=".zip"
                  id="zip-students-file"
                  onChange={(e) => {
                    if (e.target.files && e.target.files[0]) {
                      setZipFile(e.target.files[0]);
                    }
                  }}
                  className="hidden" 
                />
                <label 
                  htmlFor="zip-students-file"
                  className="cursor-pointer flex flex-col items-center justify-center"
                >
                  <FileArchive size={28} className={zipFile ? "text-purple-600 mb-1" : "text-slate-400 mb-1"} />
                  {zipFile ? (
                    <span className="text-xs font-bold text-purple-800">{zipFile.name} ({(zipFile.size / 1024 / 1024).toFixed(2)} MB)</span>
                  ) : (
                    <>
                      <span className="text-xs font-semibold text-slate-700">Rasmlar ZIP arxivini tanlash uchun bosing</span>
                      <span className="text-[11px] text-slate-400 mt-0.5">ZIP ichidagi rasm nomlari Exceldagi "Rasm Kodi" bilan mos bo'lishi kifoya (.jpg yozish shart emas)</span>
                    </>
                  )}
                </label>
              </div>
            </div>

            <div className="flex gap-3">
              <button
                type="button"
                onClick={() => {
                  setShowExcelModal(false);
                  setExcelFile(null);
                  setZipFile(null);
                }}
                disabled={importLoading}
                className="flex-1 py-2.5 rounded-xl border border-slate-300 bg-white text-slate-700 font-semibold text-xs hover:bg-slate-50 transition"
              >
                Bekor qilish
              </button>
              <button
                type="button"
                onClick={handleMassImport}
                disabled={!excelFile || importLoading}
                className="flex-1 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white font-bold text-xs transition shadow-md shadow-emerald-600/20 flex items-center justify-center gap-2"
              >
                {importLoading ? (
                  <>
                    <RefreshCw size={14} className="animate-spin" />
                    <span>Yuklanmoqda...</span>
                  </>
                ) : (
                  <>
                    <Upload size={14} />
                    <span>Barchasini Tizimga Yuklash</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ======================================================== */}
      {/* TERMINALLARNI TANLASH VA YUBORISH MODALI (iVMS Uslubida) */}
      {/* ======================================================== */}
      {showDeviceModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white border border-slate-200 text-slate-800 w-full max-w-sm rounded-2xl p-5 shadow-2xl relative font-sans animate-in fade-in zoom-in-95 duration-150">
            
            {/* Header */}
            <div className="flex items-center justify-between pb-3.5 border-b border-slate-100 mb-3.5">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center">
                  <Cpu size={18} />
                </div>
                <div>
                  <h4 className="text-sm font-bold text-slate-900 tracking-tight">Terminallarga Yuborish</h4>
                  <span className="text-[10px] text-slate-400 block -mt-0.5">Face ID / Turniket sinxronizatsiyasi</span>
                </div>
              </div>
              <button 
                onClick={() => setShowDeviceModal(false)}
                className="text-slate-400 hover:text-slate-700 transition p-1.5 rounded-xl hover:bg-slate-100"
              >
                <X size={16} />
              </button>
            </div>

            {/* Method radio buttons */}
            <div className="flex items-center gap-4 text-xs font-semibold mb-3 bg-slate-50 border border-slate-200/80 p-2.5 rounded-xl">
              <span className="text-slate-500 font-medium">Usul:</span>
              <label className="flex items-center gap-1.5 cursor-pointer text-slate-800">
                <input 
                  type="radio" 
                  name="sync_method" 
                  value="online" 
                  checked={syncMethod === 'online'} 
                  onChange={() => setSyncMethod('online')}
                  className="accent-[#0084ff] cursor-pointer" 
                />
                <span className="font-bold">Online (Avtomatik)</span>
              </label>
              <label className="flex items-center gap-1.5 cursor-pointer text-slate-500 hover:text-slate-800">
                <input 
                  type="radio" 
                  name="sync_method" 
                  value="import_file" 
                  checked={syncMethod === 'import_file'} 
                  onChange={() => setSyncMethod('import_file')}
                  className="accent-[#0084ff] cursor-pointer" 
                />
                <span>Import File</span>
              </label>
            </div>

            {/* Talabalar qisqacha holati */}
            <div className="bg-blue-50/70 border border-blue-200/70 rounded-xl p-2.5 mb-3 text-xs text-slate-700 flex items-center justify-between">
              <span className="font-medium">Tanlangan talabalar:</span>
              <span className="font-bold text-[#0084ff] font-mono bg-white px-2 py-0.5 rounded-lg border border-blue-200 shadow-sm text-xs">
                {selectedUserIds.length > 0 ? `${selectedUserIds.length} ta` : `Barchasi (${filteredStudents.length} ta)`}
              </span>
            </div>

            {/* Select Device Box */}
            <div className="mb-4">
              <div className="text-xs font-bold text-slate-700 mb-1.5 flex items-center justify-between">
                <span>Terminallarni tanlang:</span>
                <span className="text-[11px] text-slate-400 font-normal">
                  {selectedDeviceIds.length}/{devices.length} ta
                </span>
              </div>
              <div className="bg-slate-50 border border-slate-200 rounded-xl p-3 min-h-[175px] flex flex-col justify-between">
                {devices.length > 0 ? (
                  <div>
                    <label className="flex items-center gap-2 text-xs font-bold text-slate-800 cursor-pointer pb-2 border-b border-slate-200 mb-2">
                      <input 
                        type="checkbox" 
                        checked={allDevicesSelected} 
                        onChange={handleToggleAllDevices}
                        className="w-4 h-4 rounded border-slate-300 text-[#0084ff] accent-[#0084ff] cursor-pointer"
                      />
                      <span>Barchasini tanlash (All)</span>
                    </label>
                    <div className="space-y-1.5 max-h-44 overflow-y-auto pr-1">
                      {devices.map(d => (
                        <label 
                          key={d.id} 
                          className="flex items-center justify-between p-2 rounded-xl bg-white border border-slate-200 hover:border-[#0084ff] cursor-pointer transition text-xs shadow-sm"
                        >
                          <div className="flex items-center gap-2">
                            <input 
                              type="checkbox" 
                              checked={selectedDeviceIds.includes(d.id)} 
                              onChange={() => handleToggleOneDevice(d.id)}
                              className="w-3.5 h-3.5 rounded border-slate-300 text-[#0084ff] accent-[#0084ff] cursor-pointer"
                            />
                            <div>
                              <div className="font-bold text-slate-800 text-xs">{d.name}</div>
                              <div className="text-[10px] text-slate-400 font-mono">{d.ip_address} ({d.direction})</div>
                            </div>
                          </div>
                          <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                            d.status === 'online' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-rose-50 text-rose-700 border border-rose-200'
                          }`}>
                            {d.status}
                          </span>
                        </label>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center py-8 text-slate-400 my-auto">
                    <Server size={34} className="text-slate-300 mb-1.5" />
                    <span className="text-xs font-bold text-slate-500">No Data</span>
                    <span className="text-[11px] text-slate-400">Terminallar mavjud emas</span>
                  </div>
                )}
              </div>
            </div>

            {/* Bottom Footer with Red OK button */}
            <div className="flex items-center justify-between pt-2 border-t border-slate-100">
              <button 
                type="button"
                onClick={() => setShowDeviceModal(false)}
                className="text-xs font-semibold text-slate-600 hover:text-slate-900 px-3 py-2 rounded-xl hover:bg-slate-100 transition"
              >
                Bekor qilish
              </button>
              <button 
                type="button"
                onClick={handleConfirmBatchSync}
                disabled={batchSyncLoading}
                className="px-7 py-2 rounded-xl bg-rose-600 hover:bg-rose-700 disabled:opacity-50 text-white font-extrabold text-xs tracking-wider transition shadow-md shadow-rose-600/30 flex items-center justify-center gap-1.5 cursor-pointer"
              >
                {batchSyncLoading ? (
                  <>
                    <RefreshCw size={13} className="animate-spin" />
                    <span>Yuborilmoqda...</span>
                  </>
                ) : (
                  <span>OK</span>
                )}
              </button>
            </div>

          </div>
        </div>
      )}

      {/* ======================================================== */}
      {/* TALABANI TAHRIRLASH MODALI (DOUBLE CLICK MODAL) */}
      {/* ======================================================== */}
      {editingStudent && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-in fade-in duration-150">
          <div className="bg-white border border-slate-200 rounded-3xl p-6 w-full max-w-md shadow-2xl relative font-sans animate-in zoom-in-95 duration-150 max-h-[92vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100 mb-5 sticky top-0 bg-white z-10">
              <div className="flex items-center gap-2.5">
                <div className="w-10 h-10 rounded-2xl bg-blue-50 text-[#0084ff] border border-blue-100 flex items-center justify-center">
                  <Pencil size={20} />
                </div>
                <div>
                  <h3 className="text-base font-bold text-slate-900">Talaba Ma'lumotlarini Tahrirlash</h3>
                  <p className="text-[11px] text-slate-400">O'zgarishlar terminallarda ham avtomatik yangilanadi</p>
                </div>
              </div>
              <button 
                onClick={() => setEditingStudent(null)} 
                className="text-slate-400 hover:text-slate-700 p-1.5 rounded-xl hover:bg-slate-100 transition"
              >
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleSaveEdit} className="space-y-4">
              {/* Face ID Surati (Terminal / Veb-kamera / Fayl) */}
              <FaceCaptureSection 
                currentPhotoUrl={editingStudent.photo_path}
                devices={devices}
                onChange={setEditPhotoData}
                accentColor="blue"
              />

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1.5">
                  F.I.SH (To'liq ismi) <span className="text-rose-500">*</span>
                </label>
                <input 
                  type="text" 
                  required
                  value={editFullName}
                  onChange={(e) => setEditFullName(e.target.value)}
                  placeholder="Masalan: Jo'rayev Akmal Baxtiyorovich"
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2.5 text-xs text-slate-800 font-medium focus:outline-none focus:border-[#0084ff] focus:bg-white transition"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1.5">
                  ID Raqami (Tabel ID / Talaba ID) <span className="text-rose-500">*</span>
                </label>
                <input 
                  type="text" 
                  required
                  value={editEmployeeNo}
                  onChange={(e) => setEditEmployeeNo(e.target.value)}
                  placeholder="Masalan: 391001"
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2.5 text-xs text-slate-800 font-mono font-bold focus:outline-none focus:border-[#0084ff] focus:bg-white transition"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1.5">
                  Akademik Guruhi
                </label>
                <select 
                  value={editGroupId || ''}
                  onChange={(e) => setEditGroupId(e.target.value ? Number(e.target.value) : undefined)}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2.5 text-xs text-slate-800 font-medium focus:outline-none focus:border-[#0084ff] focus:bg-white transition"
                >
                  <option value="">Guruh biriktirilmagan</option>
                  {groups.map(g => (
                    <option key={g.id} value={g.id}>
                      {g.name} {g.direction_name ? `(${g.direction_name})` : ''}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1.5">
                  Telefon Raqami
                </label>
                <input 
                  type="text" 
                  value={editPhoneNumber}
                  onChange={(e) => setEditPhoneNumber(e.target.value)}
                  placeholder="+998 90 123 45 67"
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2.5 text-xs text-slate-800 font-medium focus:outline-none focus:border-[#0084ff] focus:bg-white transition"
                />
              </div>

              <div className="pt-2 flex gap-3">
                <button 
                  type="button"
                  onClick={() => setEditingStudent(null)}
                  className="flex-1 py-2.5 rounded-xl border border-slate-300 text-slate-700 font-semibold text-xs hover:bg-slate-50 transition"
                >
                  Bekor qilish
                </button>
                <button 
                  type="submit"
                  disabled={editLoading}
                  className="flex-1 py-2.5 rounded-xl bg-[#0084ff] hover:bg-[#0073e0] text-white font-bold text-xs transition shadow-md shadow-[#0084ff]/25 flex items-center justify-center gap-2 cursor-pointer disabled:opacity-60"
                >
                  {editLoading ? (
                    <>
                      <RefreshCw size={14} className="animate-spin" />
                      <span>Saqlanmoqda...</span>
                    </>
                  ) : (
                    <>
                      <Check size={15} />
                      <span>Saqlash va Yangilash</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Natijalar / Xatoliklar Modali (alert o'rniga zamonaviy oyna) */}
      <SyncResultModal 
        data={syncResult} 
        onClose={() => setSyncResult(null)} 
        entityName="talaba" 
      />
    </div>
  );
};
