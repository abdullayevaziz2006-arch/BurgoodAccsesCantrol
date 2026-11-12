import React, { useState, useEffect } from 'react';
import { 
  Users, 
  Cpu, 
  ArrowDownLeft, 
  ArrowUpRight, 
  Radio, 
  Clock, 
  LayoutDashboard, 
  UserCheck,
  Building2,
  LogOut,
  Settings,
  GraduationCap,
  Briefcase,
  Landmark,
  Menu,
  X,
  CalendarDays,
  Calendar,
  Timer,
  ChevronDown,
  ChevronRight
} from 'lucide-react';
import { 
  getStats, 
  getDevices, 
  getUsers, 
  getLogs,
  getFaculties,
  getDepartments,
  getGroups,
  getPotentialTutors,
  getMe
} from './api';
import { DashboardStats, Device, User, AccessLog, Faculty, Department, Group, OrganizationInfo, UserInfo, AuthResponse } from './types';
import { StudentsView } from './components/StudentsView';
import { StaffView } from './components/StaffView';
import { StructureView } from './components/StructureView';
import { AttendanceView } from './components/AttendanceView';
import { AttendanceSettingsView } from './components/AttendanceSettingsView';
import { SettingsView } from './components/SettingsView';
import { LoginView } from './components/LoginView';

