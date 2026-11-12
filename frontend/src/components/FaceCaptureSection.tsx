import React, { useState, useRef, useEffect } from 'react';
import { Device } from '../types';
import { captureFaceFromDevice } from '../api';
import { Camera, Server, Upload, Trash2, RefreshCw, X, Check, Video, AlertCircle } from 'lucide-react';

interface FaceCaptureSectionProps {
  currentPhotoUrl?: string | null;
  devices: Device[];
  onChange: (photoData: { file: File | null; dataUrl: string | null; isRemoved: boolean }) => void;
  accentColor?: 'indigo' | 'blue';
}

export const FaceCaptureSection: React.FC<FaceCaptureSectionProps> = ({
  currentPhotoUrl,
  devices,
  onChange,
  accentColor = 'indigo'
}) => {
  const [preview, setPreview] = useState<string | null>(currentPhotoUrl || null);
  const [terminalLoading, setTerminalLoading] = useState(false);
  const [terminalError, setTerminalError] = useState<string | null>(null);
  const [selectedDeviceId, setSelectedDeviceId] = useState<number | undefined>(
    devices.find(d => d.status === 'online')?.id || devices[0]?.id
  );
  const selectedDevice = devices.find(d => d.id === selectedDeviceId) || devices[0];

  // Web camera modal states
  const [showWebcam, setShowWebcam] = useState(false);
  const [webcamStream, setWebcamStream] = useState<MediaStream | null>(null);
  const [webcamError, setWebcamError] = useState<string | null>(null);
  const videoRef = useRef<HTMLVideoElement | null>(null);

  useEffect(() => {
    setPreview(currentPhotoUrl || null);
  }, [currentPhotoUrl]);

  // Update selected device if devices change
  useEffect(() => {
    if (!selectedDeviceId && devices.length > 0) {
      const onlineDev = devices.find(d => d.status === 'online') || devices[0];
      setSelectedDeviceId(onlineDev.id);
    }
  }, [devices]);

  // 1. Capture from Hikvision Face ID Terminal
  const handleCaptureFromTerminal = async () => {
    if (!selectedDeviceId) {
      setTerminalError("Ulangan terminal topilmadi");
      return;
    }
    setTerminalLoading(true);
    setTerminalError(null);
    try {
      const res = await captureFaceFromDevice(selectedDeviceId);
      if (res.success && res.image_data_url) {
        setPreview(res.image_data_url);
        onChange({ file: null, dataUrl: res.image_data_url, isRemoved: false });
      } else {
        setTerminalError("Terminaldan rasm olib bo'lmadi");
      }
    } catch (err: any) {
      const msg = err.response?.data?.detail || "Terminal kamerasidan rasm olishda xatolik";
      setTerminalError(msg);
    } finally {
      setTerminalLoading(false);
    }
  };

  // 2. File Upload from PC
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      const reader = new FileReader();
      reader.onload = () => {
        const url = reader.result as string;
        setPreview(url);
        onChange({ file, dataUrl: url, isRemoved: false });
      };
      reader.readAsDataURL(file);
      setTerminalError(null);
    }
  };

  // 3. Remove photo
  const handleRemovePhoto = () => {
    setPreview(null);
    onChange({ file: null, dataUrl: null, isRemoved: true });
    setTerminalError(null);
  };

  // 4. Web Camera Handling
  const startWebcam = async () => {
    setWebcamError(null);
    setShowWebcam(true);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: 'user' }
      });
      setWebcamStream(stream);
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
    } catch (err: any) {
      setWebcamError("Veb-kamerani ochib bo'lmadi. Kamera ulanmagan yoki ruxsat berilmagan.");
    }
  };

  const stopWebcam = () => {
    if (webcamStream) {
      webcamStream.getTracks().forEach(track => track.stop());
      setWebcamStream(null);
    }
    setShowWebcam(false);
  };

  useEffect(() => {
    if (showWebcam && webcamStream && videoRef.current) {
      videoRef.current.srcObject = webcamStream;
    }
  }, [showWebcam, webcamStream]);

  const captureWebcamSnapshot = () => {
    if (!videoRef.current) return;
    const video = videoRef.current;
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    const ctx = canvas.getContext('2d');
    if (ctx) {
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      const dataUrl = canvas.toDataURL('image/jpeg', 0.95);
      setPreview(dataUrl);
      onChange({ file: null, dataUrl, isRemoved: false });
      stopWebcam();
    }
  };

  const isBlue = accentColor === 'blue';

  return (
    <div className="bg-slate-50 border border-slate-200/90 rounded-2xl p-4 transition-all">
      <div className="flex flex-col sm:flex-row items-center gap-4">
        {/* Surat ko'rinishi (Preview) */}
        <div className="relative w-24 h-24 rounded-2xl bg-white border-2 border-slate-200 overflow-hidden shrink-0 flex items-center justify-center shadow-sm">
          {preview ? (
            <img src={preview} alt="Face preview" className="w-full h-full object-cover" />
          ) : (
            <div className="flex flex-col items-center justify-center text-slate-300">
              <Camera size={28} />
              <span className="text-[10px] font-medium text-slate-400 mt-1">Surat yo'q</span>
            </div>
          )}

          {terminalLoading && (
            <div className="absolute inset-0 bg-slate-900/60 backdrop-blur-xs flex flex-col items-center justify-center text-white p-1 text-center">
              <RefreshCw size={20} className="animate-spin text-white mb-1" />
              <span className="text-[9px] font-bold">Terminaldan olinmoqda...</span>
            </div>
          )}
        </div>

        {/* Boshqaruv tugmalari */}
        <div className="flex-1 w-full space-y-2.5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-800 flex items-center gap-1.5">
              Face ID Yuz Surati
            </span>
            {preview && (
              <span className="text-[10px] font-bold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-full flex items-center gap-1">
                <Check size={11} /> Tayyor
              </span>
            )}
          </div>

          {/* Terminal tanlash (agar 2 tadan ko'p bo'lsa) */}
          {devices.length > 1 && (
            <div className="flex items-center gap-1.5 text-[11px] text-slate-500">
              <span>Terminal:</span>
              <select
                value={selectedDeviceId}
                onChange={(e) => setSelectedDeviceId(Number(e.target.value))}
                className="bg-white border border-slate-200 rounded-lg px-2 py-0.5 text-xs text-slate-800 font-semibold focus:outline-none"
              >
                {devices.map(d => (
                  <option key={d.id} value={d.id}>
                    {d.name} ({d.ip_address}) {d.status === 'online' ? '🟢' : '🔴'}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Tugmalar paneli */}
          <div className="grid grid-cols-2 gap-2">
            {/* 1. Terminal Face ID orqali rasmga olish */}
            <button
              type="button"
              onClick={handleCaptureFromTerminal}
              disabled={terminalLoading || devices.length === 0}
              className={`flex items-center justify-center gap-1.5 px-3 py-2 rounded-xl text-xs font-bold transition shadow-xs cursor-pointer disabled:opacity-50 ${
                isBlue 
                  ? 'bg-blue-50 hover:bg-blue-100 text-[#0084ff] border border-blue-200' 
                  : 'bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200'
              }`}
              title="Terminal oldida turgan shaxsni Face ID kamerasidan to'g'ridan-to'g'ri suratga tushirish"
            >
              {terminalLoading ? (
                <RefreshCw size={14} className="animate-spin" />
              ) : (
                <Server size={14} />
              )}
              <span>Face ID dan olish</span>
            </button>

            {/* 2. Kompyuter veb-kamerasi orqali */}
            <button
              type="button"
              onClick={startWebcam}
              className="flex items-center justify-center gap-1.5 px-3 py-2 bg-purple-50 hover:bg-purple-100 text-purple-700 border border-purple-200 rounded-xl text-xs font-bold transition shadow-xs cursor-pointer"
              title="Kompyuter yoki noutbuk veb-kamerasi orqali suratga tushirish"
            >
              <Video size={14} />
              <span>Veb-kamera</span>
            </button>

            {/* 3. Kompyuterdan fayl tanlash */}
            <label className="flex items-center justify-center gap-1.5 px-3 py-2 bg-white hover:bg-slate-100 text-slate-700 border border-slate-300 rounded-xl text-xs font-semibold transition shadow-xs cursor-pointer">
              <Upload size={14} className="text-slate-500" />
              <span>Fayl tanlash</span>
              <input
                type="file"
                accept="image/jpeg,image/png"
                onChange={handleFileChange}
                className="hidden"
              />
            </label>

            {/* 4. Suratni tozalash */}
            {preview ? (
              <button
                type="button"
                onClick={handleRemovePhoto}
                className="flex items-center justify-center gap-1.5 px-3 py-2 bg-rose-50 hover:bg-rose-100 text-rose-600 border border-rose-200 rounded-xl text-xs font-semibold transition shadow-xs cursor-pointer"
                title="Suratni bekor qilish / tozalash"
              >
                <Trash2 size={13} />
                <span>O'chirish</span>
              </button>
            ) : (
              <div className="text-[11px] text-slate-400 flex items-center justify-center italic">
                3 usuldan biri
              </div>
            )}
          </div>

          {/* Terminal xatolik xabari */}
          {terminalError && (
            <div className="bg-rose-50 border border-rose-200 rounded-xl p-2 text-rose-700 text-[11px] flex items-center gap-1.5 animate-in fade-in">
              <AlertCircle size={14} className="shrink-0" />
              <span>{terminalError}</span>
            </div>
          )}
        </div>
      </div>

      {/* VEB-KAMERA OYNAChASI (MODAL) */}
      {showWebcam && (
        <div className="fixed inset-0 bg-slate-900/80 backdrop-blur-sm flex items-center justify-center z-[70] p-4 animate-in fade-in duration-150">
          <div className="bg-white border border-slate-200 rounded-3xl p-5 w-full max-w-md shadow-2xl relative">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-3">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center">
                  <Camera size={18} />
                </div>
                <div>
                  <h4 className="text-sm font-bold text-slate-900">Veb-kamera orqali suratga olish</h4>
                  <p className="text-[10px] text-slate-400">Yuzingizni markazga to'g'rilang</p>
                </div>
              </div>
              <button
                onClick={stopWebcam}
                className="p-1.5 rounded-xl hover:bg-slate-100 text-slate-400 hover:text-slate-700 transition"
              >
                <X size={18} />
              </button>
            </div>

            {webcamError ? (
              <div className="p-6 text-center text-rose-600 text-xs bg-rose-50 rounded-2xl border border-rose-200 mb-3">
                <AlertCircle size={28} className="mx-auto mb-2 text-rose-500" />
                {webcamError}
              </div>
            ) : (
              <div className="relative rounded-2xl overflow-hidden bg-black aspect-4/3 flex items-center justify-center mb-4">
                <video
                  ref={videoRef}
                  autoPlay
                  playsInline
                  muted
                  className="w-full h-full object-cover mirror"
                />
                {/* Oval yuz belgilagich ramka */}
                <div className="absolute inset-0 pointer-events-none border-2 border-white/30 rounded-2xl flex items-center justify-center">
                  <div className="w-48 h-60 border-2 border-dashed border-white/60 rounded-full" />
                </div>
              </div>
            )}

            <div className="flex gap-2">
              <button
                type="button"
                onClick={stopWebcam}
                className="flex-1 py-2.5 rounded-xl border border-slate-300 text-slate-700 font-semibold text-xs hover:bg-slate-50 transition"
              >
                Bekor qilish
              </button>
              <button
                type="button"
                onClick={captureWebcamSnapshot}
                disabled={!!webcamError}
                className="flex-1 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white font-bold text-xs transition shadow-md shadow-purple-600/30 flex items-center justify-center gap-2 cursor-pointer"
              >
                <Camera size={15} />
                <span>Suratga olish</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* TERMINAL FACE SCANNER ANIMATED HUD MODAL */}
      {terminalLoading && (
        <div className="fixed inset-0 z-[100] bg-slate-950/85 backdrop-blur-md flex items-center justify-center p-4 animate-in fade-in duration-200">
          <div className="relative w-full max-w-sm bg-gradient-to-b from-slate-900 to-slate-950 rounded-[32px] p-6 shadow-2xl border border-cyan-500/30 text-white flex flex-col items-center overflow-hidden">
            
            {/* Background ambient glow */}
            <div className="absolute -top-20 -left-20 w-44 h-44 bg-cyan-500/20 rounded-full blur-3xl pointer-events-none" />
            <div className="absolute -bottom-20 -right-20 w-44 h-44 bg-blue-600/20 rounded-full blur-3xl pointer-events-none" />

            {/* Top Device Bar */}
            <div className="w-full flex items-center justify-between mb-4 pb-3 border-b border-slate-800/80">
              <div className="flex items-center gap-2">
                <span className="relative flex h-3 w-3">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-cyan-500"></span>
                </span>
                <span className="text-xs font-semibold text-slate-300">
                  {selectedDevice?.name || "Face ID Terminal"}
                </span>
              </div>
              <span className="text-[11px] font-mono text-cyan-400/90 bg-cyan-950/70 px-2.5 py-0.5 rounded-md border border-cyan-800/50">
                {selectedDevice?.ip_address || "10.70.7.112"}
              </span>
            </div>

            {/* Terminal Viewport (Screen) */}
            <div className="relative w-64 h-80 rounded-2xl bg-slate-950 border border-cyan-500/40 shadow-inner overflow-hidden flex flex-col items-center justify-center">
              
              {/* Subtle grid pattern background */}
              <div 
                className="absolute inset-0 opacity-15"
                style={{
                  backgroundImage: `radial-gradient(circle, #38bdf8 1px, transparent 1px)`,
                  backgroundSize: '16px 16px'
                }}
              />

              {/* Viewfinder corner brackets */}
              <div className="absolute top-3 left-3 w-4 h-4 border-t-2 border-l-2 border-cyan-400 rounded-tl-sm" />
              <div className="absolute top-3 right-3 w-4 h-4 border-t-2 border-r-2 border-cyan-400 rounded-tr-sm" />
              <div className="absolute bottom-3 left-3 w-4 h-4 border-b-2 border-l-2 border-cyan-400 rounded-bl-sm" />
              <div className="absolute bottom-3 right-3 w-4 h-4 border-b-2 border-r-2 border-cyan-400 rounded-br-sm" />

              {/* Live scanning Laser Line */}
              <div 
                className="absolute left-4 right-4 h-0.5 bg-gradient-to-r from-transparent via-cyan-400 to-transparent shadow-[0_0_12px_#38bdf8] pointer-events-none animate-scan-beam"
              />

              {/* Oval Face Silhouette Guide (Exact Hikvision Screen Silhouette) */}
              <div className="relative w-40 h-52 rounded-[50%] border-2 border-cyan-400/70 shadow-[0_0_24px_rgba(56,189,248,0.3)] flex flex-col items-center justify-center overflow-hidden">
                
                {/* Inner subtle pulse */}
                <div className="absolute inset-0 bg-cyan-500/5 animate-pulse" />

                {/* Biometric facial points */}
                <div className="w-1.5 h-1.5 rounded-full bg-cyan-400/70 absolute top-12 left-10 animate-ping" />
                <div className="w-1.5 h-1.5 rounded-full bg-cyan-400/70 absolute top-12 right-10 animate-ping" />
                <div className="w-1 h-1 rounded-full bg-cyan-400/60 absolute top-24" />
                <div className="w-6 h-0.5 bg-cyan-400/40 rounded-full absolute bottom-14" />

                {/* Adding face started text (exact Hikvision message from terminal) */}
                <div className="z-10 bg-slate-950/85 backdrop-blur-sm px-3.5 py-1.5 rounded-xl border border-cyan-500/30 text-center shadow-lg">
                  <p className="text-[11px] font-bold text-white tracking-wide">Adding face started.</p>
                  <p className="text-[9px] text-cyan-300 font-medium mt-0.5">Yuz skanerlanmoqda...</p>
                </div>
              </div>

              {/* Bottom sensor indicator */}
              <div className="absolute bottom-3 flex items-center gap-1.5 text-[10px] text-slate-400">
                <Camera size={12} className="text-cyan-400 animate-pulse" />
                <span>Kameraga qarang</span>
              </div>
            </div>

            {/* Status Instruction */}
            <div className="mt-5 text-center space-y-1">
              <h4 className="text-sm font-bold text-slate-100 flex items-center justify-center gap-2">
                <RefreshCw size={14} className="animate-spin text-cyan-400" />
                Terminal orqali yuz skanerlanmoqda
              </h4>
              <p className="text-xs text-slate-400 max-w-xs">
                Xodim Face ID terminali kamerasiga qarab tursin. Surat avtomatik olinib dasturga yuklanadi.
              </p>
            </div>

            {/* Cancel button */}
            <button
              type="button"
              onClick={() => setTerminalLoading(false)}
              className="mt-4 px-6 py-2 rounded-xl bg-slate-800/80 hover:bg-slate-800 text-slate-300 hover:text-white text-xs font-semibold border border-slate-700 transition"
            >
              Bekor qilish
            </button>

            {/* Keyframe animation for scanning laser beam */}
            <style>{`
              @keyframes scanBeam {
                0% { top: 12%; opacity: 0.3; }
                50% { top: 84%; opacity: 1; }
                100% { top: 12%; opacity: 0.3; }
              }
              .animate-scan-beam {
                animation: scanBeam 2.2s ease-in-out infinite;
              }
            `}</style>
          </div>
        </div>
      )}
    </div>
  );
};
