import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Device, OrganizationInfo } from '../types';
import { 
  api,
  getDeviceCredentials,
  createDevice, 
  updateDevice,
  testDevice, 
  openDoorRemote, 
  deleteDevice, 
  getOrganizations, 
  updateOrganization, 
  createOrganization 
} from '../api';
import { 
  Settings as SettingsIcon, 
  Plus, 
  RefreshCw, 
  KeyRound, 
  CheckCircle, 
  AlertCircle, 
  Trash2, 
  Cpu, 
  ShieldCheck,
  Building2,
  GraduationCap,
  Layers,
  Check,
  ArrowRightLeft,
  Briefcase,
  Pencil,
  Clock,
  Monitor,
  CheckSquare
} from 'lucide-react';

interface SettingsProps {
  devices: Device[];
  onRefresh: () => void;
  currentOrg?: OrganizationInfo | null;
  onOrgUpdated?: (updatedOrg: OrganizationInfo) => void;
  isCompany?: boolean;
}

export const SettingsView: React.FC<SettingsProps> = ({ 
  devices, 
  onRefresh, 
  currentOrg, 
  onOrgUpdated, 
  isCompany 
}) => {
  const [activeTab, setActiveTab] = useState<'devices' | 'organization'>('devices');
  const [loading, setLoading] = useState(false);
  const [testResult, setTestResult] = useState<{ id: number; message: string; success: boolean } | null>(null);
  const [toastMsg, setToastMsg] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  const showToast = (text: string, type: 'success' | 'error' = 'success') => {
    setToastMsg({ text, type });
    setTimeout(() => setToastMsg(null), 4000);
  };

  // -------------------------------------------------------------
  // Organization Mode & Profile States
  // -------------------------------------------------------------
  const [allOrgs, setAllOrgs] = useState<any[]>([]);
  const [selectedOrgType, setSelectedOrgType] = useState<'university' | 'company'>(
    isCompany ? 'company' : 'university'
  );
  const [orgName, setOrgName] = useState(currentOrg?.name || '');
  const [orgCode, setOrgCode] = useState(currentOrg?.code || '');
  const [orgAddress, setOrgAddress] = useState('');
  const [showAddOrgModal, setShowAddOrgModal] = useState(false);
  
  // New Org Form
  const [newOrgName, setNewOrgName] = useState('');
  const [newOrgCode, setNewOrgCode] = useState('');
  const [newOrgType, setNewOrgType] = useState<'university' | 'company'>('company');
  const [newOrgAdminUser, setNewOrgAdminUser] = useState('admin');
  const [newOrgAdminPass, setNewOrgAdminPass] = useState('admin123');

  const loadOrganizationsList = async () => {
    try {
      const res = await getOrganizations();
      setAllOrgs(res);
      if (currentOrg) {
        const found = res.find((o: any) => o.id === currentOrg.id);
        if (found) {
          setOrgName(found.name);
          setOrgCode(found.code);
          setOrgAddress(found.address || '');
          setSelectedOrgType(
            found.org_type === 'company' || found.org_type === 'office' ? 'company' : 'university'
          );
        }
      }
    } catch (err) {
      console.error("Tashkilotlarni yuklashda xato:", err);
    }
  };

  useEffect(() => {
    loadOrganizationsList();
  }, [currentOrg]);

  const handleSaveOrgMode = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentOrg?.id) return;
    setLoading(true);
    try {
      const modules = selectedOrgType === 'company' 
        ? "dashboard,staff,structure,attendance,tabel,settings"
        : "dashboard,students,staff,structure,attendance,settings";

      await updateOrganization(currentOrg.id, {
        name: orgName.trim(),
        code: orgCode.trim(),
        address: orgAddress.trim(),
        org_type: selectedOrgType,
        modules_enabled: modules
      });

      const updatedInfo: OrganizationInfo = {
        ...currentOrg,
        name: orgName.trim(),
        code: orgCode.trim(),
        org_type: selectedOrgType,
        modules: modules.split(',')
      };

      localStorage.setItem('burgood_org', JSON.stringify(updatedInfo));
      onOrgUpdated?.(updatedInfo);
      showToast("Tashkilot rejimi muvaffaqiyatli saqlandi!");
      loadOrganizationsList();
    } catch (err: any) {
      showToast(err.response?.data?.detail || "Saqlashda xatolik yuz berdi", 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleSwitchOrganization = (orgItem: any) => {
    const modules = orgItem.modules_enabled 
      ? orgItem.modules_enabled.split(',').map((m: string) => m.trim())
      : (orgItem.org_type === 'company' ? ['dashboard', 'staff', 'structure', 'attendance', 'settings'] : ['dashboard', 'students', 'staff', 'structure', 'attendance', 'settings']);

    const newOrgData: OrganizationInfo = {
      id: orgItem.id,
      name: orgItem.name,
      code: orgItem.code,
      logo_url: orgItem.logo_url,
      org_type: orgItem.org_type === 'company' || orgItem.org_type === 'office' ? 'company' : 'university',
      modules: modules
    };

    localStorage.setItem('burgood_org', JSON.stringify(newOrgData));
    onOrgUpdated?.(newOrgData);
    showToast(`"${orgItem.name}" obyektiga o'tildi!`, 'success');
    setTimeout(() => {
      window.location.reload();
    }, 600);
  };

  const handleCreateNewOrg = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newOrgName.trim()) return;
    setLoading(true);
    try {
      await createOrganization({
        name: newOrgName.trim(),
        code: newOrgCode.trim() || newOrgName.substring(0, 4).toUpperCase(),
        org_type: newOrgType,
        admin_username: newOrgAdminUser.trim(),
        admin_password: newOrgAdminPass.trim(),
        modules_enabled: newOrgType === 'company' 
          ? "dashboard,staff,structure,attendance,tabel,settings" 
          : "dashboard,students,staff,structure,attendance,settings"
      });

      setShowAddOrgModal(false);
      setNewOrgName('');
      setNewOrgCode('');
      showToast("Yangi obyekt muvaffaqiyatli yaratildi!");
      loadOrganizationsList();
    } catch (err: any) {
      showToast(err.response?.data?.detail || "Yaratishda xatolik", 'error');
    } finally {
      setLoading(false);
    }
  };

  // -------------------------------------------------------------
  // Device Management States
  // -------------------------------------------------------------
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingDeviceId, setEditingDeviceId] = useState<number | null>(null);
  const [name, setName] = useState('');
  const [ipAddress, setIpAddress] = useState('');
  const [port, setPort] = useState(80);
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('');
  const [direction, setDirection] = useState<'entry' | 'exit' | 'universal'>('entry');
  const [universalMode, setUniversalMode] = useState<'screen_status' | 'smart_auto'>('smart_auto');
  const [universalOptions, setUniversalOptions] = useState<string[]>(['check_in', 'break_out', 'break_in', 'check_out']);
  const [lunchStart, setLunchStart] = useState('12:00');
  const [lunchEnd, setLunchEnd] = useState('14:00');
  const [location, setLocation] = useState('');

  const toggleUniversalOption = (opt: string) => {
    setUniversalOptions(prev => 
      prev.includes(opt) 
        ? (prev.length > 1 ? prev.filter(o => o !== opt) : prev) 
        : [...prev, opt]
    );
  };

  const handleOpenAddModal = () => {
    setEditingDeviceId(null);
    setName('');
    setIpAddress('');
    setPort(80);
    setUsername('admin');
    setPassword('');
    setDirection('entry');
    setUniversalMode('smart_auto');
    setUniversalOptions(['check_in', 'break_out', 'break_in', 'check_out']);
    setLunchStart('12:00');
    setLunchEnd('14:00');
    setLocation('');
    setShowAddModal(true);
  };

  const handleOpenEditModal = (dev: Device) => {
    setEditingDeviceId(dev.id);
    setName(dev.name);
    setIpAddress(dev.ip_address);
    setPort(dev.port);
    setUsername(dev.username);
    setPassword('');
    setDirection(dev.direction || 'entry');
    setUniversalMode((dev as any).universal_mode || 'smart_auto');
    const rawOpts = (dev as any).universal_options;
    if (rawOpts) {
      setUniversalOptions(rawOpts.split(',').map((s: string) => s.trim()).filter(Boolean));
    } else {
      setUniversalOptions(['check_in', 'break_out', 'break_in', 'check_out']);
    }
    setLunchStart((dev as any).lunch_start || '12:00');
    setLunchEnd((dev as any).lunch_end || '14:00');
    setLocation(dev.location || '');
    setShowAddModal(true);
  };

  const handleSaveDevice = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const payload: any = {
        name,
        ip_address: ipAddress,
        port: Number(port),
        username,
        direction,
        universal_mode: universalMode,
        universal_options: universalOptions.join(','),
        lunch_start: lunchStart,
        lunch_end: lunchEnd,
        location,
        is_active: true
      };
      if (password.trim()) {
        payload.password = password.trim();
      }

      if (editingDeviceId) {
        await updateDevice(editingDeviceId, payload);
        showToast("Terminal sozlamalari yangilandi!");
      } else {
        if (!password.trim()) {
          alert("Terminal parolini kiriting!");
          setLoading(false);
          return;
        }
        await createDevice(payload);
        showToast("Yangi terminal muvaffaqiyatli qo'shildi!");
      }

      setShowAddModal(false);
      onRefresh();
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'string' ? detail : (Array.isArray(detail) ? detail.map((d: any) => d.msg || JSON.stringify(d)).join(', ') : (err.message || "Saqlashda xatolik yuz berdi"));
      alert(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleTest = async (id: number) => {
    setLoading(true);
    const dev = devices.find(d => d.id === id);
    try {
      let isOnlineLocally = false;
      let localMsg = "";

      // 1. Agar Desktop dastur ichida bo'lsa, lokal tarmoq (LAN) orqali to'g'ridan-to'g'ri sinaymiz
      if (dev) {
        try {
          const ping = await axios.get('http://127.0.0.1:18200/api/ping', { timeout: 1200 });
          if (ping.data?.status === 'ok') {
            let devPassword = '';
            try {
              const cred = await getDeviceCredentials(dev.id);
              devPassword = cred.password || '';
            } catch {}

            const bridgeRes = await axios.post('http://127.0.0.1:18200/api/test-terminal', {
              ip: dev.ip_address,
              port: dev.port || 80,
              username: dev.username || 'admin',
              password: devPassword
            }, { timeout: 5000 });

            if (bridgeRes.data?.success) {
              isOnlineLocally = true;
              localMsg = bridgeRes.data.message;
              await api.post(`/devices/${dev.id}/mark-online`);
            }
          }
        } catch {}
      }

      if (isOnlineLocally) {
        setTestResult({ id, message: `✅ ${localMsg} (Lokal tarmoqda faol)`, success: true });
        onRefresh();
      } else {
        const res = await testDevice(id);
        setTestResult({ id, message: res.message, success: res.success });
        onRefresh();
      }
    } catch (err: any) {
      setTestResult({ id, message: err.response?.data?.detail || "Ulanish xatosi", success: false });
    } finally {
      setLoading(false);
    }
  };

  const handleOpenDoor = async (id: number) => {
    if (!confirm("Turniket eshigini masofadan ochmoqchimisiz?")) return;
    try {
      const res = await openDoorRemote(id);
      alert(res.message);
    } catch (err: any) {
      alert(err.response?.data?.detail || "Eshikni ochishda xatolik");
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Qurilmani o'chirishga ishonchingiz komilmi?")) return;
    try {
      await deleteDevice(id);
      onRefresh();
      showToast("Terminal o'chirildi!");
    } catch (err: any) {
      alert("O'chirishda xatolik yuz berdi");
    }
  };

  return (
    <div className="space-y-6">
      {/* Toast Alert */}
      {toastMsg && (
        <div className={`p-4 rounded-xl text-sm flex items-center gap-2.5 font-bold transition shadow-md ${
          toastMsg.type === 'success' 
            ? 'bg-emerald-50 text-emerald-800 border border-emerald-200' 
            : 'bg-rose-50 text-rose-800 border border-rose-200'
        }`}>
          {toastMsg.type === 'success' ? <CheckCircle size={18} className="text-emerald-600" /> : <AlertCircle size={18} className="text-rose-600" />}
          <span>{toastMsg.text}</span>
        </div>
      )}

      {/* Header Banner with Subtabs */}
      <div className="bg-white border border-slate-200/80 p-6 rounded-2xl shadow-sm space-y-5">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <h2 className="text-xl font-bold text-slate-800 flex items-center gap-2">
              <SettingsIcon className="text-[#0084ff]" size={24} />
              Tizim Sozlamalari
            </h2>
            <p className="text-slate-500 text-sm mt-1">
              Face ID terminallarini ulash hamda dastur rejimini (Universitet yoki Ofis / Korxona) boshqarish
            </p>
          </div>

          <div className="flex items-center gap-2.5">
            <button 
              onClick={() => { onRefresh(); loadOrganizationsList(); }}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl border border-slate-300 bg-white hover:bg-slate-50 text-slate-700 font-semibold text-sm transition"
            >
              <RefreshCw size={15} /> Yangilash
            </button>
            {activeTab === 'devices' && (
              <button 
                onClick={handleOpenAddModal}
                className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-[#0084ff] hover:bg-[#0073e0] text-white font-semibold text-sm shadow-md shadow-[#0084ff]/20 transition"
              >
                <Plus size={18} /> Yangi Terminal
              </button>
            )}
            {activeTab === 'organization' && (
              <button 
                onClick={() => setShowAddOrgModal(true)}
                className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-[#0084ff] hover:bg-[#0073e0] text-white font-semibold text-sm shadow-md shadow-[#0084ff]/20 transition"
              >
                <Plus size={18} /> Yangi Obyekt
              </button>
            )}
          </div>
        </div>

        {/* Subtabs Switcher */}
        <div className="flex flex-wrap gap-2 pt-2 border-t border-slate-100">
          <button
            onClick={() => setActiveTab('devices')}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition ${
              activeTab === 'devices'
                ? 'bg-[#0084ff] text-white shadow-sm'
                : 'bg-slate-100 text-slate-600 hover:text-slate-900 hover:bg-slate-200'
            }`}
          >
            <Cpu size={16} /> 1. Face ID Terminallari ({devices.length})
          </button>

          <button
            onClick={() => setActiveTab('organization')}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition ${
              activeTab === 'organization'
                ? 'bg-[#0084ff] text-white shadow-sm'
                : 'bg-slate-100 text-slate-600 hover:text-slate-900 hover:bg-slate-200'
            }`}
          >
            <Building2 size={16} /> 2. Tashkilot Rejimi & Faoliyati ({isCompany ? "🏢 Ofis / Biznes" : "🎓 Universitet"})
          </button>
        </div>
      </div>

      {/* ======================================================== */}
      {/* TAB 1: FACE ID TERMINALLARI                              */}
      {/* ======================================================== */}
      {activeTab === 'devices' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {devices.map((device) => (
            <div 
              key={device.id} 
              className="bg-white border border-slate-200/90 rounded-2xl p-5 hover:border-[#0084ff]/50 shadow-sm transition flex flex-col justify-between"
            >
              <div>
                <div className="flex justify-between items-start mb-3">
                  <div className="flex items-center gap-2">
                    <div className={`w-3 h-3 rounded-full ${
                      device.status === 'online' ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'
                    }`} />
                    <span className="font-bold text-base text-slate-900">{device.name}</span>
                  </div>
                  <span className={`px-2.5 py-0.5 text-xs font-bold rounded-full uppercase tracking-wider ${
                    device.direction === 'entry' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' :
                    device.direction === 'exit' ? 'bg-amber-50 text-amber-700 border border-amber-200' :
                    'bg-blue-50 text-[#0084ff] border border-blue-200'
                  }`}>
                    {device.direction === 'entry' ? '🟢 Kirish' :
                     device.direction === 'exit' ? '🔴 Chiqish' :
                     '🔄 Universal (1 ta terminal)'}
                  </span>
                </div>

                <div className="space-y-1.5 text-xs bg-slate-50 p-3.5 rounded-xl border border-slate-200 font-mono mb-4 text-slate-700">
                  <div className="flex justify-between">
                    <span className="text-slate-400">IP Manzil:</span>
                    <span className="text-[#0084ff] font-bold">{device.ip_address}:{device.port}</span>
                  </div>
                  {device.direction === 'universal' && (
                    <div className="flex flex-col gap-1.5 pt-1 border-t border-slate-200/60 mt-1">
                      <div className="flex justify-between text-[#0084ff] font-semibold">
                        <span className="text-slate-400">Rejim:</span>
                        <span className="truncate max-w-[170px]" title={(device as any).universal_mode === 'screen_status' ? 'Terminal Ekrani' : 'Aqlli Avtomat'}>
                          {(device as any).universal_mode === 'screen_status' 
                            ? '🖥️ Terminal Ekrani' 
                            : `⏰ Aqlli (${(device as any).lunch_start || '12:00'}-${(device as any).lunch_end || '14:00'})`}
                        </span>
                      </div>
                      <div className="flex flex-wrap gap-1">
                        {((device as any).universal_options || 'check_in,break_out,break_in,check_out').split(',').map((opt: string) => {
                          const o = opt.trim();
                          if (o === 'check_in') return <span key={o} className="text-[10px] bg-emerald-50 text-emerald-700 px-1.5 py-0.5 rounded font-bold border border-emerald-200">🟢 Kirish</span>;
                          if (o === 'break_out') return <span key={o} className="text-[10px] bg-amber-50 text-amber-700 px-1.5 py-0.5 rounded font-bold border border-amber-200">🟠 Tushlik chiqish</span>;
                          if (o === 'break_in') return <span key={o} className="text-[10px] bg-blue-50 text-blue-700 px-1.5 py-0.5 rounded font-bold border border-blue-200">🔵 Tushlik kirish</span>;
                          if (o === 'check_out') return <span key={o} className="text-[10px] bg-rose-50 text-rose-700 px-1.5 py-0.5 rounded font-bold border border-rose-200">🔴 Chiqish</span>;
                          return null;
                        })}
                      </div>
                    </div>
                  )}
                  <div className="flex justify-between">
                    <span className="text-slate-400">Model:</span>
                    <span>{device.model || 'Hikvision Face Terminal'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Seriya raqami:</span>
                    <span className="truncate max-w-[150px]">{device.serial_number || 'Aniqlanmagan'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Joylashuv:</span>
                    <span className="text-slate-800">{device.location || 'Asosiy korpus'}</span>
                  </div>
                </div>

                {testResult && testResult.id === device.id && (
                  <div className={`p-2.5 mb-3 rounded-xl text-xs flex items-center gap-2 ${
                    testResult.success ? 'bg-emerald-50 text-emerald-800 border border-emerald-200' : 'bg-rose-50 text-rose-800 border border-rose-200'
                  }`}>
                    {testResult.success ? <CheckCircle size={14} className="text-emerald-600" /> : <AlertCircle size={14} className="text-rose-600" />}
                    <span>{testResult.message}</span>
                  </div>
                )}
              </div>

              <div className="pt-3 border-t border-slate-100 flex items-center justify-between gap-2">
                <button 
                  onClick={() => handleTest(device.id)}
                  disabled={loading}
                  className="flex-1 py-2 text-xs font-semibold rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 transition"
                >
                  Aloqa Sinovi
                </button>
                <button 
                  onClick={() => handleOpenDoor(device.id)}
                  className="flex-1 py-2 text-xs font-bold rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white shadow-sm transition flex items-center justify-center gap-1.5"
                >
                  <KeyRound size={13} /> Eshikni Och
                </button>
                <button 
                  onClick={() => handleOpenEditModal(device)}
                  className="p-2 rounded-lg bg-blue-50 hover:bg-blue-100 text-[#0084ff] border border-blue-200 transition"
                  title="Sozlamalarni tahrirlash"
                >
                  <Pencil size={15} />
                </button>
                <button 
                  onClick={() => handleDelete(device.id)}
                  className="p-2 rounded-lg bg-rose-50 hover:bg-rose-100 text-rose-600 border border-rose-200 transition"
                  title="O'chirish"
                >
                  <Trash2 size={15} />
                </button>
              </div>
            </div>
          ))}

          {devices.length === 0 && (
            <div className="col-span-full py-16 text-center text-slate-400 bg-white border border-dashed border-slate-300 rounded-2xl">
              <Cpu size={40} className="mx-auto mb-3 opacity-40" />
              <p className="text-base font-semibold text-slate-700">Hozircha hech qanday Face ID terminali kiritilmagan</p>
              <p className="text-xs text-slate-500 mt-1">"Yangi Terminal" tugmasini bosing va qurilma parametrlarini kiriting</p>
            </div>
          )}
        </div>
      )}

      {/* ======================================================== */}
      {/* TAB 2: TASHKILOT REJIMI & FAOLIYATI                     */}
      {/* ======================================================== */}
      {activeTab === 'organization' && (
        <div className="space-y-6">
          {/* Active Mode Form Card */}
          <div className="bg-white border border-slate-200/90 rounded-2xl p-6 shadow-sm">
            <div className="mb-6">
              <h3 className="text-lg font-black text-slate-900 tracking-tight flex items-center gap-2">
                <ShieldCheck className="text-[#0084ff]" size={22} />
                Tashkilot Faoliyat Turi va Tizim Rejimi
              </h3>
              <p className="text-xs text-slate-500 mt-1">
                Dasturni korxona ofisi yoki universitet sifatida ishlatish uchun rejimni tanlang va saqlang.
              </p>
            </div>

            <form onSubmit={handleSaveOrgMode} className="space-y-6">
              {/* Select Mode Option Cards */}
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-3">
                  Tizim Ishlash Rejimi (Faoliyat Yo'nalishi)
                </label>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  
                  {/* Card 1: Universitet / Maktab */}
                  <div 
                    onClick={() => setSelectedOrgType('university')}
                    className={`p-5 rounded-2xl border-2 cursor-pointer transition relative ${
                      selectedOrgType === 'university'
                        ? 'border-[#0084ff] bg-blue-50/40 shadow-sm'
                        : 'border-slate-200 hover:border-slate-300 bg-white'
                    }`}
                  >
                    {selectedOrgType === 'university' && (
                      <span className="absolute top-4 right-4 w-6 h-6 rounded-full bg-[#0084ff] text-white flex items-center justify-center text-xs">
                        <Check size={14} />
                      </span>
                    )}
                    <div className="w-11 h-11 rounded-xl bg-blue-100 text-[#0084ff] flex items-center justify-center mb-3">
                      <GraduationCap size={24} />
                    </div>
                    <h4 className="font-bold text-base text-slate-900">
                      🎓 Ta'lim Muassasasi (Universitet / Maktab)
                    </h4>
                    <p className="text-xs text-slate-500 mt-1 leading-relaxed">
                      Fakultetlar, Kafedralar, Akademik Guruhlar, Talabalar davomati, Tyutorlar va O'qituvchilar bo'limi faol bo'ladi.
                    </p>
                    <div className="mt-3 flex flex-wrap gap-1.5">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-white text-blue-700 border border-blue-200">Talabalar</span>
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-white text-blue-700 border border-blue-200">Fakultet & Guruhlar</span>
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-white text-blue-700 border border-blue-200">Tyutorlar</span>
                    </div>
                  </div>

                  {/* Card 2: Idora / Ofis / Korxona */}
                  <div 
                    onClick={() => setSelectedOrgType('company')}
                    className={`p-5 rounded-2xl border-2 cursor-pointer transition relative ${
                      selectedOrgType === 'company'
                        ? 'border-[#0084ff] bg-blue-50/40 shadow-sm'
                        : 'border-slate-200 hover:border-slate-300 bg-white'
                    }`}
                  >
                    {selectedOrgType === 'company' && (
                      <span className="absolute top-4 right-4 w-6 h-6 rounded-full bg-[#0084ff] text-white flex items-center justify-center text-xs">
                        <Check size={14} />
                      </span>
                    )}
                    <div className="w-11 h-11 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center mb-3">
                      <Building2 size={24} />
                    </div>
                    <h4 className="font-bold text-base text-slate-900">
                      🏢 Idora / Ofis / Korxona / Tadbirkorlik
                    </h4>
                    <p className="text-xs text-slate-500 mt-1 leading-relaxed">
                      Departamentlar, Filiallar, Xodimlar davomati, Smenalar va Oylik Tabel (.xlsx). Talabalar bo'limi butunlay yashiriladi.
                    </p>
                    <div className="mt-3 flex flex-wrap gap-1.5">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-white text-emerald-700 border border-emerald-200">Faqat Xodimlar</span>
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-white text-emerald-700 border border-emerald-200">Bo'limlar & Filiallar</span>
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-white text-emerald-700 border border-emerald-200">Oylik Tabel (.xlsx)</span>
                    </div>
                  </div>

                </div>
              </div>

              {/* Organization Info Fields */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1.5">
                    Tashkilot Nomi
                  </label>
                  <input 
                    type="text" 
                    value={orgName}
                    onChange={(e) => setOrgName(e.target.value)}
                    required
                    placeholder="Masalan: Burgood Holding yoki Voha Trans MCHJ"
                    className="w-full bg-slate-50 border border-slate-300 rounded-xl px-4 py-2.5 text-slate-900 text-sm focus:outline-none focus:border-[#0084ff] focus:bg-white font-medium"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1.5">
                    Qisqa Kod (Prefiks)
                  </label>
                  <input 
                    type="text" 
                    value={orgCode}
                    onChange={(e) => setOrgCode(e.target.value)}
                    placeholder="Masalan: BGD, OFFICE1, UDU"
                    className="w-full bg-slate-50 border border-slate-300 rounded-xl px-4 py-2.5 text-slate-900 text-sm focus:outline-none focus:border-[#0084ff] focus:bg-white font-mono uppercase font-bold"
                  />
                </div>

                <div className="md:col-span-2">
                  <label className="block text-xs font-bold text-slate-700 mb-1.5">
                    Manzili (Bino yoki Ofis manzili)
                  </label>
                  <input 
                    type="text" 
                    value={orgAddress}
                    onChange={(e) => setOrgAddress(e.target.value)}
                    placeholder="Masalan: Toshkent sh., Chilonzor tumani, 12-bino"
                    className="w-full bg-slate-50 border border-slate-300 rounded-xl px-4 py-2.5 text-slate-900 text-sm focus:outline-none focus:border-[#0084ff] focus:bg-white"
                  />
                </div>
              </div>

              <div className="flex justify-end pt-3 border-t border-slate-100">
                <button
                  type="submit"
                  disabled={loading}
                  className="px-6 py-3 rounded-xl bg-[#0084ff] hover:bg-[#0073e0] text-white font-bold text-sm shadow-md shadow-[#0084ff]/25 transition cursor-pointer flex items-center gap-2"
                >
                  <Check size={18} /> Rejimni Saqlash va Qo'llash
                </button>
              </div>
            </form>
          </div>

          {/* List of All Configured Objects / Organizations */}
          <div className="bg-white border border-slate-200/90 rounded-2xl p-6 shadow-sm">
            <div className="flex justify-between items-center mb-5">
              <div>
                <h3 className="text-lg font-bold text-slate-900 tracking-tight flex items-center gap-2">
                  <Layers className="text-[#0084ff]" size={20} />
                  Barcha Tizimdagi Obyektlar (Korxonalar va Universitetlar)
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Tizimda yaratilgan barcha universitetlar va korxonalar orasida tezkor almashish
                </p>
              </div>
              <button
                onClick={() => setShowAddOrgModal(true)}
                className="px-3.5 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs font-bold transition flex items-center gap-1.5"
              >
                <Plus size={15} /> Yangi Obyekt Qo'shish
              </button>
            </div>

            <div className="space-y-3">
              {allOrgs.map((item) => {
                const isCurrent = currentOrg?.id === item.id;
                const isOfis = item.org_type === 'company' || item.org_type === 'office';
                return (
                  <div 
                    key={item.id} 
                    className={`p-4 rounded-xl border flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 transition ${
                      isCurrent 
                        ? 'bg-blue-50/50 border-[#0084ff] shadow-xs' 
                        : 'bg-slate-50/80 border-slate-200 hover:bg-slate-100/70'
                    }`}
                  >
                    <div className="flex items-center gap-3.5">
                      <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${
                        isOfis ? 'bg-emerald-100 text-emerald-700' : 'bg-blue-100 text-[#0084ff]'
                      }`}>
                        {isOfis ? <Building2 size={20} /> : <GraduationCap size={20} />}
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-sm text-slate-900">{item.name}</span>
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                            isOfis ? 'bg-emerald-100 text-emerald-800' : 'bg-blue-100 text-blue-800'
                          }`}>
                            {isOfis ? "🏢 Ofis / Biznes" : "🎓 Ta'lim"}
                          </span>
                        </div>
                        <div className="text-xs text-slate-500 mt-0.5 font-mono">
                          Kod: <span className="font-bold text-slate-700">{item.code || '-'}</span> • Admin: <span className="font-bold text-slate-700">{item.admin_username}</span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 self-end sm:self-center">
                      {isCurrent ? (
                        <span className="px-3.5 py-1.5 rounded-lg bg-emerald-100 text-emerald-800 border border-emerald-200 text-xs font-bold flex items-center gap-1.5">
                          <Check size={14} /> Faol Obyekt
                        </span>
                      ) : (
                        <button
                          onClick={() => handleSwitchOrganization(item)}
                          className="px-3.5 py-1.5 rounded-lg bg-white hover:bg-blue-50 text-[#0084ff] border border-blue-200 text-xs font-bold transition shadow-xs flex items-center gap-1.5"
                        >
                          <ArrowRightLeft size={13} /> Ushbu Obyektga O'tish
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* ======================================================== */}
      {/* MODAL: ADD NEW TERMINAL                                 */}
      {/* ======================================================== */}
      {showAddModal && (
        <div className="fixed inset-0 bg-slate-950/75 flex items-center justify-center z-50 p-4 overflow-y-auto">
          <div className="bg-white border border-slate-200 w-full max-w-lg rounded-2xl p-6 shadow-2xl animate-in fade-in zoom-in-95 duration-150 my-6">
            <h3 className="text-lg font-bold text-slate-900 mb-4 flex items-center gap-2">
              <SettingsIcon className="text-[#0084ff]" /> 
              {editingDeviceId ? "Terminal Sozlamalarini Tahrirlash" : "Yangi Terminal Qo'shish"}
            </h3>
            <form onSubmit={handleSaveDevice} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1">Terminal Nomi</label>
                <input 
                  type="text" 
                  placeholder="Turniket 1 - Bosh bino"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                  className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2 text-slate-900 text-sm focus:outline-none focus:border-[#0084ff] focus:bg-white"
                />
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div className="col-span-2">
                  <label className="block text-xs font-semibold text-slate-600 mb-1">IP Manzil</label>
                  <input 
                    type="text" 
                    placeholder="192.168.1.120"
                    value={ipAddress}
                    onChange={(e) => setIpAddress(e.target.value)}
                    required
                    className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2 text-slate-900 text-sm focus:outline-none focus:border-[#0084ff] focus:bg-white font-mono"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-1">Port</label>
                  <input 
                    type="number" 
                    value={port}
                    onChange={(e) => setPort(Number(e.target.value))}
                    className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2 text-slate-900 text-sm focus:outline-none focus:border-[#0084ff] focus:bg-white font-mono"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-1">Terminal Logini</label>
                  <input 
                    type="text" 
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    required
                    className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2 text-slate-900 text-sm focus:outline-none focus:border-[#0084ff] focus:bg-white"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-1">
                    Terminal Paroli {editingDeviceId && <span className="text-slate-400 font-normal">(ixtiyoriy)</span>}
                  </label>
                  <input 
                    type="password" 
                    placeholder={editingDeviceId ? "O'zgartirmaslik uchun bo'sh qoldiring" : "••••••••"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required={!editingDeviceId}
                    className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2 text-slate-900 text-sm focus:outline-none focus:border-[#0084ff] focus:bg-white"
                  />
                </div>
              </div>

              {/* Terminal Yo'nalishi (Kirish / Chiqish / Universal) */}
              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1">
                  Terminal Vazifasi (Yo'nalishi)
                </label>
                <div className="grid grid-cols-3 gap-1.5 p-1 bg-slate-100 rounded-xl border border-slate-200">
                  <button
                    type="button"
                    onClick={() => setDirection('entry')}
                    className={`py-2 px-2 rounded-lg text-xs font-bold transition flex items-center justify-center gap-1.5 ${
                      direction === 'entry'
                        ? 'bg-emerald-600 text-white shadow-sm'
                        : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200'
                    }`}
                  >
                    🟢 Kirish
                  </button>
                  <button
                    type="button"
                    onClick={() => setDirection('exit')}
                    className={`py-2 px-2 rounded-lg text-xs font-bold transition flex items-center justify-center gap-1.5 ${
                      direction === 'exit'
                        ? 'bg-amber-600 text-white shadow-sm'
                        : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200'
                    }`}
                  >
                    🔴 Chiqish
                  </button>
                  <button
                    type="button"
                    onClick={() => setDirection('universal')}
                    className={`py-2 px-2 rounded-lg text-xs font-bold transition flex items-center justify-center gap-1.5 ${
                      direction === 'universal'
                        ? 'bg-[#0084ff] text-white shadow-sm'
                        : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200'
                    }`}
                  >
                    🔄 Universal
                  </button>
                </div>
              </div>

              {/* Bitta Face ID terminal bo'lsa: 4 ta Holat (Checkboxlar) va Aniqlash Usuli tanlovi */}
              {direction === 'universal' && (
                <div className="p-4 bg-gradient-to-br from-blue-50/90 to-indigo-50/50 border border-blue-200 rounded-2xl space-y-4 animate-in fade-in duration-200">
                  {/* 4 ta Checkbox: Kirish, Tushlikka chiqish, Tushlikdan qaytish, Chiqish */}
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <label className="text-xs font-bold text-slate-900 flex items-center gap-1.5">
                        <CheckSquare size={15} className="text-[#0084ff]" />
                        Face ID Terminal Ekrani & Tizim Holatlari:
                      </label>
                      <span className="text-[10px] text-blue-700 bg-blue-100 font-bold px-2 py-0.5 rounded-full border border-blue-200">
                        {universalOptions.length} ta holat faol
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-500 mb-2.5">
                      Mijoz talabiga ko'ra kerakli holatlarni belgilang. Tanlangan holatlar terminal ekrani va dasturda ishlaydi:
                    </p>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                      {/* 1. Kirish */}
                      <label className={`flex items-center gap-2.5 p-2.5 rounded-xl border cursor-pointer transition select-none ${
                        universalOptions.includes('check_in') 
                          ? 'bg-emerald-50 border-emerald-300 text-emerald-950 font-bold shadow-xs' 
                          : 'bg-white border-slate-200 text-slate-500 hover:bg-slate-50'
                      }`}>
                        <input 
                          type="checkbox"
                          checked={universalOptions.includes('check_in')}
                          onChange={() => toggleUniversalOption('check_in')}
                          className="w-4 h-4 text-emerald-600 rounded cursor-pointer accent-emerald-600 shrink-0"
                        />
                        <div className="flex flex-col">
                          <span className="text-xs">🟢 Kirish (Check In)</span>
                          <span className="text-[10px] font-normal text-slate-500">Ertalab ishga kelish</span>
                        </div>
                      </label>

                      {/* 2. Tushlikka chiqish */}
                      <label className={`flex items-center gap-2.5 p-2.5 rounded-xl border cursor-pointer transition select-none ${
                        universalOptions.includes('break_out') 
                          ? 'bg-amber-50 border-amber-300 text-amber-950 font-bold shadow-xs' 
                          : 'bg-white border-slate-200 text-slate-500 hover:bg-slate-50'
                      }`}>
                        <input 
                          type="checkbox"
                          checked={universalOptions.includes('break_out')}
                          onChange={() => toggleUniversalOption('break_out')}
                          className="w-4 h-4 text-amber-600 rounded cursor-pointer accent-amber-600 shrink-0"
                        />
                        <div className="flex flex-col">
                          <span className="text-xs">🟠 Tushlikka chiqish</span>
                          <span className="text-[10px] font-normal text-slate-500">Tushlik oralig'iga ketish</span>
                        </div>
                      </label>

                      {/* 3. Tushlikdan qaytish */}
                      <label className={`flex items-center gap-2.5 p-2.5 rounded-xl border cursor-pointer transition select-none ${
                        universalOptions.includes('break_in') 
                          ? 'bg-blue-50 border-blue-300 text-blue-950 font-bold shadow-xs' 
                          : 'bg-white border-slate-200 text-slate-500 hover:bg-slate-50'
                      }`}>
                        <input 
                          type="checkbox"
                          checked={universalOptions.includes('break_in')}
                          onChange={() => toggleUniversalOption('break_in')}
                          className="w-4 h-4 text-[#0084ff] rounded cursor-pointer accent-[#0084ff] shrink-0"
                        />
                        <div className="flex flex-col">
                          <span className="text-xs">🔵 Tushlikdan qaytish</span>
                          <span className="text-[10px] font-normal text-slate-500">Tushlikdan ishga qaytish</span>
                        </div>
                      </label>

                      {/* 4. Chiqish */}
                      <label className={`flex items-center gap-2.5 p-2.5 rounded-xl border cursor-pointer transition select-none ${
                        universalOptions.includes('check_out') 
                          ? 'bg-rose-50 border-rose-300 text-rose-950 font-bold shadow-xs' 
                          : 'bg-white border-slate-200 text-slate-500 hover:bg-slate-50'
                      }`}>
                        <input 
                          type="checkbox"
                          checked={universalOptions.includes('check_out')}
                          onChange={() => toggleUniversalOption('check_out')}
                          className="w-4 h-4 text-rose-600 rounded cursor-pointer accent-rose-600 shrink-0"
                        />
                        <div className="flex flex-col">
                          <span className="text-xs">🔴 Chiqish (Check Out)</span>
                          <span className="text-[10px] font-normal text-slate-500">Ish vaqti tugab ketish</span>
                        </div>
                      </label>
                    </div>
                  </div>

                  {/* Aniqlash usuli: Avtomat yoki Ekrandan bosish */}
                  <div className="pt-2 border-t border-blue-200/60">
                    <label className="block text-xs font-bold text-slate-800 mb-1.5">
                      Bitta terminalda yo'nalishni aniqlash usuli:
                    </label>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                      <button
                        type="button"
                        onClick={() => setUniversalMode('smart_auto')}
                        className={`p-2.5 rounded-xl border text-left transition flex flex-col gap-1 ${
                          universalMode === 'smart_auto'
                            ? 'bg-[#0084ff] text-white border-[#0084ff] shadow-sm'
                            : 'bg-white text-slate-700 border-slate-200 hover:border-slate-300'
                        }`}
                      >
                        <span className="text-xs font-bold flex items-center gap-1.5">
                          <Clock size={14} /> 1. Avtomatik (Aqlli)
                        </span>
                        <span className={`text-[10px] leading-tight ${universalMode === 'smart_auto' ? 'text-blue-100' : 'text-slate-500'}`}>
                          Vaqt va navbatga qarab (ertalab kelish, tushlik, kechqurun ketish)
                        </span>
                      </button>

                      <button
                        type="button"
                        onClick={() => setUniversalMode('screen_status')}
                        className={`p-2.5 rounded-xl border text-left transition flex flex-col gap-1 ${
                          universalMode === 'screen_status'
                            ? 'bg-[#0084ff] text-white border-[#0084ff] shadow-sm'
                            : 'bg-white text-slate-700 border-slate-200 hover:border-slate-300'
                        }`}
                      >
                        <span className="text-xs font-bold flex items-center gap-1.5">
                          <Monitor size={14} /> 2. Terminal Ekrani
                        </span>
                        <span className={`text-[10px] leading-tight ${universalMode === 'screen_status' ? 'text-blue-100' : 'text-slate-500'}`}>
                          Xodim ekrandagi tugmalarni tanlab yuzini ko'rsatadi
                        </span>
                      </button>
                    </div>
                  </div>

                  {universalMode === 'smart_auto' && (universalOptions.includes('break_out') || universalOptions.includes('break_in')) && (
                    <div className="pt-2 border-t border-blue-200/60">
                      <label className="block text-xs font-bold text-slate-700 mb-1">
                        🍱 Tushlik vaqti oralig'i (Chiqish va Qaytish uchun):
                      </label>
                      <div className="grid grid-cols-2 gap-2">
                        <div>
                          <span className="text-[10px] text-slate-500 font-medium">Boshlanishi:</span>
                          <input 
                            type="time" 
                            value={lunchStart}
                            onChange={(e) => setLunchStart(e.target.value)}
                            className="w-full bg-white border border-slate-300 rounded-lg px-2.5 py-1.5 text-xs font-bold text-slate-800"
                          />
                        </div>
                        <div>
                          <span className="text-[10px] text-slate-500 font-medium">Tugashi:</span>
                          <input 
                            type="time" 
                            value={lunchEnd}
                            onChange={(e) => setLunchEnd(e.target.value)}
                            className="w-full bg-white border border-slate-300 rounded-lg px-2.5 py-1.5 text-xs font-bold text-slate-800"
                          />
                        </div>
                      </div>
                      <p className="text-[10px] text-slate-500 mt-1">
                        * Shu soatlar orasida xodim birinchi chiqsa "Tushlikka ketdi", qaytib kirsa "Tushlikdan qaytdi" deb hisoblanadi.
                      </p>
                    </div>
                  )}
                </div>
              )}

              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1">Joylashuv</label>
                <input 
                  type="text" 
                  placeholder="Bosh korpus, 1-qavat"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
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
                  {loading ? "Saqlanmoqda..." : (editingDeviceId ? "Saqlash" : "Qo'shish")}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ======================================================== */}
      {/* MODAL: CREATE NEW ORGANIZATION                           */}
      {/* ======================================================== */}
      {showAddOrgModal && (
        <div className="fixed inset-0 bg-slate-950/75 flex items-center justify-center z-50 p-4">
          <div className="bg-white border border-slate-200 w-full max-w-lg rounded-2xl p-6 shadow-2xl animate-in fade-in zoom-in-95 duration-150">
            <h3 className="text-lg font-bold text-slate-900 mb-2 flex items-center gap-2">
              <Building2 className="text-[#0084ff]" /> Yangi Obyekt Yaratish
            </h3>
            <p className="text-xs text-slate-500 mb-5">
              Yangi universitet yoki tadbirkorlik ofisi uchun alohida tashkilot hisobini yarating
            </p>

            <form onSubmit={handleCreateNewOrg} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1.5">
                  Faoliyat Turi
                </label>
                <div className="grid grid-cols-2 gap-2 p-1 bg-slate-100 rounded-xl border border-slate-200">
                  <button
                    type="button"
                    onClick={() => setNewOrgType('company')}
                    className={`py-2 px-3 rounded-lg text-xs font-bold transition flex items-center justify-center gap-1.5 ${
                      newOrgType === 'company'
                        ? 'bg-emerald-600 text-white shadow-sm'
                        : 'text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    <Building2 size={15} /> 🏢 Idora / Korxona
                  </button>
                  <button
                    type="button"
                    onClick={() => setNewOrgType('university')}
                    className={`py-2 px-3 rounded-lg text-xs font-bold transition flex items-center justify-center gap-1.5 ${
                      newOrgType === 'university'
                        ? 'bg-[#0084ff] text-white shadow-sm'
                        : 'text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    <GraduationCap size={15} /> 🎓 Universitet
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1.5">
                  Tashkilot / Korxona Nomi <span className="text-rose-500">*</span>
                </label>
                <input 
                  type="text" 
                  value={newOrgName}
                  onChange={(e) => setNewOrgName(e.target.value)}
                  required
                  placeholder={newOrgType === 'company' ? "Masalan: Burgood Trading MCHJ" : "Masalan: Samarqand Davlat Universiteti"}
                  className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2 text-slate-900 text-sm focus:outline-none focus:border-[#0084ff] focus:bg-white"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1.5">
                  Qisqa Kod (Prefiks)
                </label>
                <input 
                  type="text" 
                  value={newOrgCode}
                  onChange={(e) => setNewOrgCode(e.target.value)}
                  placeholder="Masalan: BGD2, SAMDU"
                  className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2 text-slate-900 text-sm focus:outline-none focus:border-[#0084ff] focus:bg-white font-mono uppercase"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1.5">Admin Logini</label>
                  <input 
                    type="text" 
                    value={newOrgAdminUser}
                    onChange={(e) => setNewOrgAdminUser(e.target.value)}
                    required
                    className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2 text-slate-900 text-sm focus:outline-none focus:border-[#0084ff] focus:bg-white"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1.5">Admin Paroli</label>
                  <input 
                    type="text" 
                    value={newOrgAdminPass}
                    onChange={(e) => setNewOrgAdminPass(e.target.value)}
                    required
                    className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2 text-slate-900 text-sm focus:outline-none focus:border-[#0084ff] focus:bg-white"
                  />
                </div>
              </div>

              <div className="flex gap-3 pt-3 border-t border-slate-100">
                <button 
                  type="button" 
                  onClick={() => setShowAddOrgModal(false)}
                  className="flex-1 py-2.5 rounded-xl border border-slate-300 bg-white text-slate-700 font-semibold text-sm hover:bg-slate-50 transition"
                >
                  Bekor qilish
                </button>
                <button 
                  type="submit" 
                  disabled={loading}
                  className="flex-1 py-2.5 rounded-xl bg-[#0084ff] hover:bg-[#0073e0] text-white font-bold text-sm transition shadow-md shadow-[#0084ff]/20"
                >
                  {loading ? "Yaratilmoqda..." : "Yaratish"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