export function App() {
  const [authToken, setAuthToken] = useState<string | null>(() => localStorage.getItem('burgood_token'));
  const [currentUser, setCurrentUser] = useState<UserInfo | null>(() => {
    try {
      const u = localStorage.getItem('burgood_user');
      return u ? JSON.parse(u) : null;
    } catch {
      return null;
    }
  });
  const [currentOrg, setCurrentOrg] = useState<OrganizationInfo | null>(() => {
    try {
      const o = localStorage.getItem('burgood_org');
      return o ? JSON.parse(o) : null;
    } catch {
      return null;
    }
  });

  const handleLogout = () => {
    localStorage.removeItem('burgood_token');
    localStorage.removeItem('burgood_user');
    localStorage.removeItem('burgood_org');
    setAuthToken(null);
    setCurrentUser(null);
    setCurrentOrg(null);
    try {
      (window as any).AndroidBridge?.logout();
    } catch (e) {}
  };

  const [activeTab, setActiveTab] = useState<'dashboard' | 'students' | 'staff' | 'structure' | 'attendance' | 'attendance_settings' | 'settings'>('dashboard');
  const [attendanceMenuOpen, setAttendanceMenuOpen] = useState(false);
  const [attendanceSubTab, setAttendanceSubTab] = useState<'shifts' | 'schedules' | 'assign_staff' | 'assign_students'>('shifts');
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [devices, setDevices] = useState<Device[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [faculties, setFaculties] = useState<Faculty[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [groups, setGroups] = useState<Group[]>([]);
  const [tutors, setTutors] = useState<User[]>([]);
  const [logs, setLogs] = useState<AccessLog[]>([]);
  const [liveLogs, setLiveLogs] = useState<AccessLog[]>([]);
  const [wsConnected, setWsConnected] = useState(false);
  const [lang, setLang] = useState<'UZ' | 'RU'>('UZ');
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);
  const [fadeExit, setFadeExit] = useState(false);

  const dismissLoadingScreen = () => {
    setFadeExit(true);
    setTimeout(() => {
      setInitialLoading(false);
    }, 500);
  };

  // Foydalanuvchi huquqlari va ruxsatlarini doimiy server bilan jonli sinxronlash
  useEffect(() => {
    if (!authToken) return;
    getMe()
      .then(res => {
        if (res.success && res.user) {
          setCurrentUser(res.user);
          localStorage.setItem('burgood_user', JSON.stringify(res.user));
          if (res.organization) {
            setCurrentOrg(res.organization);
            localStorage.setItem('burgood_org', JSON.stringify(res.organization));
          }
        }
      })
      .catch(() => {});
  }, [authToken]);

  const loadData = async (isInitial = false) => {
    try {
      const [sRes, dRes, uRes, lRes, facsRes, deptsRes, grpsRes, tutsRes] = await Promise.allSettled([
        getStats(),
        getDevices(),
        getUsers(),
        getLogs({ limit: 50 }),
        getFaculties(),
        getDepartments(),
        getGroups(),
        getPotentialTutors()
      ]);
      if (sRes.status === 'fulfilled') setStats(sRes.value);
      if (dRes.status === 'fulfilled') setDevices(dRes.value);
      if (uRes.status === 'fulfilled') setUsers(uRes.value);
      if (lRes.status === 'fulfilled') {
        setLogs(lRes.value);
        setLiveLogs(lRes.value.slice(0, 8));
      }
      if (facsRes.status === 'fulfilled') setFaculties(facsRes.value);
      if (deptsRes.status === 'fulfilled') setDepartments(deptsRes.value);
      if (grpsRes.status === 'fulfilled') setGroups(grpsRes.value);
      if (tutsRes.status === 'fulfilled') setTutors(tutsRes.value);
    } catch (err) {
      console.error("Ma'lumotlarni yuklashda xatolik:", err);
    } finally {
      if (isInitial) {
        dismissLoadingScreen();
      }
    }
  };

  useEffect(() => {
    loadData(true);
    // Xavfsizlik taymeri: internet 3G bo'lsa yoki API kechiksa ham eng ko'pi 4s ichida ekranni ochish
    const fallbackTimer = setTimeout(() => {
      dismissLoadingScreen();
    }, 4000);

    const interval = setInterval(() => loadData(false), 30000);
    return () => {
      clearTimeout(fallbackTimer);
      clearInterval(interval);
    };
  }, []);

  // WebSocket Live Events
  useEffect(() => {
    let ws: WebSocket | null = null;
    let reconnectTimeout: any = null;
    let isDestroyed = false;

    const connectWs = () => {
      if (isDestroyed) return;
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/ws/live-events`;
      ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        setWsConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          if (payload.type === 'NEW_ACCESS_EVENT') {
            const newLog: AccessLog = payload.data;

            // 1. Jonli oqim dublikatini oldini olish (ID bo'yicha tekshirish)
            setLiveLogs(prev => {
              if (prev.some(item => item.id === newLog.id)) return prev;
              return [newLog, ...prev.slice(0, 9)];
            });

            // 2. Asosiy davomat ro'yxati dublikatini oldini olish
            setLogs(prev => {
              if (prev.some(item => item.id === newLog.id)) return prev;
              return [newLog, ...prev];
            });

            // 3. Statistika hisoblagichi
            setStats(prev => {
              if (!prev) return null;
              return {
                ...prev,
                today_entries: newLog.direction === 'entry' ? prev.today_entries + 1 : prev.today_entries,
                today_exits: newLog.direction === 'exit' ? prev.today_exits + 1 : prev.today_exits,
              };
            });
          }
        } catch (e) {
          console.error("WS error:", e);
        }
      };

      ws.onclose = () => {
        setWsConnected(false);
        if (!isDestroyed) {
          reconnectTimeout = setTimeout(connectWs, 3000);
        }
      };

      ws.onerror = () => {
        setWsConnected(false);
      };
    };

    connectWs();

    return () => {
      isDestroyed = true;
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
      if (ws) {
        ws.close();
      }
    };
  }, []);

  const studentCount = users.filter(u => u.role === 'student').length;
  const staffCount = users.filter(u => u.role !== 'student').length;

  const userRole = currentUser?.role || 'admin';
  const isAdmin = userRole === 'admin' || userRole === 'superadmin';
  
  const rawModules = (currentUser?.allowed_modules && currentUser.allowed_modules.length > 0)
    ? currentUser.allowed_modules
    : (currentOrg?.modules && currentOrg.modules.length > 0 ? currentOrg.modules : ['dashboard', 'students', 'staff', 'structure', 'attendance', 'settings']);

  const isCompany = 
    currentOrg?.org_type === 'company' || 
    currentOrg?.org_type === 'office' || 
    currentOrg?.org_type === 'business' || 
    currentOrg?.org_type === 'enterprise' || 
    (!rawModules.includes('students') && userRole !== 'tutor');

  // Role-based visibility
  const canViewDashboard = (isAdmin || rawModules.includes('dashboard') || userRole === 'direktor') && userRole !== 'otdel_kadr';
  const canViewStudents = !isCompany && (isAdmin || rawModules.includes('students')) && userRole !== 'otdel_kadr' && userRole !== 'buxgalter';
  const canViewStaff = isAdmin || rawModules.includes('staff') || userRole === 'direktor' || userRole === 'buxgalter' || userRole === 'otdel_kadr';
  const canViewStructure = !isCompany 
    ? ((isAdmin || rawModules.includes('structure')) && userRole !== 'otdel_kadr') 
    : (isAdmin || userRole === 'direktor' || rawModules.includes('structure'));
  const canViewAttendance = isAdmin || rawModules.includes('attendance') || userRole === 'direktor' || userRole === 'buxgalter' || userRole === 'otdel_kadr';
  const canViewSettings = isAdmin || rawModules.includes('settings');

  const getRoleLabel = (role?: string) => {
    switch (role) {
      case 'superadmin': return '👑 Super Admin';
      case 'admin': return isCompany ? '🛡️ Administrator' : '🛡️ Bosh Admin';
      case 'direktor': return '👔 Bosh Direktor';
      case 'buxgalter': return '🧮 Bosh Buxgalter';
      case 'otdel_kadr': return '💼 Otdel Kadr (HR)';
      case 'tutor': return '👨‍🏫 Guruh Tyutori';
      case 'dekanat': return '🏛️ Dekanat Mas\'uli';
      case 'qorovul': return '🚪 Nazoratchi (Qorovul)';
      default: return role || 'Foydalanuvchi';
    }
  };

  useEffect(() => {
    if (!authToken || !currentUser) return;
    
    const isTabPermitted = (tab: string) => {
      if (tab === 'dashboard') return canViewDashboard;
      if (tab === 'students') return canViewStudents;
      if (tab === 'staff') return canViewStaff;
      if (tab === 'structure') return canViewStructure;
      if (tab === 'attendance' || tab === 'attendance_settings') return canViewAttendance;
      if (tab === 'settings') return canViewSettings;
      return true;
    };

    if (!isTabPermitted(activeTab)) {
      if (canViewStaff) {
        setActiveTab('staff');
      } else if (canViewAttendance) {
        setActiveTab('attendance');
      } else if (canViewStudents) {
        setActiveTab('students');
      } else if (canViewDashboard) {
        setActiveTab('dashboard');
      }
    }
  }, [authToken, currentUser, activeTab, canViewDashboard, canViewStudents, canViewStaff, canViewStructure, canViewAttendance, canViewSettings]);

  useEffect(() => {
    if (!canViewStudents && attendanceSubTab === 'assign_students') {
      setAttendanceSubTab('assign_staff');
    }
  }, [canViewStudents, attendanceSubTab]);

  // Agar foydalanuvchi tizimga kirmagan bo'lsa - Login sahifasini ko'rsatish
  if (!authToken) {
    return (
      <LoginView 
        onLoginSuccess={(auth) => {
          setAuthToken(auth.token);
          setCurrentUser(auth.user);
          if (auth.organization) {
            setCurrentOrg(auth.organization);
          }
          loadData(true);
        }} 
      />
    );
  }

  return (
    <div className="flex h-screen bg-slate-100 text-slate-800 overflow-hidden font-sans">
      
      {/* Mobile Backdrop */}
      {sidebarOpen && (
        <div 
          onClick={() => setSidebarOpen(false)} 
          className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-40 md:hidden transition-opacity" 
        />
      )}

      {/* ======================================================== */}
      {/* 1. CHAP SIDEBAR MENU (Burgood B2B uslubidagi dizayn)      */}
      {/* ======================================================== */}
      <aside className={`fixed inset-y-0 left-0 z-50 w-72 max-w-[85vw] bg-[#0a1122] border-r border-[#15233e] flex flex-col justify-between shrink-0 select-none transition-transform duration-300 md:static md:w-64 md:translate-x-0 ${
        sidebarOpen ? 'translate-x-0 shadow-2xl' : '-translate-x-full'
      }`}>
        <div>
          {/* Logo & Brand Header */}
          <div className="px-5 py-5 border-b border-[#15233e] flex items-center justify-between">
            <div className="flex items-center gap-3 min-w-0">
              <div className="w-11 h-11 rounded-xl bg-[#0e1b38] border border-cyan-500/30 flex items-center justify-center p-1.5 shadow-lg shadow-cyan-950/50 shrink-0">
                <img 
                  src={currentOrg?.logo_url || "/logo.png"} 
                  alt="Logo" 
                  className="w-full h-full object-contain" 
                  onError={(e) => {
                    (e.target as HTMLImageElement).src = "/logo.png";
                  }}
                />
              </div>
              <div className="overflow-hidden min-w-0">
                <h1 className="font-extrabold text-[15px] tracking-tight text-white flex items-center gap-1 truncate" title={currentOrg?.name || "Burgood"}>
                  {currentOrg?.name || "Burgood"}
                </h1>
                <span className="text-[10px] uppercase font-bold tracking-widest text-cyan-400 block mt-0.5">
                  ACCESS CONTROL
                </span>
              </div>
            </div>
            {/* Close button for mobile */}
            <button 
              onClick={() => setSidebarOpen(false)}
              className="md:hidden text-slate-400 hover:text-white p-1 rounded-lg hover:bg-[#121f3a] transition"
            >
              <X size={20} />
            </button>
          </div>

          {/* Active Operating Mode Pill */}
          <div className="mx-3 mt-3 px-3 py-2 rounded-xl bg-[#091224] border border-[#16274a] flex items-center justify-between text-xs">
            <div className="flex items-center gap-2">
              <span className={`w-2 h-2 rounded-full ${isCompany ? 'bg-emerald-400' : 'bg-[#0084ff]'} animate-pulse`} />
              <span className="font-bold text-slate-200">
                {isCompany ? "🏢 Ofis & Idora" : "🎓 Ta'lim & OTM"}
              </span>
            </div>
            {isAdmin && (
              <button
                onClick={() => { setActiveTab('settings'); setSidebarOpen(false); }}
                title="Rejimni o'zgartirish yoki sozlash"
                className="text-[11px] text-cyan-400 hover:text-cyan-300 font-semibold"
              >
                Rejim &rarr;
              </button>
            )}
          </div>

          {/* Navigation Links: 1. Asosiy, 2. Talabalar, 3. Xodimlar, 4. Kafedra & Guruhlar, 5. Davomat, 6. Sozlamalar */}
          <nav className="p-3 space-y-1.5 mt-2">
            
            {/* 1. Asosiy Panel */}
            {canViewDashboard && (
              <button
                onClick={() => { setActiveTab('dashboard'); setSidebarOpen(false); }}
                className={`w-full flex items-center gap-3 px-3.5 py-3 rounded-xl text-sm font-semibold transition-all duration-200 ${
                  activeTab === 'dashboard'
                    ? 'bg-[#0084ff] text-white shadow-lg shadow-[#0084ff]/30 font-bold'
                    : 'text-slate-400 hover:text-slate-100 hover:bg-[#121f3a]'
                }`}
              >
                <LayoutDashboard size={19} className={activeTab === 'dashboard' ? 'text-white' : 'text-slate-400'} />
                <span>Asosiy Panel</span>
              </button>
            )}

            {/* 2. Talabalar */}
            {canViewStudents && (
              <button
                onClick={() => { setActiveTab('students'); setSidebarOpen(false); }}
                className={`w-full flex items-center justify-between px-3.5 py-3 rounded-xl text-sm font-semibold transition-all duration-200 ${
                  activeTab === 'students'
                    ? 'bg-[#0084ff] text-white shadow-lg shadow-[#0084ff]/30 font-bold'
                    : 'text-slate-400 hover:text-slate-100 hover:bg-[#121f3a]'
                }`}
              >
                <div className="flex items-center gap-3">
                  <GraduationCap size={19} className={activeTab === 'students' ? 'text-white' : 'text-slate-400'} />
                  <span>Talabalar</span>
                </div>
                <span className={`text-[11px] px-2 py-0.5 rounded-full font-mono font-bold ${
                  activeTab === 'students' ? 'bg-white/20 text-white' : 'bg-[#15233e] text-cyan-400'
                }`}>
                  {studentCount}
                </span>
              </button>
            )}

            {/* 3. Xodimlar */}
            {canViewStaff && (
              <button
                onClick={() => { setActiveTab('staff'); setSidebarOpen(false); }}
                className={`w-full flex items-center justify-between px-3.5 py-3 rounded-xl text-sm font-semibold transition-all duration-200 ${
                  activeTab === 'staff'
                    ? 'bg-[#0084ff] text-white shadow-lg shadow-[#0084ff]/30 font-bold'
                    : 'text-slate-400 hover:text-slate-100 hover:bg-[#121f3a]'
                }`}
              >
                <div className="flex items-center gap-3">
                  <Briefcase size={19} className={activeTab === 'staff' ? 'text-white' : 'text-slate-400'} />
                  <span>Xodimlar</span>
                </div>
                <span className={`text-[11px] px-2 py-0.5 rounded-full font-mono font-bold ${
                  activeTab === 'staff' ? 'bg-white/20 text-white' : 'bg-[#15233e] text-slate-400'
                }`}>
                  {staffCount}
                </span>
              </button>
            )}

            {/* 4. Kafedra & Guruhlar / Bo'limlar */}
            {canViewStructure && (
              <button
                onClick={() => { setActiveTab('structure'); setSidebarOpen(false); }}
                className={`w-full flex items-center justify-between px-3.5 py-3 rounded-xl text-sm font-semibold transition-all duration-200 ${
                  activeTab === 'structure'
                    ? 'bg-[#0084ff] text-white shadow-lg shadow-[#0084ff]/30 font-bold'
                    : 'text-slate-400 hover:text-slate-100 hover:bg-[#121f3a]'
                }`}
              >
                <div className="flex items-center gap-3">
                  <Landmark size={19} className={activeTab === 'structure' ? 'text-white' : 'text-slate-400'} />
                  <span>{isCompany ? "Bo'limlar" : "Kafedra & Guruhlar"}</span>
                </div>
                <span className={`text-[11px] px-2 py-0.5 rounded-full font-mono font-bold ${
                  activeTab === 'structure' ? 'bg-white/20 text-white' : 'bg-[#15233e] text-slate-400'
                }`}>
                  {isCompany ? departments.filter(d => d.type === 'division').length : groups.length}
                </span>
              </button>
            )}

            {/* 5. Attendance Settings & Davomat Accordion */}
            {canViewAttendance && (
              <div className="space-y-1">
                <button
                  onClick={() => {
                    setAttendanceMenuOpen(prev => !prev);
                    if (activeTab !== 'attendance' && activeTab !== 'attendance_settings') {
                      setActiveTab('attendance_settings');
                    }
                  }}
                  className={`w-full flex items-center justify-between px-3.5 py-3 rounded-xl text-sm font-semibold transition-all duration-200 ${
                    activeTab === 'attendance' || activeTab === 'attendance_settings'
                      ? 'bg-[#121f3a] text-white font-bold'
                      : 'text-slate-400 hover:text-slate-100 hover:bg-[#121f3a]'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <CalendarDays size={19} className={activeTab === 'attendance' || activeTab === 'attendance_settings' ? 'text-white' : 'text-slate-400'} />
                    <span>{isCompany ? "Davomat & Tabel" : "Attendance Settings"}</span>
                  </div>
                  <ChevronDown 
                    size={16} 
                    className={`transition-transform duration-200 text-slate-400 ${
                      attendanceMenuOpen ? 'rotate-180 text-white' : ''
                    }`} 
                  />
                </button>

                {/* Expandable Submenu */}
                {attendanceMenuOpen && (
                  <div className="pl-2 pr-1 py-1.5 space-y-1 bg-[#091224]/80 rounded-xl border border-[#16274a]/60">
                    {/* Sub-item: Davomat Jurnali */}
                    <button
                      onClick={() => { 
                        setActiveTab('attendance'); 
                        setSidebarOpen(false); 
                      }}
                      className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium transition ${
                        activeTab === 'attendance'
                          ? 'bg-[#0084ff] text-white font-bold shadow-sm'
                          : 'text-slate-400 hover:text-white hover:bg-[#121f3a]'
                      }`}
                    >
                      <Clock size={16} className={activeTab === 'attendance' ? 'text-white' : 'text-slate-400'} />
                      <span>Davomat Jurnali (Logs)</span>
                    </button>

                    {/* Sub-item: Smenalar (Ish vaqti) */}
                    <button
                      onClick={() => { 
                        setAttendanceSubTab('shifts');
                        setActiveTab('attendance_settings'); 
                        setSidebarOpen(false); 
                      }}
                      className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium transition ${
                        activeTab === 'attendance_settings' && attendanceSubTab === 'shifts'
                          ? 'bg-[#0084ff] text-white font-bold shadow-sm'
                          : 'text-slate-400 hover:text-white hover:bg-[#121f3a]'
                      }`}
                    >
                      <Timer size={16} className={activeTab === 'attendance_settings' && attendanceSubTab === 'shifts' ? 'text-white' : 'text-slate-400'} />
                      <span>Smenalar (Ish vaqti)</span>
                    </button>

                    {/* Sub-item: Haftalik Jadvallar */}
                    <button
                      onClick={() => { 
                        setAttendanceSubTab('schedules');
                        setActiveTab('attendance_settings'); 
                        setSidebarOpen(false); 
                      }}
                      className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium transition ${
                        activeTab === 'attendance_settings' && attendanceSubTab === 'schedules'
                          ? 'bg-[#0084ff] text-white font-bold shadow-sm'
                          : 'text-slate-400 hover:text-white hover:bg-[#121f3a]'
                      }`}
                    >
                      <Calendar size={16} className={activeTab === 'attendance_settings' && attendanceSubTab === 'schedules' ? 'text-white' : 'text-slate-400'} />
                      <span>Haftalik Jadvallar</span>
                    </button>

                    {/* Sub-item: Xodimlarga Biriktirish */}
                    <button
                      onClick={() => { 
                        setAttendanceSubTab('assign_staff');
                        setActiveTab('attendance_settings'); 
                        setSidebarOpen(false); 
                      }}
                      className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium transition ${
                        activeTab === 'attendance_settings' && attendanceSubTab === 'assign_staff'
                          ? 'bg-[#0084ff] text-white font-bold shadow-sm'
                          : 'text-slate-400 hover:text-white hover:bg-[#121f3a]'
                      }`}
                    >
                      <Briefcase size={16} className={activeTab === 'attendance_settings' && attendanceSubTab === 'assign_staff' ? 'text-white' : 'text-slate-400'} />
                      <span>Xodimlarga Biriktirish</span>
                    </button>

                    {/* Sub-item: Talabalar & Guruhlarga Biriktirish */}
                    {canViewStudents && (
                      <button
                        onClick={() => { 
                          setAttendanceSubTab('assign_students');
                          setActiveTab('attendance_settings'); 
                          setSidebarOpen(false); 
                        }}
                        className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium transition ${
                          activeTab === 'attendance_settings' && attendanceSubTab === 'assign_students'
                            ? 'bg-[#0084ff] text-white font-bold shadow-sm'
                            : 'text-slate-400 hover:text-white hover:bg-[#121f3a]'
                        }`}
                      >
                        <GraduationCap size={16} className={activeTab === 'attendance_settings' && attendanceSubTab === 'assign_students' ? 'text-white' : 'text-slate-400'} />
                        <span>Talaba & Guruhlarga</span>
                      </button>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* 6. Sozlamalar (Eng oxirida) */}
            {canViewSettings && (
              <button
                onClick={() => { setActiveTab('settings'); setSidebarOpen(false); }}
                className={`w-full flex items-center justify-between px-3.5 py-3 rounded-xl text-sm font-semibold transition-all duration-200 ${
                  activeTab === 'settings'
                    ? 'bg-[#0084ff] text-white shadow-lg shadow-[#0084ff]/30 font-bold'
                    : 'text-slate-400 hover:text-slate-100 hover:bg-[#121f3a]'
                }`}
              >
                <div className="flex items-center gap-3">
                  <Settings size={19} className={activeTab === 'settings' ? 'text-white' : 'text-slate-400'} />
                  <span>{isCompany ? "Turniket & Sozlamalar" : "Sozlamalar"}</span>
                </div>
                <span className={`text-[11px] px-2 py-0.5 rounded-full font-mono font-bold ${
                  activeTab === 'settings' ? 'bg-white/20 text-white' : 'bg-[#15233e] text-slate-400'
                }`}>
                  {devices.length}
                </span>
              </button>
            )}

          </nav>
        </div>

        {/* Bottom Section: Language & Admin Profile */}
        <div className="p-3 border-t border-[#15233e] space-y-3">
          {/* Language Switcher */}
          <div className="flex bg-[#070d1a] p-1 rounded-xl border border-[#15233e]">
            <button
              onClick={() => setLang('UZ')}
              className={`flex-1 py-1.5 text-xs font-bold rounded-lg transition ${
                lang === 'UZ' ? 'bg-[#0084ff] text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              UZ
            </button>
            <button
              onClick={() => setLang('RU')}
              className={`flex-1 py-1.5 text-xs font-bold rounded-lg transition ${
                lang === 'RU' ? 'bg-[#0084ff] text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              RU
            </button>
          </div>

          {/* User profile capsule */}
          <div className="flex items-center gap-3 p-2.5 rounded-xl bg-[#0d162d] border border-[#172747]">
            <div className="w-9 h-9 rounded-full bg-[#0084ff] flex items-center justify-center font-bold text-white text-sm shadow-md uppercase shrink-0">
              {currentUser?.username?.[0] || 'A'}
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-xs font-bold text-white truncate">
                {currentUser?.full_name || currentUser?.username || 'Administrator'}
              </div>
              <div className="text-[11px] text-cyan-400 font-semibold truncate">
                {getRoleLabel(currentUser?.role)}
              </div>
              <div className="text-[10px] text-slate-400 truncate">
                {currentOrg?.name || 'Burgood Access'}
              </div>
            </div>
            <button 
              onClick={handleLogout} 
              title="Chiqish (Logout)" 
              className="text-slate-400 hover:text-rose-400 p-1.5 rounded-lg hover:bg-white/5 transition shrink-0"
            >
              <LogOut size={16} />
            </button>
          </div>
        </div>
      </aside>

      {/* ======================================================== */}
      {/* 2. O'NG ASOSIY KONTENT SOHASI (Yorug', ko'z og'ritmaydi)   */}
      {/* ======================================================== */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden bg-[#f4f6fa]">
        {/* Mobile Top Header Navigation */}
        <header className="md:hidden flex items-center justify-between bg-[#0a1122] text-white px-4 py-3.5 border-b border-[#15233e] shadow-lg shrink-0 z-30">
          <div className="flex items-center gap-3 min-w-0">
            <div className="w-10 h-10 rounded-xl bg-[#0e1b38] border border-cyan-500/30 flex items-center justify-center p-1.5 shadow-md shadow-cyan-950/40 shrink-0">
              <img 
                src={currentOrg?.logo_url || "/logo.png"} 
                alt="Logo" 
                className="w-full h-full object-contain" 
                onError={(e) => {
                  (e.target as HTMLImageElement).src = "/logo.png";
                }}
              />
            </div>
            <div className="overflow-hidden min-w-0">
              <span className="font-bold text-[15px] block leading-tight truncate text-white tracking-tight">
                {currentOrg?.name || "Burgood"}
              </span>
              <span className="text-[10px] text-cyan-400 font-extrabold uppercase tracking-widest block mt-0.5">
                ACCESS CONTROL
              </span>
            </div>
          </div>
          
          {/* Hamburger Menu Tugmasi - Qulay, bosish oson va hech narsa to'sib qo'ymaydi */}
          <button 
            onClick={() => setSidebarOpen(true)}
            className="w-11 h-11 rounded-xl bg-[#121f3a] active:bg-[#1a2d52] text-cyan-400 active:scale-95 transition flex items-center justify-center border border-[#1e345e] shadow-md shrink-0 cursor-pointer"
            title="Menuni ochish"
          >
            <Menu size={22} className="text-white" />
          </button>
        </header>

        {/* Scrollable Content Body */}
        <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8 min-w-0">
          
          {activeTab === 'dashboard' && (
            <div className="space-y-7 max-w-7xl mx-auto">
              
              {/* Hero Banner */}
              <div className="bg-gradient-to-r from-[#0d1b38] via-[#0f2247] to-[#0a152d] border border-[#19305d] rounded-2xl p-7 relative overflow-hidden shadow-md">
                <div className="relative z-10 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                  <div>
                    <h2 className="text-2xl font-black text-white tracking-tight">
                      Xush kelibsiz, {currentOrg?.name || 'Burgood Access'} tizimiga!
                    </h2>
                    <p className="text-slate-300 text-sm mt-1.5 flex items-center gap-2">
                      <span className="text-cyan-400 font-medium">• {currentOrg?.name || (isCompany ? "Ofis & Korxona" : "Universitet")}</span>
                      <span className="text-slate-500">|</span>
                      <span>
                        {isCompany 
                          ? "Tashkilot bo'limlari, xodimlar va Face ID turniketlari" 
                          : "Universitet fakultetlari, kafedralari va Face ID turniketlari"}
                      </span>
                    </p>
                  </div>
                  <div className="flex gap-3">
                    <button 
                      onClick={() => setActiveTab('attendance')}
                      className="px-5 py-2.5 rounded-xl bg-[#0084ff] hover:bg-[#0073e0] text-white text-sm font-bold shadow-md shadow-[#0084ff]/30 transition flex items-center gap-2"
                    >
                      <Clock size={16} /> Davomatga o'tish
                    </button>
                  </div>
                </div>
                {/* Background decorative shield glow */}
                <div className="absolute right-0 top-0 bottom-0 w-80 opacity-10 pointer-events-none flex items-center justify-center">
                  <img 
                    src={currentOrg?.logo_url || "/logo.png"} 
                    alt="" 
                    className="w-64 h-64 object-contain filter brightness-200" 
                    onError={(e) => {
                      (e.target as HTMLImageElement).src = "/logo.png";
                    }}
                  />
                </div>
              </div>

              {/* KPI Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                
                <div className="bg-white border border-slate-200/80 p-5 rounded-2xl flex items-center justify-between shadow-sm hover:shadow transition">
                  <div>
                    <div className="text-xs font-semibold text-slate-500">
                      {isCompany ? "Ofisda hozir" : "Universitetda hozir"}
                    </div>
                    <div className="text-2xl font-black text-slate-900 mt-1 font-mono">
                      {stats?.unique_present ?? 0} <span className="text-xs font-normal text-slate-500">kishi</span>
                    </div>
                    <div className="text-[11px] text-slate-400 mt-1">
                      {isCompany ? `Jami xodimlar: ${staffCount} ta` : `Jami talaba va xodim: ${stats?.total_users ?? 0}`}
                    </div>
                  </div>
                  <div className="w-12 h-12 rounded-xl bg-blue-50 text-[#0084ff] flex items-center justify-center">
                    <UserCheck size={24} />
                  </div>
                </div>

                <div className="bg-white border border-slate-200/80 p-5 rounded-2xl flex items-center justify-between shadow-sm hover:shadow transition">
                  <div>
                    <div className="text-xs font-semibold text-slate-500">Bugungi Kirishlar</div>
                    <div className="text-2xl font-black text-emerald-600 mt-1 font-mono">
                      {stats?.today_entries ?? 0}
                    </div>
                    <div className="text-[11px] text-emerald-600/80 mt-1">Turniketdan o'tganlar</div>
                  </div>
                  <div className="w-12 h-12 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
                    <ArrowDownLeft size={24} />
                  </div>
                </div>

                <div className="bg-white border border-slate-200/80 p-5 rounded-2xl flex items-center justify-between shadow-sm hover:shadow transition">
                  <div>
                    <div className="text-xs font-semibold text-slate-500">
                      {isCompany ? "Bo'limlar Soni" : "Guruhlar Soni"}
                    </div>
                    <div className="text-2xl font-black text-amber-600 mt-1 font-mono">
                      {isCompany 
                        ? (departments.filter(d => d.type === 'division').length || departments.length) 
                        : groups.length}
                    </div>
                    <div className="text-[11px] text-amber-600/80 mt-1">
                      {isCompany ? "Tashkiliy bo'lim va filiallar" : "Tyutorlar biriktirilgan"}
                    </div>
                  </div>
                  <div className="w-12 h-12 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center">
                    {isCompany ? <Building2 size={24} /> : <Landmark size={24} />}
                  </div>
                </div>

                <div className="bg-white border border-slate-200/80 p-5 rounded-2xl flex items-center justify-between shadow-sm hover:shadow transition">
                  <div>
                    <div className="text-xs font-semibold text-slate-500">Face ID Terminallar</div>
                    <div className="text-2xl font-black text-slate-900 mt-1 font-mono">
                      {stats?.online_devices ?? 0} <span className="text-xs font-normal text-slate-500">/ {stats?.total_devices ?? 0}</span>
                    </div>
                    <div className="text-[11px] text-[#0084ff] font-medium mt-1">Qurilmalar holati</div>
                  </div>
                  <div className="w-12 h-12 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center">
                    <Cpu size={24} />
                  </div>
                </div>

              </div>

              {/* Real-time Stream & Connected Devices View */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                
                {/* Live Face Turnstile Stream */}
                <div className="lg:col-span-2 bg-white border border-slate-200/80 rounded-2xl p-6 shadow-sm">
                  <div className="flex justify-between items-center mb-5 pb-3 border-b border-slate-100">
                    <div className="flex items-center gap-2">
                      <Radio className="text-rose-500 animate-pulse" size={20} />
                      <h3 className="font-bold text-slate-900 text-base">Jonli Turniket Oqimi (Live Real-time Feed)</h3>
                    </div>
                    <span className="text-xs text-slate-400 font-medium">Real vaqt</span>
                  </div>

                  <div className="space-y-3">
                    {liveLogs.map((item) => (
                      <div 
                        key={item.id}
                        className="bg-slate-50 border border-slate-200/70 p-3.5 rounded-xl flex items-center justify-between hover:border-slate-300 transition"
                      >
                        <div className="flex items-center gap-3.5">
                          <div className="w-11 h-11 rounded-full bg-white border border-slate-200 flex items-center justify-center overflow-hidden shrink-0 shadow-sm">
                            {item.photo_path ? (
                              <img src={item.photo_path} alt={item.user_name} className="w-full h-full object-cover" />
                            ) : (
                              <Users size={18} className="text-slate-400" />
                            )}
                          </div>
                          <div>
                            <div className="font-bold text-sm text-slate-900">{item.user_name || "Noma'lum Shaxs"}</div>
                            <div className="flex items-center gap-2 text-xs text-slate-500 mt-0.5">
                              <span className="font-mono text-[#0084ff] font-bold">{item.employee_no || "-"}</span>
                              {item.group_name && <span>• {item.group_name}</span>}
                              <span>• {item.device_name}</span>
                            </div>
                          </div>
                        </div>

                        <div className="text-right">
                          <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold ${
                            item.direction === 'entry'
                              ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                              : item.direction === 'break_out'
                              ? 'bg-amber-50 text-amber-700 border border-amber-200'
                              : item.direction === 'break_in'
                              ? 'bg-sky-50 text-sky-700 border border-sky-200'
                              : 'bg-rose-50 text-rose-700 border border-rose-200'
                          }`}>
                            {item.direction === 'entry' || item.direction === 'break_in' ? <ArrowDownLeft size={12} /> : <ArrowUpRight size={12} />}
                            {item.direction === 'entry' ? 'KIRISH' : item.direction === 'break_out' ? 'TUSHLIK (KETDI)' : item.direction === 'break_in' ? 'TUSHLIK (QAYTDI)' : 'CHIQISH'}
                          </span>
                          <div className="text-[11px] text-slate-400 font-mono mt-1">{item.event_time}</div>
                        </div>
                      </div>
                    ))}

                    {liveLogs.length === 0 && (
                      <div className="py-16 text-center text-slate-400 text-sm">
                        Hozircha o'tish yozuvi kelmadi. Face ID terminallaridan o'tish kutilmoqda...
                      </div>
                    )}
                  </div>
                </div>

                {/* Right side: Terminals quick list & info */}
                <div className="bg-white border border-slate-200/80 rounded-2xl p-6 flex flex-col justify-between shadow-sm">
                  <div>
                    <div className="flex justify-between items-center mb-4 pb-3 border-b border-slate-100">
                      <h3 className="font-bold text-slate-900 text-base">Ulangan Terminallar</h3>
                      <button 
                        onClick={() => setActiveTab('settings')}
                        className="text-xs text-[#0084ff] hover:underline font-bold"
                      >
                        Sozlamalar &rarr;
                      </button>
                    </div>

                    <div className="space-y-3">
                      {devices.slice(0, 5).map((d) => (
                        <div key={d.id} className="bg-slate-50 border border-slate-200/70 p-3 rounded-xl flex items-center justify-between">
                          <div>
                            <div className="font-bold text-xs text-slate-800 flex items-center gap-2">
                              <span className={`w-2 h-2 rounded-full ${d.status === 'online' ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'}`} />
                              {d.name}
                            </div>
                            <div className="text-[11px] text-slate-500 font-mono mt-0.5">{d.ip_address} ({d.direction})</div>
                          </div>
                          <span className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase ${
                            d.status === 'online' ? 'bg-emerald-50 text-emerald-700' : 'bg-rose-50 text-rose-700'
                          }`}>
                            {d.status}
                          </span>
                        </div>
                      ))}

                      {devices.length === 0 && (
                        <div className="py-8 text-center text-slate-400 text-xs">
                          Terminallar kiritilmagan.
                        </div>
                      )}
                    </div>
                  </div>
                </div>

              </div>

            </div>
          )}

          {activeTab === 'students' && (
            <StudentsView 
              users={users} 
              groups={groups} 
              departments={departments} 
              devices={devices}
              onRefresh={loadData} 
            />
          )}

          {activeTab === 'staff' && (
            <StaffView 
              users={users} 
              departments={departments} 
              devices={devices}
              onRefresh={loadData} 
              isCompany={isCompany}
            />
          )}

          {activeTab === 'structure' && (
            <StructureView
              faculties={faculties}
              departments={departments}
              groups={groups}
              tutors={tutors}
              onRefresh={loadData}
              isCompany={isCompany}
            />
          )}

          {activeTab === 'attendance' && (
            <AttendanceView 
              logs={logs} 
              onRefresh={loadData} 
              isCompany={isCompany}
              onNavigateToSettings={() => {
                setAttendanceMenuOpen(true);
                setActiveTab('attendance_settings');
              }}
            />
          )}

          {activeTab === 'attendance_settings' && (
            <AttendanceSettingsView
              initialSubTab={attendanceSubTab}
              onNavigateToLogs={() => {
                setActiveTab('attendance');
              }}
              isCompany={isCompany}
            />
          )}

          {activeTab === 'settings' && (
            <SettingsView 
              devices={devices} 
              onRefresh={loadData} 
              currentOrg={currentOrg}
              onOrgUpdated={(newOrg) => {
                localStorage.setItem('burgood_org', JSON.stringify(newOrg));
                setCurrentOrg(newOrg);
                loadData();
              }}
              isCompany={isCompany}
            />
          )}

        </main>
      </div>

      {/* Dastlabki Yuklanish (Preloader) Oynasi - Burgood Logo va animatsiyasi */}
      {initialLoading && (
        <div 
          className={`fixed inset-0 z-[99999] flex flex-col items-center justify-center transition-opacity duration-500 ease-out select-none ${
            fadeExit ? 'opacity-0 pointer-events-none' : 'opacity-100'
          }`}
          style={{ background: 'radial-gradient(circle at center, #0f1f3d 0%, #070c18 70%)' }}
        >
          <div className="relative w-28 h-28 flex items-center justify-center mb-6">
            <div className="absolute -inset-6 rounded-full border border-cyan-400/25 border-dashed animate-[spin_12s_linear_infinite]" />
            <div className="absolute -inset-3 rounded-full border-2 border-[#0084ff]/40 shadow-[0_0_25px_rgba(0,132,255,0.4)] animate-pulse" />
            <img 
              src="/burgood_shield.png" 
              alt="Burgood Shield" 
              className="w-18 h-18 object-contain drop-shadow-[0_0_20px_rgba(0,132,255,0.6)] animate-bounce"
              style={{ animationDuration: '3s' }}
            />
          </div>

          <h1 className="text-2xl font-black tracking-tight text-white mb-1.5 flex items-center gap-1.5">
            BURGOOD <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#0084ff] to-cyan-400">ACCESS</span>
          </h1>
          <p className="text-[11px] font-bold tracking-[0.25em] text-cyan-400 uppercase mb-7 opacity-95">
            Face ID Xavfsizlik Tizimi
          </p>

          <div className="w-56 h-1 bg-white/10 rounded-full overflow-hidden relative shadow-[0_0_10px_rgba(0,132,255,0.2)]">
            <div className="absolute h-full w-1/2 bg-gradient-to-r from-transparent via-[#0084ff] to-cyan-300 rounded-full animate-progress-slide" />
          </div>

          <p className="mt-3.5 text-xs text-slate-400 font-medium tracking-wide animate-pulse">
            Tizim yuklanmoqda, kuting...
          </p>
        </div>
      )}

    </div>
  );
}

export default App;
