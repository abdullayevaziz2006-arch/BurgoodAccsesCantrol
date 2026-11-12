import React, { useState } from 'react';
import { User, Device } from '../types';
import { createUser, deleteUser, uploadUserPhoto, syncUserToAll, syncUserToDevice } from '../api';
import { Users as UsersIcon, UserPlus, Upload, RefreshCw, Trash2, CheckCircle2, AlertCircle, Camera, Search, UserCheck } from 'lucide-react';

interface UsersProps {
  users: User[];
  devices: Device[];
  onRefresh: () => void;
}

export const UsersView: React.FC<UsersProps> = ({ users, devices, onRefresh }) => {
  const [showAddModal, setShowAddModal] = useState(false);
  const [showPhotoModal, setShowPhotoModal] = useState<User | null>(null);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(false);
  const [syncStatus, setSyncStatus] = useState<string | null>(null);

  // Add User Form
  const [employeeNo, setEmployeeNo] = useState('');
  const [fullName, setFullName] = useState('');
  const [role, setRole] = useState<'student' | 'teacher' | 'staff'>('student');
  const [groupName, setGroupName] = useState('');
  const [phoneNumber, setPhoneNumber] = useState('');

  // Photo upload
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await createUser({
        employee_no: employeeNo,
        full_name: fullName,
        role,
        group_name: groupName || undefined,
        phone_number: phoneNumber || undefined,
        is_active: true
      });
      setShowAddModal(false);
      setEmployeeNo('');
      setFullName('');
      setGroupName('');
      setPhoneNumber('');
      onRefresh();
    } catch (err: any) {
      alert(err.response?.data?.detail || "Foydalanuvchi yaratishda xatolik");
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
    if (!showPhotoModal || !selectedFile) return;
    setLoading(true);
    try {
      await uploadUserPhoto(showPhotoModal.id, selectedFile);
      alert("Surat saqlandi! Endi uni terminalga yuborishingiz mumkin.");
      setShowPhotoModal(null);
      setSelectedFile(null);
      setPreviewUrl(null);
      onRefresh();
    } catch (err: any) {
      alert("Suratni yuklashda xatolik yuz berdi");
    } finally {
      setLoading(false);
    }
  };

  const handleSyncToAll = async (userId: number) => {
    setLoading(true);
    setSyncStatus("Terminallarga yuborilmoqda...");
    try {
      const res = await syncUserToAll(userId);
      alert("Sinxronizatsiya yakunlandi!\n" + res.results.map((r: any) => `${r.device_name}: Foydalanuvchi: ${r.user_status}, Yuz: ${r.face_status}`).join('\n'));
    } catch (err: any) {
      alert("Sinxronizatsiya jarayonida xatolik yuz berdi");
    } finally {
      setLoading(false);
      setSyncStatus(null);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Foydalanuvchini o'chirmoqchimisiz? U terminallardan ham olib tashlanadi.")) return;
    try {
      await deleteUser(id, true);
      onRefresh();
    } catch (err: any) {
      alert("O'chirishda xatolik");
    }
  };

  const filteredUsers = users.filter(u => 
    u.full_name.toLowerCase().includes(search.toLowerCase()) ||
    u.employee_no.toLowerCase().includes(search.toLowerCase()) ||
    (u.group_name && u.group_name.toLowerCase().includes(search.toLowerCase()))
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-sm">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <UsersIcon className="text-indigo-400" />
            Talabalar va Xodimlar Bazasi
          </h2>
          <p className="text-slate-400 text-sm mt-1">
            Yuz suratlari (Face ID) va turniketlarga yuklash
          </p>
        </div>

        <div className="flex items-center gap-3 w-full md:w-auto">
          <div className="relative flex-1 md:w-64">
            <Search size={16} className="absolute left-3.5 top-3 text-slate-500" />
            <input 
              type="text" 
              placeholder="F.I.SH, ID yoki Guruh..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-10 pr-4 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
            />
          </div>
          <button 
            onClick={() => setShowAddModal(true)}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-sm shadow-lg shadow-indigo-600/30 transition whitespace-nowrap"
          >
            <UserPlus size={18} /> Yangi Qo'shish
          </button>
        </div>
      </div>

      {syncStatus && (
        <div className="bg-indigo-950/60 border border-indigo-700/50 p-3 rounded-xl text-indigo-300 text-sm flex items-center gap-2 animate-pulse">
          <RefreshCw size={16} className="animate-spin" />
          {syncStatus}
        </div>
      )}

      {/* Users Table */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="bg-slate-950/80 text-xs uppercase tracking-wider text-slate-400 border-b border-slate-800">
              <tr>
                <th className="py-4 px-6">Shaxs</th>
                <th className="py-4 px-6">ID Raqami</th>
                <th className="py-4 px-6">Roli / Guruh</th>
                <th className="py-4 px-6">Yuz Surati</th>
                <th className="py-4 px-6 text-center">Turniket Sinxron</th>
                <th className="py-4 px-6 text-right">Amallar</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {filteredUsers.map((u) => (
                <tr key={u.id} className="hover:bg-slate-800/40 transition">
                  <td className="py-4 px-6 flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center overflow-hidden shrink-0">
                      {u.photo_path ? (
                        <img src={u.photo_path} alt={u.full_name} className="w-full h-full object-cover" />
                      ) : (
                        <UsersIcon size={18} className="text-slate-500" />
                      )}
                    </div>
                    <div>
                      <div className="font-semibold text-white">{u.full_name}</div>
                      <div className="text-xs text-slate-500">{u.phone_number || "Telefon kiritilmagan"}</div>
                    </div>
                  </td>
                  <td className="py-4 px-6 font-mono text-xs text-indigo-300 font-semibold">
                    {u.employee_no}
                  </td>
                  <td className="py-4 px-6">
                    <span className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-medium mr-2 ${
                      u.role === 'student' ? 'bg-blue-950 text-blue-400 border border-blue-800' :
                      u.role === 'teacher' ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' :
                      'bg-purple-950 text-purple-400 border border-purple-800'
                    }`}>
                      {u.role === 'student' ? 'Talaba' : u.role === 'teacher' ? "O'qituvchi" : 'Xodim'}
                    </span>
                    {u.group_name && <span className="text-xs text-slate-400 font-mono">{u.group_name}</span>}
                  </td>
                  <td className="py-4 px-6">
                    {u.photo_path ? (
                      <span className="inline-flex items-center gap-1.5 text-xs text-emerald-400 bg-emerald-950/60 border border-emerald-800 px-2.5 py-1 rounded-lg">
                        <CheckCircle2 size={13} /> Yuklangan
                      </span>
                    ) : (
                      <button 
                        onClick={() => setShowPhotoModal(u)}
                        className="inline-flex items-center gap-1 text-xs text-amber-400 bg-amber-950/50 border border-amber-800/80 px-2.5 py-1 rounded-lg hover:bg-amber-900/60 transition"
                      >
                        <Camera size={13} /> Rasm Yuklash
                      </button>
                    )}
                  </td>
                  <td className="py-4 px-6 text-center">
                    <button 
                      onClick={() => handleSyncToAll(u.id)}
                      disabled={loading}
                      className="px-3 py-1.5 rounded-lg bg-indigo-600/20 hover:bg-indigo-600/40 text-indigo-300 border border-indigo-600/30 text-xs font-semibold transition flex items-center justify-center gap-1.5 mx-auto"
                      title="Barcha Face ID terminallariga yuklash"
                    >
                      <UserCheck size={14} /> Turniketlarga Yuborish
                    </button>
                  </td>
                  <td className="py-4 px-6 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <button 
                        onClick={() => setShowPhotoModal(u)}
                        className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
                        title="Suratni yangilash"
                      >
                        <Camera size={14} />
                      </button>
                      <button 
                        onClick={() => handleDelete(u.id)}
                        className="p-1.5 rounded-lg bg-rose-950/50 hover:bg-rose-900 text-rose-400 border border-rose-900/50 transition"
                        title="O'chirish"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}

              {filteredUsers.length === 0 && (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-500">
                    Foydalanuvchilar topilmadi
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add User Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/75 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-slate-900 border border-slate-800 w-full max-w-md rounded-2xl p-6 shadow-2xl">
            <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
              <UserPlus className="text-indigo-400" /> Yangi Talaba yoki Xodim Qo'shish
            </h3>
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">ID Raqami (Talaba / Hemis ID)</label>
                <input 
                  type="text" 
                  placeholder="3902148"
                  value={employeeNo}
                  onChange={(e) => setEmployeeNo(e.target.value)}
                  required
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-white text-sm focus:outline-none focus:border-indigo-500 font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">To'liq F.I.SH</label>
                <input 
                  type="text" 
                  placeholder="Azizov Jasur Alisherovich"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  required
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-white text-sm focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">Roli</label>
                  <select 
                    value={role}
                    onChange={(e: any) => setRole(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-white text-sm focus:outline-none focus:border-indigo-500"
                  >
                    <option value="student">Talaba</option>
                    <option value="teacher">O'qituvchi</option>
                    <option value="staff">Xodim</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">Guruh / Kafedra</label>
                  <input 
                    type="text" 
                    placeholder="941-21"
                    value={groupName}
                    onChange={(e) => setGroupName(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-white text-sm focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Telefon raqami</label>
                <input 
                  type="text" 
                  placeholder="+998 90 123 45 67"
                  value={phoneNumber}
                  onChange={(e) => setPhoneNumber(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-white text-sm focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="flex gap-3 pt-4">
                <button 
                  type="button" 
                  onClick={() => setShowAddModal(false)}
                  className="flex-1 py-2.5 rounded-xl border border-slate-700 bg-slate-800 text-slate-300 font-medium text-sm hover:bg-slate-700 transition"
                >
                  Bekor qilish
                </button>
                <button 
                  type="submit" 
                  disabled={loading}
                  className="flex-1 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-sm transition shadow-lg shadow-indigo-600/30"
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
        <div className="fixed inset-0 bg-black/75 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-slate-900 border border-slate-800 w-full max-w-sm rounded-2xl p-6 shadow-2xl text-center">
            <h3 className="text-lg font-bold text-white mb-2">Yuz Suratini Yuklash</h3>
            <p className="text-slate-400 text-xs mb-5">{showPhotoModal.full_name} ({showPhotoModal.employee_no})</p>

            <div className="w-40 h-40 mx-auto rounded-2xl bg-slate-950 border-2 border-dashed border-slate-700 flex items-center justify-center overflow-hidden mb-4 relative">
              {previewUrl ? (
                <img src={previewUrl} alt="Preview" className="w-full h-full object-cover" />
              ) : showPhotoModal.photo_path ? (
                <img src={showPhotoModal.photo_path} alt="Current" className="w-full h-full object-cover" />
              ) : (
                <div className="text-slate-600 flex flex-col items-center">
                  <Camera size={32} className="mb-1" />
                  <span className="text-[10px]">Surat tanlang</span>
                </div>
              )}
            </div>

            <input 
              type="file" 
              accept="image/jpeg,image/png" 
              id="face-file-input"
              onChange={handleFileChange}
              className="hidden" 
            />

            <label 
              htmlFor="face-file-input"
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold cursor-pointer border border-slate-700 mb-5"
            >
              <Upload size={14} /> Yangi surat tanlash
            </label>

            <div className="flex gap-3">
              <button 
                onClick={() => { setShowPhotoModal(null); setPreviewUrl(null); setSelectedFile(null); }}
                className="flex-1 py-2.5 rounded-xl border border-slate-700 bg-slate-800 text-slate-300 font-medium text-xs hover:bg-slate-700 transition"
              >
                Yopish
              </button>
              <button 
                onClick={handleUploadPhoto}
                disabled={!selectedFile || loading}
                className="flex-1 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-medium text-xs transition shadow-lg shadow-indigo-600/30"
              >
                {loading ? "Yuklanmoqda..." : "Suratni Saqlash"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
