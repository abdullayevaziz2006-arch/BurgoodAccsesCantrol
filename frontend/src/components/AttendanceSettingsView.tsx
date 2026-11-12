import React, { useState, useEffect } from 'react';
import { 
  Shift, Schedule, ScheduleAssignmentsSummary 
} from '../types';
import { 
  getShifts, createShift, updateShift, deleteShift,
  getSchedules, createSchedule, updateSchedule, deleteSchedule,
  assignSchedule, getScheduleAssignments
} from '../api';
import { 
  Calendar, Clock, CalendarDays, Plus, Trash2, Edit2, 
  CheckCircle, AlertCircle, RefreshCw, Users,
  CheckSquare, Square
} from 'lucide-react';

interface AttendanceSettingsProps {
  initialSubTab?: 'shifts' | 'schedules' | 'assign_staff' | 'assign_students';
  onNavigateToLogs?: () => void;
  isCompany?: boolean;
}

export const AttendanceSettingsView: React.FC<AttendanceSettingsProps> = ({ 
  initialSubTab = 'shifts',
  onNavigateToLogs,
  isCompany
}) => {
  const [activeTab, setActiveTab] = useState<'shifts' | 'schedules' | 'assign_staff' | 'assign_students'>(
    isCompany && initialSubTab === 'assign_students' ? 'assign_staff' : initialSubTab
  );
  const [shifts, setShifts] = useState<Shift[]>([]);
  const [schedules, setSchedules] = useState<Schedule[]>([]);
  const [assignments, setAssignments] = useState<ScheduleAssignmentsSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Modal states for Shifts
  const [showShiftModal, setShowShiftModal] = useState(false);
  const [editingShift, setEditingShift] = useState<Shift | null>(null);
  const [shiftName, setShiftName] = useState('');
  const [shiftStart, setShiftStart] = useState('08:30');
  const [shiftEnd, setShiftEnd] = useState('17:30');
  const [shiftLunchStart, setShiftLunchStart] = useState('12:00');
  const [shiftLunchEnd, setShiftLunchEnd] = useState('13:00');
  const [shiftLateTol, setShiftLateTol] = useState(15);
  const [shiftEarlyTol, setShiftEarlyTol] = useState(15);
  const [shiftColor, setShiftColor] = useState('#0084ff');

  // Modal states for Schedules
  const [showScheduleModal, setShowScheduleModal] = useState(false);
  const [editingSchedule, setEditingSchedule] = useState<Schedule | null>(null);
  const [schName, setSchName] = useState('');
  const [schDesc, setSchDesc] = useState('');
  const [dayShifts, setDayShifts] = useState<{ [key: string]: number | null }>({
    monday: null,
    tuesday: null,
    wednesday: null,
    thursday: null,
    friday: null,
    saturday: null,
    sunday: null,
  });

  // Assignment states
  const [selectedStaffIds, setSelectedStaffIds] = useState<number[]>([]);
  const [selectedGroupIds, setSelectedGroupIds] = useState<number[]>([]);
  const [targetScheduleId, setTargetScheduleId] = useState<number | null>(null);
  const [searchAssign, setSearchAssign] = useState('');

  const loadAll = async () => {
    setLoading(true);
    try {
      const [sh, sc, asg] = await Promise.all([
        getShifts(),
        getSchedules(),
        getScheduleAssignments()
      ]);
      setShifts(sh);
      setSchedules(sc);
      setAssignments(asg);
    } catch (err: any) {
      console.error(err);
      setMsg({ type: 'error', text: "Ma'lumotlarni yuklashda xatolik yuz berdi" });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAll();
  }, []);

  useEffect(() => {
    if (initialSubTab) {
      if (isCompany && initialSubTab === 'assign_students') {
        setActiveTab('assign_staff');
      } else {
        setActiveTab(initialSubTab);
      }
    }
  }, [initialSubTab, isCompany]);

  const showNotification = (text: string, type: 'success' | 'error' = 'success') => {
    setMsg({ type, text });
    setTimeout(() => setMsg(null), 4000);
  };

  // ========================================================
  // SHIFTS HANDLERS
  // ========================================================
  const openNewShiftModal = () => {
    setEditingShift(null);
    setShiftName('');
    setShiftStart('08:30');
    setShiftEnd('17:30');
    setShiftLunchStart('12:00');
    setShiftLunchEnd('13:00');
    setShiftLateTol(15);
    setShiftEarlyTol(15);
    setShiftColor('#0084ff');
    setShowShiftModal(true);
  };

  const openEditShiftModal = (s: Shift) => {
    setEditingShift(s);
    setShiftName(s.name);
    setShiftStart(s.start_time);
    setShiftEnd(s.end_time);
    setShiftLunchStart(s.lunch_start || '12:00');
    setShiftLunchEnd(s.lunch_end || '13:00');
    setShiftLateTol(s.late_tolerance_minutes);
    setShiftEarlyTol(s.early_leave_tolerance_minutes);
    setShiftColor(s.color || '#0084ff');
    setShowShiftModal(true);
  };

  const handleSaveShift = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingShift) {
        await updateShift(editingShift.id, {
          name: shiftName,
          start_time: shiftStart,
          end_time: shiftEnd,
          lunch_start: shiftLunchStart,
          lunch_end: shiftLunchEnd,
          late_tolerance_minutes: shiftLateTol,
          early_leave_tolerance_minutes: shiftEarlyTol,
          color: shiftColor
        });
        showNotification("Smena muvaffaqiyatli yangilandi");
      } else {
        await createShift({
          name: shiftName,
          start_time: shiftStart,
          end_time: shiftEnd,
          lunch_start: shiftLunchStart,
          lunch_end: shiftLunchEnd,
          late_tolerance_minutes: shiftLateTol,
          early_leave_tolerance_minutes: shiftEarlyTol,
          color: shiftColor
        });
        showNotification("Yangi smena muvaffaqiyatli qo'shildi");
      }
      setShowShiftModal(false);
      loadAll();
    } catch (err: any) {
      showNotification("Smenani saqlashda xatolik", 'error');
    }
  };

  const handleDeleteShift = async (id: number) => {
    if (!confirm("Haqiqatan ham bu smenani o'chirmoqchimisiz?")) return;
    try {
      await deleteShift(id);
      showNotification("Smena o'chirildi");
      loadAll();
    } catch (err: any) {
      showNotification("O'chirishda xatolik", 'error');
    }
  };

  // ========================================================
  // SCHEDULES HANDLERS
  // ========================================================
  const openNewScheduleModal = () => {
    setEditingSchedule(null);
    setSchName('');
    setSchDesc('');
    // Default to first shift for Monday-Friday if exists
    const defaultShiftId = shifts.length > 0 ? shifts[0].id : null;
    setDayShifts({
      monday: defaultShiftId,
      tuesday: defaultShiftId,
      wednesday: defaultShiftId,
      thursday: defaultShiftId,
      friday: defaultShiftId,
      saturday: null,
      sunday: null,
    });
    setShowScheduleModal(true);
  };

  const openEditScheduleModal = (sc: Schedule) => {
    setEditingSchedule(sc);
    setSchName(sc.name);
    setSchDesc(sc.description || '');
    setDayShifts({
      monday: sc.monday_shift_id ?? null,
      tuesday: sc.tuesday_shift_id ?? null,
      wednesday: sc.wednesday_shift_id ?? null,
      thursday: sc.thursday_shift_id ?? null,
      friday: sc.friday_shift_id ?? null,
      saturday: sc.saturday_shift_id ?? null,
      sunday: sc.sunday_shift_id ?? null,
    });
    setShowScheduleModal(true);
  };

  const handleSaveSchedule = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const payload = {
        name: schName,
        description: schDesc,
        monday_shift_id: dayShifts.monday,
        tuesday_shift_id: dayShifts.tuesday,
        wednesday_shift_id: dayShifts.wednesday,
        thursday_shift_id: dayShifts.thursday,
        friday_shift_id: dayShifts.friday,
        saturday_shift_id: dayShifts.saturday,
        sunday_shift_id: dayShifts.sunday,
      };

      if (editingSchedule) {
        await updateSchedule(editingSchedule.id, payload);
        showNotification("Haftalik jadval yangilandi");
      } else {
        await createSchedule(payload);
        showNotification("Yangi haftalik jadval yaratildi");
      }
      setShowScheduleModal(false);
      loadAll();
    } catch (err: any) {
      showNotification("Jadvalni saqlashda xatolik", 'error');
    }
  };

  const handleDeleteSchedule = async (id: number) => {
    if (!confirm("Haqiqatan ham bu jadvalni o'chirmoqchimisiz?")) return;
    try {
      await deleteSchedule(id);
      showNotification("Jadval o'chirildi");
      loadAll();
    } catch (err: any) {
      showNotification("O'chirishda xatolik", 'error');
    }
  };

  // ========================================================
  // ASSIGNMENTS HANDLERS
  // ========================================================
  const handleAssignToStaff = async () => {
    if (selectedStaffIds.length === 0) {
      showNotification("Kamida bitta xodimni tanlang", 'error');
      return;
    }
    try {
      await assignSchedule({
        schedule_id: targetScheduleId,
        user_ids: selectedStaffIds
      });
      showNotification(`${selectedStaffIds.length} ta xodimga jadval biriktirildi`);
      setSelectedStaffIds([]);
      loadAll();
    } catch (err: any) {
      showNotification("Jadval biriktirishda xatolik", 'error');
    }
  };

  const handleAssignToGroups = async () => {
    if (selectedGroupIds.length === 0) {
      showNotification("Kamida bitta guruhni tanlang", 'error');
      return;
    }
    try {
      await assignSchedule({
        schedule_id: targetScheduleId,
        group_ids: selectedGroupIds
      });
      showNotification(`${selectedGroupIds.length} ta guruh va uning barcha talabalariga jadval biriktirildi`);
      setSelectedGroupIds([]);
      loadAll();
    } catch (err: any) {
      showNotification("Jadval biriktirishda xatolik", 'error');
    }
  };

  const toggleSelectAllStaff = () => {
    if (!assignments) return;
    const filtered = assignments.staff.filter(s => 
      s.full_name.toLowerCase().includes(searchAssign.toLowerCase()) ||
      s.employee_no.toLowerCase().includes(searchAssign.toLowerCase())
    );
    if (selectedStaffIds.length === filtered.length) {
      setSelectedStaffIds([]);
    } else {
      setSelectedStaffIds(filtered.map(s => s.id));
    }
  };

  const toggleSelectAllGroups = () => {
    if (!assignments) return;
    const filtered = assignments.groups.filter(g => 
      g.name.toLowerCase().includes(searchAssign.toLowerCase()) ||
      (g.direction_name && g.direction_name.toLowerCase().includes(searchAssign.toLowerCase()))
    );
    if (selectedGroupIds.length === filtered.length) {
      setSelectedGroupIds([]);
    } else {
      setSelectedGroupIds(filtered.map(g => g.id));
    }
  };

  const daysConfig = [
    { key: 'monday', label: 'Dushanba' },
    { key: 'tuesday', label: 'Seshanba' },
    { key: 'wednesday', label: 'Chorshanba' },
    { key: 'thursday', label: 'Payshanba' },
    { key: 'friday', label: 'Juma' },
    { key: 'saturday', label: 'Shanba' },
    { key: 'sunday', label: 'Yakshanba' },
  ];

  return (
    <div className="space-y-6">
      
      {/* 1. Header Banner */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-white border border-slate-200/80 p-5 sm:p-6 rounded-2xl shadow-sm">
        <div>
          <h2 className="text-xl font-bold text-slate-800 flex items-center gap-2">
            {activeTab === 'shifts' && <Clock className="text-[#0084ff]" size={24} />}
            {activeTab === 'schedules' && <CalendarDays className="text-[#0084ff]" size={24} />}
            {activeTab === 'assign_staff' && <Users className="text-[#0084ff]" size={24} />}
            {activeTab === 'assign_students' && <Calendar className="text-[#0084ff]" size={24} />}
            <span>
              {activeTab === 'shifts' && "Smenalar va Ish Vaqtlari"}
              {activeTab === 'schedules' && (isCompany ? "Haftalik Ish Jadvallari" : "Haftalik Jadvallar (Schedules)")}
              {activeTab === 'assign_staff' && (isCompany ? "Xodimlarga Ish Grafigini Biriktirish" : "Xodimlarga Jadval Biriktirish")}
              {activeTab === 'assign_students' && (!isCompany ? "Talaba & Guruhlarga Jadval Biriktirish" : "")}
            </span>
          </h2>
          <p className="text-slate-500 text-sm mt-1">
            {activeTab === 'shifts' && (isCompany ? "Xodimlar uchun ish vaqti va kechikish chegaralari" : "Xodimlar va talabalar uchun kelish-ketish vaqtlari va kechikish chegaralari")}
            {activeTab === 'schedules' && (isCompany ? "Dushanbadan yakshanbagacha xodimlar ish grafigi" : "Dushanbadan Yakshanbagacha qaysi kun qaysi smenada ishlash grafigi")}
            {activeTab === 'assign_staff' && (isCompany ? "Xodimlarni tanlab, ularga tegishli ish grafigini biriktirish" : "Xodimlarni belgilab, haftalik ish grafigini biriktirish")}
            {activeTab === 'assign_students' && (!isCompany ? "Guruhlar bo'yicha haftalik o'qish jadvallarini biriktirish" : "")}
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          {onNavigateToLogs && (
            <button 
              onClick={onNavigateToLogs}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl border border-slate-300 bg-white hover:bg-slate-50 text-slate-700 font-semibold text-sm transition"
            >
              <Clock size={16} /> Davomat Jurnali
            </button>
          )}
          <button 
            onClick={loadAll}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-sm transition"
          >
            <RefreshCw size={15} className={loading ? "animate-spin" : ""} /> Yangilash
          </button>
        </div>
      </div>

      {/* Notification Toast */}
      {msg && (
        <div className={`p-4 rounded-xl text-sm flex items-center gap-2.5 font-medium transition ${
          msg.type === 'success' ? 'bg-emerald-50 text-emerald-800 border border-emerald-200' : 'bg-rose-50 text-rose-800 border border-rose-200'
        }`}>
          {msg.type === 'success' ? <CheckCircle size={18} className="text-emerald-600 shrink-0" /> : <AlertCircle size={18} className="text-rose-600 shrink-0" />}
          <span>{msg.text}</span>
        </div>
      )}

      {/* ======================================================== */}
      {/* TAB 1: SMENALAR (SHIFTS)                                */}
      {/* ======================================================== */}
      {activeTab === 'shifts' && (
        <div className="space-y-4">
          <div className="flex justify-between items-center bg-white p-4 rounded-xl border border-slate-200">
            <div>
              <h3 className="font-bold text-slate-900 text-base">Smenalar & Ish Vaqtlari</h3>
              <p className="text-xs text-slate-500 mt-0.5">
                {isCompany ? "Xodimlar uchun kelish-ketish vaqtlari va kechikish chegaralari" : "Xodimlar va talabalar uchun kelish-ketish vaqtlari va kechikish chegaralari"}
              </p>
            </div>
            <button
              onClick={openNewShiftModal}
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-[#0084ff] hover:bg-[#0073e0] text-white font-bold text-sm shadow-md shadow-[#0084ff]/20 transition"
            >
              <Plus size={16} /> Yangi Smena Qo'shish
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {shifts.map((s) => (
              <div key={s.id} className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm hover:border-[#0084ff]/50 transition flex flex-col justify-between">
                <div>
                  <div className="flex justify-between items-start mb-3">
                    <div className="flex items-center gap-2.5">
                      <div className="w-3.5 h-3.5 rounded-full" style={{ backgroundColor: s.color || '#0084ff' }} />
                      <h4 className="font-bold text-slate-900 text-base">{s.name}</h4>
                    </div>
                  </div>

                  <div className="bg-slate-50 border border-slate-100 rounded-xl p-3.5 space-y-2 text-xs text-slate-600 mb-4 font-mono">
                    <div className="flex justify-between items-center">
                      <span className="text-slate-400">{isCompany ? "Ish Vaqti:" : "Ish/O'qish Vaqti:"}</span>
                      <span className="font-bold text-slate-900 text-sm bg-white px-2 py-0.5 rounded border border-slate-200">
                        {s.start_time} - {s.end_time}
                      </span>
                    </div>
                    <div className="flex justify-between items-center bg-amber-50/80 px-2 py-1 rounded-lg border border-amber-200/60">
                      <span className="text-amber-700 font-semibold flex items-center gap-1">
                        🍱 Tushlik vaqti:
                      </span>
                      <span className="font-bold text-amber-900 text-xs bg-white px-1.5 py-0.5 rounded border border-amber-200">
                        {s.lunch_start || '12:00'} - {s.lunch_end || '13:00'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Kechikish ruxsati:</span>
                      <span className="text-amber-600 font-semibold">{s.late_tolerance_minutes} daqiqa</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Barvaqt ketish ruxsati:</span>
                      <span className="text-indigo-600 font-semibold">{s.early_leave_tolerance_minutes} daqiqa</span>
                    </div>
                  </div>
                </div>

                <div className="flex gap-2 pt-3 border-t border-slate-100 justify-end">
                  <button
                    onClick={() => openEditShiftModal(s)}
                    className="p-2 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 transition"
                    title="Tahrirlash"
                  >
                    <Edit2 size={15} />
                  </button>
                  <button
                    onClick={() => handleDeleteShift(s.id)}
                    className="p-2 rounded-lg bg-rose-50 hover:bg-rose-100 text-rose-600 transition"
                    title="O'chirish"
                  >
                    <Trash2 size={15} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ======================================================== */}
      {/* TAB 2: HAFTALIK JADVALLAR (SCHEDULES)                   */}
      {/* ======================================================== */}
      {activeTab === 'schedules' && (
        <div className="space-y-4">
          <div className="flex justify-between items-center bg-white p-4 rounded-xl border border-slate-200">
            <div>
              <h3 className="font-bold text-slate-900 text-base">
                {isCompany ? "Haftalik Ish Jadvallari" : "Haftalik Ish & Dars Jadvallari"}
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">Dushanbadan Yakshanbagacha qaysi kun qaysi smenada ishlash grafigi</p>
            </div>
            <button
              onClick={openNewScheduleModal}
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-[#0084ff] hover:bg-[#0073e0] text-white font-bold text-sm shadow-md shadow-[#0084ff]/20 transition"
            >
              <Plus size={16} /> Yangi Jadval Tuzish
            </button>
          </div>

          <div className="space-y-4">
            {schedules.map((sc) => {
              const weekDays = [
                { name: 'Du', shift: sc.monday_shift },
                { name: 'Se', shift: sc.tuesday_shift },
                { name: 'Ch', shift: sc.wednesday_shift },
                { name: 'Pa', shift: sc.thursday_shift },
                { name: 'Ju', shift: sc.friday_shift },
                { name: 'Sha', shift: sc.saturday_shift },
                { name: 'Yak', shift: sc.sunday_shift },
              ];

              return (
                <div key={sc.id} className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm hover:border-[#0084ff]/50 transition">
                  <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-3 mb-4">
                    <div>
                      <div className="flex items-center gap-2">
                        <CalendarDays className="text-[#0084ff]" size={20} />
                        <h4 className="font-bold text-slate-900 text-lg">{sc.name}</h4>
                      </div>
                      {sc.description && (
                        <p className="text-xs text-slate-500 mt-1">{sc.description}</p>
                      )}
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => openEditScheduleModal(sc)}
                        className="px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold flex items-center gap-1.5 transition"
                      >
                        <Edit2 size={13} /> Tahrirlash
                      </button>
                      <button
                        onClick={() => handleDeleteSchedule(sc.id)}
                        className="p-1.5 rounded-lg bg-rose-50 hover:bg-rose-100 text-rose-600 transition"
                        title="O'chirish"
                      >
                        <Trash2 size={15} />
                      </button>
                    </div>
                  </div>

                  {/* 7-day strip */}
                  <div className="grid grid-cols-7 gap-2">
                    {weekDays.map((d, idx) => (
                      <div 
                        key={idx} 
                        className={`p-3 rounded-xl border text-center flex flex-col justify-between min-h-[75px] ${
                          d.shift 
                            ? 'bg-blue-50/50 border-blue-200' 
                            : 'bg-slate-50 border-slate-200/60 opacity-60'
                        }`}
                      >
                        <div className="font-bold text-xs text-slate-700">{d.name}</div>
                        {d.shift ? (
                          <div>
                            <div className="text-[11px] font-bold text-[#0084ff] truncate">{d.shift.name}</div>
                            <div className="text-[10px] font-mono font-semibold text-slate-600 mt-0.5">
                              {d.shift.start_time} - {d.shift.end_time}
                            </div>
                          </div>
                        ) : (
                          <div className="text-[11px] font-medium text-slate-400">Dam olish</div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ======================================================== */}
      {/* TAB 3: XODIMLARGA BIRIKTIRISH                           */}
      {/* ======================================================== */}
      {activeTab === 'assign_staff' && assignments && (
        <div className="space-y-4">
          <div className="bg-white p-4 rounded-xl border border-slate-200 flex flex-wrap gap-3 items-center justify-between">
            <div className="flex items-center gap-3">
              <input
                type="text"
                placeholder="Xodim F.I.SH yoki ID..."
                value={searchAssign}
                onChange={(e) => setSearchAssign(e.target.value)}
                className="bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2 text-sm text-slate-800 focus:outline-none focus:border-[#0084ff]"
              />
              <span className="text-xs text-slate-500">Tanlandi: <b>{selectedStaffIds.length}</b> ta xodim</span>
            </div>

            <div className="flex items-center gap-2">
              <select
                value={targetScheduleId ?? ''}
                onChange={(e) => setTargetScheduleId(e.target.value ? Number(e.target.value) : null)}
                className="bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2 text-sm text-slate-800 focus:outline-none focus:border-[#0084ff] font-medium"
              >
                <option value="">-- Jadvalni tanlang --</option>
                {schedules.map(sc => (
                  <option key={sc.id} value={sc.id}>{sc.name}</option>
                ))}
              </select>

              <button
                onClick={handleAssignToStaff}
                className="px-4 py-2 rounded-xl bg-[#0084ff] hover:bg-[#0073e0] text-white font-bold text-sm shadow-md shadow-[#0084ff]/20 transition whitespace-nowrap"
              >
                Biriktirish
              </button>
            </div>
          </div>

          <div className="bg-white border border-slate-200 rounded-2xl overflow-hidden shadow-sm">
            <table className="w-full text-left text-sm text-slate-700">
              <thead className="bg-slate-50 text-xs uppercase tracking-wider text-slate-500 border-b border-slate-200">
                <tr>
                  <th className="py-3.5 px-4 w-12 text-center">
                    <button onClick={toggleSelectAllStaff} className="text-slate-600 hover:text-[#0084ff]">
                      {selectedStaffIds.length > 0 && selectedStaffIds.length === assignments.staff.length ? (
                        <CheckSquare size={18} className="text-[#0084ff]" />
                      ) : (
                        <Square size={18} />
                      )}
                    </button>
                  </th>
                  <th className="py-3.5 px-4">Xodim</th>
                  <th className="py-3.5 px-4">ID</th>
                  <th className="py-3.5 px-4">Bo'lim / Lavozim</th>
                  <th className="py-3.5 px-4">Biriktirilgan Jadval</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {assignments.staff
                  .filter(s => 
                    s.full_name.toLowerCase().includes(searchAssign.toLowerCase()) ||
                    s.employee_no.toLowerCase().includes(searchAssign.toLowerCase())
                  )
                  .map(u => {
                    const isSelected = selectedStaffIds.includes(u.id);
                    return (
                      <tr key={u.id} className={isSelected ? 'bg-blue-50/40' : 'hover:bg-slate-50'}>
                        <td className="py-3 px-4 text-center">
                          <input
                            type="checkbox"
                            checked={isSelected}
                            onChange={() => {
                              setSelectedStaffIds(prev => 
                                isSelected ? prev.filter(id => id !== u.id) : [...prev, u.id]
                              );
                            }}
                            className="w-4 h-4 text-[#0084ff] rounded cursor-pointer accent-[#0084ff]"
                          />
                        </td>
                        <td className="py-3 px-4 font-semibold text-slate-900">{u.full_name}</td>
                        <td className="py-3 px-4 font-mono text-xs">{u.employee_no}</td>
                        <td className="py-3 px-4 text-slate-500 text-xs">
                          {u.department_name || '-'} {u.position ? `(${u.position})` : ''}
                        </td>
                        <td className="py-3 px-4">
                          <span className={`px-2.5 py-1 rounded-full text-xs font-semibold ${
                            u.schedule_id ? 'bg-blue-50 text-[#0084ff] border border-blue-200' : 'bg-slate-100 text-slate-500'
                          }`}>
                            {u.schedule_name}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ======================================================== */}
      {/* TAB 4: TALABALAR & GURUHLARGA BIRIKTIRISH                */}
      {/* ======================================================== */}
      {!isCompany && activeTab === 'assign_students' && assignments && (
        <div className="space-y-4">
          <div className="bg-white p-4 rounded-xl border border-slate-200 flex flex-wrap gap-3 items-center justify-between">
            <div className="flex items-center gap-3">
              <input
                type="text"
                placeholder="Guruh nomi yoki yo'nalish..."
                value={searchAssign}
                onChange={(e) => setSearchAssign(e.target.value)}
                className="bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2 text-sm text-slate-800 focus:outline-none focus:border-[#0084ff]"
              />
              <span className="text-xs text-slate-500">Tanlandi: <b>{selectedGroupIds.length}</b> ta guruh</span>
            </div>

            <div className="flex items-center gap-2">
              <select
                value={targetScheduleId ?? ''}
                onChange={(e) => setTargetScheduleId(e.target.value ? Number(e.target.value) : null)}
                className="bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2 text-sm text-slate-800 focus:outline-none focus:border-[#0084ff] font-medium"
              >
                <option value="">-- O'qish Jadvalini tanlang --</option>
                {schedules.map(sc => (
                  <option key={sc.id} value={sc.id}>{sc.name}</option>
                ))}
              </select>

              <button
                onClick={handleAssignToGroups}
                className="px-4 py-2 rounded-xl bg-[#0084ff] hover:bg-[#0073e0] text-white font-bold text-sm shadow-md shadow-[#0084ff]/20 transition whitespace-nowrap"
              >
                Guruhga Biriktirish
              </button>
            </div>
          </div>

          <div className="bg-white border border-slate-200 rounded-2xl overflow-hidden shadow-sm">
            <table className="w-full text-left text-sm text-slate-700">
              <thead className="bg-slate-50 text-xs uppercase tracking-wider text-slate-500 border-b border-slate-200">
                <tr>
                  <th className="py-3.5 px-4 w-12 text-center">
                    <button onClick={toggleSelectAllGroups} className="text-slate-600 hover:text-[#0084ff]">
                      {selectedGroupIds.length > 0 && selectedGroupIds.length === assignments.groups.length ? (
                        <CheckSquare size={18} className="text-[#0084ff]" />
                      ) : (
                        <Square size={18} />
                      )}
                    </button>
                  </th>
                  <th className="py-3.5 px-4">Guruh Nomi</th>
                  <th className="py-3.5 px-4">Ta'lim Yo'nalishi</th>
                  <th className="py-3.5 px-4">Biriktirilgan Smena Jadvali</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {assignments.groups
                  .filter(g => 
                    g.name.toLowerCase().includes(searchAssign.toLowerCase()) ||
                    (g.direction_name && g.direction_name.toLowerCase().includes(searchAssign.toLowerCase()))
                  )
                  .map(g => {
                    const isSelected = selectedGroupIds.includes(g.id);
                    return (
                      <tr key={g.id} className={isSelected ? 'bg-blue-50/40' : 'hover:bg-slate-50'}>
                        <td className="py-3 px-4 text-center">
                          <input
                            type="checkbox"
                            checked={isSelected}
                            onChange={() => {
                              setSelectedGroupIds(prev => 
                                isSelected ? prev.filter(id => id !== g.id) : [...prev, g.id]
                              );
                            }}
                            className="w-4 h-4 text-[#0084ff] rounded cursor-pointer accent-[#0084ff]"
                          />
                        </td>
                        <td className="py-3 px-4 font-bold text-slate-900">{g.name}</td>
                        <td className="py-3 px-4 text-slate-600 text-xs">{g.direction_name || '-'}</td>
                        <td className="py-3 px-4">
                          <span className={`px-2.5 py-1 rounded-full text-xs font-semibold ${
                            g.schedule_id ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-slate-100 text-slate-500'
                          }`}>
                            {g.schedule_name}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ======================================================== */}
      {/* SHIFT CREATE / EDIT MODAL                                */}
      {/* ======================================================== */}
      {showShiftModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white border border-slate-200 w-full max-w-md rounded-2xl p-6 shadow-2xl">
            <h3 className="text-lg font-bold text-slate-900 mb-4 flex items-center gap-2">
              <Clock className="text-[#0084ff]" /> {editingShift ? "Smenani Tahrirlash" : "Yangi Smena (Ish Vaqti) Qo'shish"}
            </h3>
            <form onSubmit={handleSaveShift} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1">Smena Nomi</label>
                <input
                  type="text"
                  placeholder="Masalan: Standart Ish Vaqti yoki 1-Smena"
                  value={shiftName}
                  onChange={(e) => setShiftName(e.target.value)}
                  required
                  className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2 text-slate-900 text-sm focus:outline-none focus:border-[#0084ff] focus:bg-white"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-1">Kirish Vaqti (Boshlanishi)</label>
                  <input
                    type="time"
                    value={shiftStart}
                    onChange={(e) => setShiftStart(e.target.value)}
                    required
                    className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2 text-slate-900 text-sm focus:outline-none focus:border-[#0084ff] focus:bg-white font-mono"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-1">Chiqish Vaqti (Tugashi)</label>
                  <input
                    type="time"
                    value={shiftEnd}
                    onChange={(e) => setShiftEnd(e.target.value)}
                    required
                    className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2 text-slate-900 text-sm focus:outline-none focus:border-[#0084ff] focus:bg-white font-mono"
                  />
                </div>
              </div>

              {/* Tushlik vaqti (Tanaffus) */}
              <div className="p-3.5 bg-amber-50/70 border border-amber-200/90 rounded-2xl space-y-2.5">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-bold text-amber-950 flex items-center gap-1.5">
                    🍱 Tushlik Vaqti (Tanaffus)
                  </label>
                  <span className="text-[10px] text-amber-800 bg-amber-100 font-bold px-2 py-0.5 rounded-full border border-amber-200">
                    Universal Davomat & Tabel
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-[11px] font-semibold text-slate-600 mb-1">
                      Tushlikka chiqish (Boshlanishi)
                    </label>
                    <input
                      type="time"
                      value={shiftLunchStart}
                      onChange={(e) => setShiftLunchStart(e.target.value)}
                      required
                      className="w-full bg-white border border-slate-300 rounded-xl px-3.5 py-2 text-slate-900 text-sm focus:outline-none focus:border-[#0084ff] font-mono font-bold"
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] font-semibold text-slate-600 mb-1">
                      Tushlikdan qaytish (Tugashi)
                    </label>
                    <input
                      type="time"
                      value={shiftLunchEnd}
                      onChange={(e) => setShiftLunchEnd(e.target.value)}
                      required
                      className="w-full bg-white border border-slate-300 rounded-xl px-3.5 py-2 text-slate-900 text-sm focus:outline-none focus:border-[#0084ff] font-mono font-bold"
                    />
                  </div>
                </div>
                <p className="text-[10px] text-amber-800/80 leading-relaxed">
                  * Universal rejimda xodim ushbu soatlar orasida chiqib-kirsa, tizim buni tushlik hisoblab tabelda to'g'ri qayd etadi.
                </p>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-1">Kechikish chegarasi (daqiqa)</label>
                  <input
                    type="number"
                    value={shiftLateTol}
                    onChange={(e) => setShiftLateTol(Number(e.target.value))}
                    min={0}
                    max={120}
                    required
                    className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2 text-slate-900 text-sm focus:outline-none focus:border-[#0084ff] focus:bg-white font-mono"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-1">Barvaqt ketish (daqiqa)</label>
                  <input
                    type="number"
                    value={shiftEarlyTol}
                    onChange={(e) => setShiftEarlyTol(Number(e.target.value))}
                    min={0}
                    max={120}
                    required
                    className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2 text-slate-900 text-sm focus:outline-none focus:border-[#0084ff] focus:bg-white font-mono"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1">Belgi Rangi</label>
                <div className="flex gap-3 items-center">
                  <input
                    type="color"
                    value={shiftColor}
                    onChange={(e) => setShiftColor(e.target.value)}
                    className="w-10 h-10 rounded-lg cursor-pointer border-0 p-0"
                  />
                  <span className="text-xs font-mono text-slate-600">{shiftColor}</span>
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowShiftModal(false)}
                  className="px-4 py-2 text-slate-600 hover:text-slate-800 text-sm font-semibold transition"
                >
                  Bekor qilish
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 bg-[#0084ff] hover:bg-[#0073e0] text-white rounded-xl text-sm font-bold shadow-md shadow-[#0084ff]/20 transition"
                >
                  Saqlash
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ======================================================== */}
      {/* SCHEDULE CREATE / EDIT MODAL                             */}
      {/* ======================================================== */}
      {showScheduleModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white border border-slate-200 w-full max-w-lg rounded-2xl p-6 shadow-2xl max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-bold text-slate-900 mb-4 flex items-center gap-2">
              <CalendarDays className="text-[#0084ff]" /> {editingSchedule ? "Haftalik Jadvalni Tahrirlash" : "Yangi Haftalik Jadval Tuzish"}
            </h3>
            <form onSubmit={handleSaveSchedule} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1">Jadval Nomi</label>
                <input
                  type="text"
                  placeholder="Masalan: 5 kunlik Xodimlar Grafigi"
                  value={schName}
                  onChange={(e) => setSchName(e.target.value)}
                  required
                  className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2 text-slate-900 text-sm focus:outline-none focus:border-[#0084ff] focus:bg-white"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1">Tavsif (ixtiyoriy)</label>
                <input
                  type="text"
                  placeholder="Masalan: Dushanba - Juma 08:30 dan 17:30 gacha"
                  value={schDesc}
                  onChange={(e) => setSchDesc(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2 text-slate-900 text-sm focus:outline-none focus:border-[#0084ff] focus:bg-white"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-2">Haftaning Har Bir Kuni Uchun Smena:</label>
                <div className="space-y-2.5 bg-slate-50 p-3.5 rounded-xl border border-slate-200">
                  {daysConfig.map((d) => (
                    <div key={d.key} className="flex items-center justify-between gap-3 text-sm">
                      <span className="font-semibold text-slate-800 w-28">{d.label}:</span>
                      <select
                        value={dayShifts[d.key] ?? ''}
                        onChange={(e) => {
                          const val = e.target.value ? Number(e.target.value) : null;
                          setDayShifts(prev => ({ ...prev, [d.key]: val }));
                        }}
                        className="flex-1 bg-white border border-slate-300 rounded-lg px-3 py-1.5 text-xs text-slate-800 focus:outline-none focus:border-[#0084ff]"
                      >
                        <option value="">-- Dam Olish Kuni (Day off) --</option>
                        {shifts.map(s => (
                          <option key={s.id} value={s.id}>
                            {s.name} ({s.start_time} - {s.end_time})
                          </option>
                        ))}
                      </select>
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowScheduleModal(false)}
                  className="px-4 py-2 text-slate-600 hover:text-slate-800 text-sm font-semibold transition"
                >
                  Bekor qilish
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 bg-[#0084ff] hover:bg-[#0073e0] text-white rounded-xl text-sm font-bold shadow-md shadow-[#0084ff]/20 transition"
                >
                  Saqlash
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
};
