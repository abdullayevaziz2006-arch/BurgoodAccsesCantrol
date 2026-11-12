import React, { useState } from 'react';
import { AccessLog } from '../types';
import { exportLogsExcel, exportTabelExcel } from '../api';
import { FileSpreadsheet, Search, ArrowUpRight, ArrowDownLeft, Clock, CalendarDays } from 'lucide-react';

interface AttendanceProps {
  logs: AccessLog[];
  onRefresh: () => void;
  onNavigateToSettings?: () => void;
  isCompany?: boolean;
}

export const AttendanceView: React.FC<AttendanceProps> = ({ logs, onNavigateToSettings, isCompany }) => {
  const [search, setSearch] = useState('');
  const [filterDirection, setFilterDirection] = useState<string>('all');

  const filteredLogs = logs.filter(log => {
    const matchesSearch = 
      (log.user_name && log.user_name.toLowerCase().includes(search.toLowerCase())) ||
      (log.employee_no && log.employee_no.toLowerCase().includes(search.toLowerCase())) ||
      (log.device_name && log.device_name.toLowerCase().includes(search.toLowerCase()));

    const matchesDirection = 
      filterDirection === 'all' || log.direction === filterDirection;

    return matchesSearch && matchesDirection;
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-white border border-slate-200/80 p-5 sm:p-6 rounded-2xl shadow-sm">
        <div>
          <h2 className="text-xl font-bold text-slate-800 flex items-center gap-2">
            <Clock className="text-[#0084ff]" size={24} />
            {isCompany ? "Xodimlar Davomati & Ish Vaqti Tabeli" : "Davomat va Kirish-Chiqish Tarixi"}
          </h2>
          <p className="text-slate-500 text-sm mt-1">
            {isCompany 
              ? "Turniketlar orqali o'tgan barcha xodimlar va mas'ullar o'tish jurnali & Tabel"
              : "Turniketlar orqali o'tgan barcha talabalar va xodimlar o'tish jurnali"}
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          {onNavigateToSettings && (
            <button 
              onClick={onNavigateToSettings}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-[#0a1224] hover:bg-[#121f3a] text-white font-semibold text-sm shadow-md transition whitespace-nowrap border border-slate-700"
            >
              <CalendarDays size={18} className="text-cyan-400" /> {isCompany ? "Ish Rejasi & Smenalar" : "Attendance Settings"}
            </button>
          )}

          <button 
            onClick={() => exportTabelExcel()}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold text-sm shadow-md shadow-blue-600/20 transition whitespace-nowrap"
            title="Oylik ish vaqti tabeli, ishlangan soatlar va kechikishlar hisoboti"
          >
            <FileSpreadsheet size={18} /> Oylik Tabel (.xlsx)
          </button>

          <button 
            onClick={exportLogsExcel}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-sm shadow-md shadow-emerald-600/20 transition whitespace-nowrap"
          >
            <FileSpreadsheet size={18} /> Kunlik Jurnal (.xlsx)
          </button>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="bg-white border border-slate-200/80 p-4 rounded-2xl flex flex-wrap gap-3 items-center justify-between shadow-sm">
        <div className="relative flex-1 min-w-[220px]">
          <Search size={16} className="absolute left-3.5 top-3 text-slate-400" />
          <input 
            type="text" 
            placeholder="F.I.SH, ID yoki Turniket..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-slate-50 border border-slate-200 rounded-xl pl-10 pr-4 py-2 text-sm text-slate-800 focus:outline-none focus:border-[#0084ff] focus:bg-white transition"
          />
        </div>

        <div className="flex gap-2">
          <button 
            onClick={() => setFilterDirection('all')}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition ${
              filterDirection === 'all' ? 'bg-[#0084ff] text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            Barchasi
          </button>
          <button 
            onClick={() => setFilterDirection('entry')}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition ${
              filterDirection === 'entry' ? 'bg-emerald-600 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            Faqat Kirish
          </button>
          <button 
            onClick={() => setFilterDirection('exit')}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition ${
              filterDirection === 'exit' ? 'bg-amber-600 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            Faqat Chiqish
          </button>
        </div>
      </div>

      {/* Logs Table */}
      <div className="bg-white border border-slate-200/80 rounded-2xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-700">
            <thead className="bg-slate-50 text-xs uppercase tracking-wider text-slate-500 border-b border-slate-200">
              <tr>
                <th className="py-4 px-6">Vaqt</th>
                <th className="py-4 px-6">{isCompany ? "Xodim (F.I.SH)" : "Shaxs (Talaba / Xodim)"}</th>
                <th className="py-4 px-6">ID Raqami</th>
                <th className="py-4 px-6">Yo'nalish</th>
                <th className="py-4 px-6">Turniket / Qurilma</th>
                <th className="py-4 px-6">Turi / Usul</th>
                <th className="py-4 px-6 text-right">Holat</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-sans">
              {filteredLogs.map((log) => (
                <tr key={log.id} className="hover:bg-slate-50/80 transition">
                  <td className="py-4 px-6 font-mono text-xs text-slate-500 whitespace-nowrap">
                    {log.event_time}
                  </td>
                  <td className="py-4 px-6 font-bold text-slate-900">
                    {log.user_name || "Noma'lum Shaxs"}
                  </td>
                  <td className="py-4 px-6 font-mono text-xs text-[#0084ff] font-bold">
                    {log.employee_no || "-"}
                  </td>
                  <td className="py-4 px-6">
                    <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold ${
                      log.direction === 'entry'
                        ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                        : log.direction === 'break_out'
                        ? 'bg-amber-50 text-amber-700 border border-amber-200'
                        : log.direction === 'break_in'
                        ? 'bg-sky-50 text-sky-700 border border-sky-200'
                        : 'bg-rose-50 text-rose-700 border border-rose-200'
                    }`}>
                      {log.direction === 'entry' ? (
                        <>
                          <ArrowDownLeft size={13} /> Kirish
                        </>
                      ) : log.direction === 'break_out' ? (
                        <>
                          <ArrowUpRight size={13} /> Tushlik (Ketdi)
                        </>
                      ) : log.direction === 'break_in' ? (
                        <>
                          <ArrowDownLeft size={13} /> Tushlik (Qaytdi)
                        </>
                      ) : (
                        <>
                          <ArrowUpRight size={13} /> Chiqish
                        </>
                      )}
                    </span>
                  </td>
                  <td className="py-4 px-6 text-xs text-slate-700 font-medium">
                    {log.device_name || `Turniket #${log.device_id}`}
                  </td>
                  <td className="py-4 px-6 text-xs text-slate-500">
                    {log.event_type}
                  </td>
                  <td className="py-4 px-6 text-right">
                    <span className={`px-2 py-0.5 rounded text-xs font-bold ${
                      log.status === 'Success' ? 'text-emerald-700 bg-emerald-50' : 'text-rose-700 bg-rose-50'
                    }`}>
                      {log.status === 'Success' ? 'Ruxsat berildi' : 'Rad etildi'}
                    </span>
                  </td>
                </tr>
              ))}

              {filteredLogs.length === 0 && (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-slate-400">
                    O'tish jurnallari topilmadi
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
