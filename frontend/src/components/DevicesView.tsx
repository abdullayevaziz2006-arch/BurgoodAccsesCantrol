import React, { useState } from 'react';
import { Device } from '../types';
import { createDevice, testDevice, openDoorRemote, deleteDevice } from '../api';
import { Shield, Plus, RefreshCw, KeyRound, ArrowRightCircle, ArrowLeftCircle, CheckCircle, AlertCircle, Trash2, Cpu } from 'lucide-react';

interface DevicesProps {
  devices: Device[];
  onRefresh: () => void;
}

export const DevicesView: React.FC<DevicesProps> = ({ devices, onRefresh }) => {
  const [showAddModal, setShowAddModal] = useState(false);
  const [loading, setLoading] = useState(false);
  const [testResult, setTestResult] = useState<{ id: number; message: string; success: boolean } | null>(null);

  // Form states
  const [name, setName] = useState('');
  const [ipAddress, setIpAddress] = useState('');
  const [port, setPort] = useState(80);
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('');
  const [direction, setDirection] = useState<'entry' | 'exit'>('entry');
  const [location, setLocation] = useState('');

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await createDevice({
        name,
        ip_address: ipAddress,
        port: Number(port),
        username,
        password,
        direction,
        location,
        is_active: true
      });
      setShowAddModal(false);
      setName('');
      setIpAddress('');
      setPassword('');
      setLocation('');
      onRefresh();
    } catch (err: any) {
      alert(err.response?.data?.detail || "Terminal qo'shishda xatolik");
    } finally {
      setLoading(false);
    }
  };

  const handleTest = async (id: number) => {
    setLoading(true);
    try {
      const res = await testDevice(id);
      setTestResult({ id, message: res.message, success: res.success });
      onRefresh();
    } catch (err: any) {
      setTestResult({ id, message: err.response?.data?.detail || "Ulanish xatosi", success: false });
    } finally {
      setLoading(false);
    }
  };

  const handleOpenDoor = async (id: number) => {
    if (!confirm("Haqiqatan ham turniketni masofadan ochmoqchimisiz?")) return;
    try {
      const res = await openDoorRemote(id);
      alert(res.message);
    } catch (err: any) {
      alert(err.response?.data?.detail || "Eshikni ochishda xatolik");
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Qurilmani ro'yxatdan o'chirishga ishonchingiz komilmi?")) return;
    try {
      await deleteDevice(id);
      onRefresh();
    } catch (err: any) {
      alert("O'chirishda xatolik yuz berdi");
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-sm">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Cpu className="text-indigo-400" />
            Hikvision Face ID Terminallari
          </h2>
          <p className="text-slate-400 text-sm mt-1">
            Turniketlar, yuzni tanish kameralari va ularning tarmoqdagi holati
          </p>
        </div>
        <div className="flex gap-3">
          <button 
            onClick={onRefresh}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl border border-slate-700 bg-slate-800 hover:bg-slate-700 text-slate-200 transition"
          >
            <RefreshCw size={16} /> Yangilash
          </button>
          <button 
            onClick={() => setShowAddModal(true)}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-medium shadow-lg shadow-indigo-600/30 transition"
          >
            <Plus size={18} /> Yangi Terminal Qo'shish
          </button>
        </div>
      </div>

      {/* Grid of Devices */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {devices.map((device) => (
          <div 
            key={device.id} 
            className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 hover:border-slate-700 transition relative overflow-hidden flex flex-col justify-between"
          >
            <div>
              <div className="flex justify-between items-start mb-3">
                <div className="flex items-center gap-2">
                  <div className={`w-3 h-3 rounded-full ${
                    device.status === 'online' ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'
                  }`} />
                  <span className="font-semibold text-lg text-white">{device.name}</span>
                </div>
                <span className={`px-2.5 py-1 text-xs font-semibold rounded-full uppercase tracking-wider ${
                  device.direction === 'entry' ? 'bg-emerald-950/80 text-emerald-400 border border-emerald-800/50' : 'bg-amber-950/80 text-amber-400 border border-amber-800/50'
                }`}>
                  {device.direction === 'entry' ? 'Kirish' : 'Chiqish'}
                </span>
              </div>

              <div className="space-y-1.5 text-xs text-slate-300 bg-slate-950/50 p-3.5 rounded-xl border border-slate-800/80 font-mono mb-4">
                <div className="flex justify-between">
                  <span className="text-slate-500">IP Manzil:</span>
                  <span className="text-indigo-300 font-bold">{device.ip_address}:{device.port}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Model:</span>
                  <span>{device.model || 'Hikvision Terminal'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Seriya raqami:</span>
                  <span>{device.serial_number || 'Aniqlanmagan'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Joylashuv:</span>
                  <span className="text-slate-200">{device.location || 'Asosiy bino'}</span>
                </div>
              </div>

              {testResult && testResult.id === device.id && (
                <div className={`p-2.5 mb-3 rounded-xl text-xs flex items-center gap-2 ${
                  testResult.success ? 'bg-emerald-900/40 text-emerald-300 border border-emerald-800' : 'bg-rose-900/40 text-rose-300 border border-rose-800'
                }`}>
                  {testResult.success ? <CheckCircle size={14} /> : <AlertCircle size={14} />}
                  <span>{testResult.message}</span>
                </div>
              )}
            </div>

            <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between gap-2">
              <button 
                onClick={() => handleTest(device.id)}
                disabled={loading}
                className="flex-1 py-2 text-xs font-medium rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700/80 transition"
              >
                Aloqa Sinovi
              </button>
              <button 
                onClick={() => handleOpenDoor(device.id)}
                className="flex-1 py-2 text-xs font-semibold rounded-lg bg-emerald-600/90 hover:bg-emerald-500 text-white shadow-md shadow-emerald-700/20 transition flex items-center justify-center gap-1.5"
              >
                <KeyRound size={13} /> Eshikni Och
              </button>
              <button 
                onClick={() => handleDelete(device.id)}
                className="p-2 rounded-lg bg-rose-950/40 hover:bg-rose-900/60 text-rose-400 border border-rose-900/40 transition"
                title="O'chirish"
              >
                <Trash2 size={14} />
              </button>
            </div>
          </div>
        ))}

        {devices.length === 0 && (
          <div className="col-span-full py-16 text-center text-slate-500 bg-slate-900/40 border border-dashed border-slate-800 rounded-2xl">
            <Cpu size={40} className="mx-auto mb-3 opacity-40" />
            <p className="text-base font-medium">Hozircha hech qanday Face ID terminali ulanmagan</p>
            <p className="text-xs text-slate-600 mt-1">"Yangi Terminal Qo'shish" tugmasini bosing va IP manzilini kiriting</p>
          </div>
        )}
      </div>

      {/* Add Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/75 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-slate-900 border border-slate-800 w-full max-w-md rounded-2xl p-6 shadow-2xl">
            <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
              <Cpu className="text-indigo-400" /> Yangi Hikvision Terminalini Qo'shish
            </h3>
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Qurilma Nomi</label>
                <input 
                  type="text" 
                  placeholder="Turniket 1 - Bosh bino"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-white text-sm focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div className="col-span-2">
                  <label className="block text-xs font-medium text-slate-400 mb-1">IP Manzil</label>
                  <input 
                    type="text" 
                    placeholder="192.168.1.120"
                    value={ipAddress}
                    onChange={(e) => setIpAddress(e.target.value)}
                    required
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-white text-sm focus:outline-none focus:border-indigo-500 font-mono"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">Port</label>
                  <input 
                    type="number" 
                    value={port}
                    onChange={(e) => setPort(Number(e.target.value))}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-white text-sm focus:outline-none focus:border-indigo-500 font-mono"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">Terminal Logini</label>
                  <input 
                    type="text" 
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    required
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-white text-sm focus:outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">Terminal Paroli</label>
                  <input 
                    type="password" 
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-white text-sm focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">Yo'nalish</label>
                  <select 
                    value={direction}
                    onChange={(e: any) => setDirection(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-white text-sm focus:outline-none focus:border-indigo-500"
                  >
                    <option value="entry">Kirish (Entry)</option>
                    <option value="exit">Chiqish (Exit)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">Joylashuv</label>
                  <input 
                    type="text" 
                    placeholder="Bosh korpus, 1-qavat"
                    value={location}
                    onChange={(e) => setLocation(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-white text-sm focus:outline-none focus:border-indigo-500"
                  />
                </div>
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
                  {loading ? "Ulanmoqda..." : "Qo'shish"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
