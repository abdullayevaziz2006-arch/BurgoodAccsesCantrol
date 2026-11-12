import React, { useState, useEffect } from 'react';
import { Lock, User, Eye, EyeOff, ShieldCheck, AlertCircle, ArrowRight } from 'lucide-react';
import { loginUser, getBranding } from '../api';
import { AuthResponse, BrandingInfo } from '../types';

interface LoginViewProps {
  onLoginSuccess: (authData: AuthResponse) => void;
}

export const LoginView: React.FC<LoginViewProps> = ({ onLoginSuccess }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [branding, setBranding] = useState<BrandingInfo | null>(null);

  useEffect(() => {
    getBranding()
      .then(b => setBranding(b))
      .catch(() => {});
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password.trim()) {
      setError("Login va parolni to'liq kiriting!");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const res = await loginUser(username.trim(), password.trim());
      if (res.success) {
        // Save to localStorage
        localStorage.setItem('burgood_token', res.token);
        localStorage.setItem('burgood_user', JSON.stringify(res.user));
        if (res.organization) {
          localStorage.setItem('burgood_org', JSON.stringify(res.organization));
        }
        onLoginSuccess(res);
      }
    } catch (err: any) {
      console.error("Login xatosi:", err);
      const detail = err.response?.data?.detail || "Login yoki parol noto'g'ri! Iltimos, qayta tekshiring.";
      setError(detail);
    } finally {
      setLoading(false);
    }
  };

  const logoSrc = '/burgood_shield.png';
  const orgTitle = 'Burgood Access Control';

  return (
    <div 
      className="min-h-screen w-full flex items-center justify-center p-4 relative overflow-hidden select-none"
      style={{ background: 'radial-gradient(circle at center, #0f1f3d 0%, #070c18 75%)' }}
    >
      {/* Decorative ambient background glows */}
      <div className="absolute -top-40 -left-40 w-96 h-96 bg-[#0084ff]/15 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute -bottom-40 -right-40 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />

      {/* Login Card */}
      <div className="w-full max-w-md bg-[#0a1224]/90 backdrop-blur-xl border border-[#19305d] rounded-3xl p-8 sm:p-10 shadow-2xl relative z-10">
        
        {/* Logo and Header */}
        <div className="text-center mb-8">
          <div className="relative inline-flex items-center justify-center mb-4">
            <div className="w-20 h-20 rounded-2xl bg-[#0f2347] border border-[#20407a] flex items-center justify-center shadow-lg shadow-[#0084ff]/20">
              <img 
                src={logoSrc} 
                alt="Logo" 
                className="w-14 h-14 object-contain filter drop-shadow-[0_0_12px_rgba(0,132,255,0.4)]"
              />
            </div>
          </div>

          <h1 className="text-xl sm:text-2xl font-black text-white tracking-tight">
            {orgTitle}
          </h1>
          <p className="text-xs text-cyan-400 font-medium tracking-widest uppercase mt-1">
            Face ID & Davomat Boshqaruv Tizimi
          </p>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mb-6 p-3.5 bg-rose-500/15 border border-rose-500/40 rounded-xl text-rose-300 text-xs flex items-center gap-2.5 animate-pulse">
            <AlertCircle size={18} className="text-rose-400 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Login Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5 ml-1">
              Foydalanuvchi nomi (Login)
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                <User size={18} />
              </div>
              <input
                type="text"
                autoFocus
                required
                placeholder="Loginni kiriting..."
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full pl-10 pr-4 py-3 bg-[#070e1c] border border-[#19305d] rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:border-[#0084ff] focus:ring-2 focus:ring-[#0084ff]/20 transition"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5 ml-1">
              Parol
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                <Lock size={18} />
              </div>
              <input
                type={showPassword ? 'text' : 'password'}
                required
                placeholder="Parolni kiriting..."
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full pl-10 pr-11 py-3 bg-[#070e1c] border border-[#19305d] rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:border-[#0084ff] focus:ring-2 focus:ring-[#0084ff]/20 transition"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-slate-400 hover:text-slate-200 transition"
              >
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full mt-2 py-3 px-4 rounded-xl bg-gradient-to-r from-[#0084ff] to-[#0066cc] hover:from-[#0073e0] hover:to-[#0055b3] text-white font-bold text-sm shadow-lg shadow-[#0084ff]/30 transition flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
          >
            {loading ? (
              <span>Tekshirilmoqda...</span>
            ) : (
              <>
                <span>Tizimga kirish</span>
                <ArrowRight size={17} />
              </>
            )}
          </button>
        </form>

        {/* Footer info */}
        <div className="mt-8 pt-6 border-t border-[#152747] text-center">
          <div className="flex items-center justify-center gap-1.5 text-xs text-slate-400 font-medium">
            <ShieldCheck size={15} className="text-cyan-400" />
            <span>Himoyalangan Boshqaruv Tizimi</span>
          </div>
          <p className="text-[11px] text-slate-400 mt-1">
            Burgood Access Control • v2.0
          </p>
        </div>

      </div>
    </div>
  );
};
