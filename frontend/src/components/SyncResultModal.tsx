import React from 'react';
import { CheckCircle2, AlertTriangle, XCircle, Cpu, X, Server, Image, Users } from 'lucide-react';

export interface SyncResultData {
  isOpen: boolean;
  success: boolean;
  title?: string;
  total_users: number;
  total_devices: number;
  total_faces_uploaded?: number;
  total_failures?: number;
  details: Array<{
    device_id: number;
    device_name: string;
    success_count: number;
    fail_count: number;
    faces_uploaded?: number;
    errors?: string[];
  }>;
  errorMessage?: string;
}

interface SyncResultModalProps {
  data: SyncResultData | null;
  onClose: () => void;
  entityName?: string; // "talaba" yoki "xodim"
}

export const SyncResultModal: React.FC<SyncResultModalProps> = ({ data, onClose, entityName = "foydalanuvchi" }) => {
  if (!data || !data.isOpen) return null;

  const isCompleteSuccess = data.success && (!data.total_failures || data.total_failures === 0) && !data.errorMessage;
  const isPartial = !isCompleteSuccess && (data.details.some(d => d.success_count > 0));

  return (
    <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-in fade-in duration-200 font-sans">
      <div className="bg-white border border-slate-200 text-slate-800 w-full max-w-md rounded-3xl p-6 shadow-2xl relative animate-in zoom-in-95 duration-150">
        
        {/* Close Button */}
        <button 
          onClick={onClose}
          className="absolute right-5 top-5 text-slate-400 hover:text-slate-700 p-1.5 rounded-xl hover:bg-slate-100 transition"
        >
          <X size={18} />
        </button>

        {/* Status Header */}
        <div className="flex flex-col items-center text-center mb-5">
          {isCompleteSuccess ? (
            <div className="w-16 h-16 rounded-2xl bg-emerald-50 border border-emerald-100 flex items-center justify-center text-emerald-600 mb-3.5 shadow-inner">
              <CheckCircle2 size={36} className="animate-in zoom-in-50 duration-300" />
            </div>
          ) : isPartial ? (
            <div className="w-16 h-16 rounded-2xl bg-amber-50 border border-amber-100 flex items-center justify-center text-amber-600 mb-3.5 shadow-inner">
              <AlertTriangle size={36} className="animate-in zoom-in-50 duration-300" />
            </div>
          ) : (
            <div className="w-16 h-16 rounded-2xl bg-rose-50 border border-rose-100 flex items-center justify-center text-rose-600 mb-3.5 shadow-inner">
              <XCircle size={36} className="animate-in zoom-in-50 duration-300" />
            </div>
          )}

          <h3 className="text-xl font-extrabold text-slate-900 tracking-tight">
            {data.title || (isCompleteSuccess ? "Hammasi ajoyib!" : isPartial ? "Qisman muvaffaqiyatli" : "Xatolik yuz berdi")}
          </h3>
          <p className="text-xs text-slate-500 mt-1 max-w-xs">
            {isCompleteSuccess 
              ? `Barcha ma'lumotlar va Face ID rasmlari terminallarga to'liq uzatildi.` 
              : isPartial 
              ? `Ba'zi terminallarga yuborildi, ammo ayrim xatoliklar mavjud.`
              : `Ma'lumotlarni terminallarga yuborishda muammo yuzaga keldi.`
            }
          </p>
        </div>

        {/* Global Error Banner if any */}
        {data.errorMessage && (
          <div className="mb-4 p-3 bg-rose-50 border border-rose-200 rounded-xl text-rose-700 text-xs font-medium">
            {data.errorMessage}
          </div>
        )}

        {/* Statistics Cards */}
        <div className="grid grid-cols-3 gap-2.5 mb-4">
          <div className="bg-slate-50 border border-slate-200/80 rounded-2xl p-3 text-center">
            <div className="flex items-center justify-center text-slate-400 mb-1">
              <Users size={15} />
            </div>
            <div className="text-base font-black text-slate-800">{data.total_users}</div>
            <div className="text-[10px] font-semibold text-slate-500 capitalize">{entityName}lar</div>
          </div>

          <div className="bg-slate-50 border border-slate-200/80 rounded-2xl p-3 text-center">
            <div className="flex items-center justify-center text-slate-400 mb-1">
              <Server size={15} />
            </div>
            <div className="text-base font-black text-slate-800">{data.total_devices}</div>
            <div className="text-[10px] font-semibold text-slate-500">Terminallar</div>
          </div>

          <div className="bg-emerald-50/70 border border-emerald-200/70 rounded-2xl p-3 text-center">
            <div className="flex items-center justify-center text-emerald-600 mb-1">
              <Image size={15} />
            </div>
            <div className="text-base font-black text-emerald-700">{data.total_faces_uploaded ?? 0}</div>
            <div className="text-[10px] font-semibold text-emerald-600">Yuz rasmlari</div>
          </div>
        </div>

        {/* Per-device Results List */}
        {data.details && data.details.length > 0 && (
          <div className="space-y-2 mb-5 max-h-48 overflow-y-auto pr-1">
            {data.details.map((dev) => {
              const devOk = dev.fail_count === 0 && dev.success_count > 0;
              return (
                <div 
                  key={dev.device_id}
                  className={`p-3 rounded-2xl border transition text-xs ${
                    devOk 
                      ? 'bg-emerald-50/40 border-emerald-200/80' 
                      : 'bg-rose-50/40 border-rose-200/80'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center gap-1.5 font-bold text-slate-800">
                      <Cpu size={14} className={devOk ? "text-emerald-600" : "text-rose-600"} />
                      <span>{dev.device_name}</span>
                    </div>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                      devOk 
                        ? 'bg-emerald-100 text-emerald-800' 
                        : 'bg-rose-100 text-rose-800'
                    }`}>
                      {devOk ? "Muvaffaqiyatli" : `${dev.fail_count} ta xatolik`}
                    </span>
                  </div>

                  <div className="text-[11px] text-slate-600 flex items-center justify-between">
                    <span>Qabul qilindi: <b>{dev.success_count} ta</b></span>
                    {dev.faces_uploaded !== undefined && (
                      <span className="text-emerald-700 font-semibold">Face ID: {dev.faces_uploaded} ta</span>
                    )}
                  </div>

                  {/* Device Specific Errors */}
                  {dev.errors && dev.errors.length > 0 && (
                    <div className="mt-2 pt-2 border-t border-rose-200/60 space-y-1">
                      {dev.errors.map((err, idx) => (
                        <div key={idx} className="text-[10px] text-rose-700 bg-rose-100/60 rounded-lg p-1.5 font-mono break-words leading-tight">
                          {err}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {/* Action Button */}
        <button
          type="button"
          onClick={onClose}
          className={`w-full py-3 rounded-2xl font-bold text-xs tracking-wider transition shadow-lg ${
            isCompleteSuccess
              ? 'bg-[#0084ff] hover:bg-[#0073e0] text-white shadow-[#0084ff]/25'
              : 'bg-slate-800 hover:bg-slate-900 text-white shadow-slate-800/20'
          }`}
        >
          {isCompleteSuccess ? "Ajoyib, Tushunarli" : "Yopish"}
        </button>

      </div>
    </div>
  );
};
