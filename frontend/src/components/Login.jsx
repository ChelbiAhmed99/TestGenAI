import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Lock, Mail, ArrowRight, User, ShieldCheck, CheckCircle2, Zap, Sun, Moon } from 'lucide-react';
import { apiService } from '../services/api';
import { useTheme } from '../hooks/ThemeContext';

export default function Login({ onLogin }) {
  const [isRegister, setIsRegister] = useState(false);
  const [isForgotPassword, setIsForgotPassword] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [username, setUsername] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { isDark, toggleTheme } = useTheme();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    try {
      if (isForgotPassword) {
        const data = await apiService.forgotPassword(email);
        setError(data.message || 'Password reset link sent.');
      } else if (isRegister) {
        await apiService.register(username, email, password);
        setIsRegister(false);
        setError('Registration successful. Please login.');
      } else {
        const data = await apiService.login(username, password);
        localStorage.setItem('token', data.access_token);
        onLogin(data.access_token);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const inputStyle = { background: 'var(--bg-input)', border: '1px solid var(--border-color)', color: 'var(--text-primary)' };
  const inputCls = "w-full pl-12 pr-4 py-3.5 rounded-xl text-[14px] focus:border-red-500 focus:ring-2 focus:ring-red-500/20 outline-none transition-all font-semibold";
  const labelStyle = { color: 'var(--text-muted)' };
  const iconStyle = { color: 'var(--text-muted)' };

  const features = [
    { icon: Zap, text: 'Instant Gherkin & Playwright TS Generation' },
    { icon: ShieldCheck, text: 'Enterprise-grade Page Object Model' },
    { icon: CheckCircle2, text: 'One-click GitLab CI/CD Orchestration' }
  ];

  return (
    <div className="min-h-screen w-full flex font-sans overflow-hidden" style={{ background: 'var(--bg-primary)' }}>
      <button onClick={toggleTheme} className="fixed top-6 right-6 z-50 p-2.5 rounded-xl transition-all active:scale-95" style={{ background: 'var(--bg-hover)', border: '1px solid var(--border-color)', color: 'var(--text-muted)' }} title={isDark ? 'Light Mode' : 'Dark Mode'}>
        {isDark ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-indigo-500" />}
      </button>

      {/* LEFT: Branding */}
      <div className="hidden lg:flex flex-col justify-between w-[45%] max-w-[600px] p-12 relative overflow-hidden" style={{ background: 'var(--bg-secondary)', borderRight: '1px solid var(--border-color)' }}>
        <div className="absolute top-[-10%] right-[-20%] w-[500px] h-[500px] bg-red-600/8 rounded-full blur-[100px]" />
        <div className="absolute bottom-[-10%] left-[-10%] w-[600px] h-[600px] bg-red-500/5 rounded-full blur-[120px]" />
        <div className="relative z-10">
          <div className="flex items-center gap-3 mb-16">
            <div className="w-12 h-12 bg-gradient-to-br from-red-600 to-red-500 rounded-xl shadow-lg shadow-red-500/20 flex items-center justify-center">
              <span className="text-white font-black text-2xl">D</span>
            </div>
            <div>
              <span className="text-xl font-black tracking-tight leading-none block" style={{ color: 'var(--text-primary)' }}>Devoteam</span>
              <span className="text-[10px] font-bold text-red-400 tracking-widest uppercase block mt-0.5">TestGenAI Platform</span>
            </div>
          </div>
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
            <h1 className="text-4xl font-black leading-[1.15] tracking-tight mb-6" style={{ color: 'var(--text-primary)' }}>
              AI-Driven Quality<br />Engineering
              <span className="text-gradient-brand block">at Enterprise Scale.</span>
            </h1>
            <p className="text-[15px] font-medium leading-relaxed max-w-md" style={{ color: 'var(--text-secondary)' }}>
              Transform requirements into automated test pipelines in seconds with Gemini AI and Playwright architecture.
            </p>
          </motion.div>
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="mt-12 space-y-4">
            {features.map((f, i) => (
              <div key={i} className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: 'var(--bg-hover)', border: '1px solid var(--border-color)' }}>
                  <f.icon className="w-4 h-4 text-red-400" />
                </div>
                <span className="text-sm font-bold" style={{ color: 'var(--text-primary)' }}>{f.text}</span>
              </div>
            ))}
          </motion.div>
        </div>
        <div className="relative z-10 pt-8 mt-12" style={{ borderTop: '1px solid var(--border-color)' }}>
          <p className="text-[11px] font-bold uppercase tracking-widest mb-4" style={{ color: 'var(--text-faint)' }}>Powered by</p>
          <span className="font-black text-xl tracking-tighter" style={{ color: 'var(--text-muted)' }}>Devoteam Group</span>
        </div>
      </div>

      {/* RIGHT: Form */}
      <div className="flex-1 flex flex-col items-center justify-center p-8 sm:p-12 relative" style={{ background: 'var(--bg-primary)' }}>
        <div className="w-full max-w-[420px]">
          <div className="lg:hidden flex flex-col items-center mb-10">
            <div className="w-16 h-16 bg-gradient-to-br from-red-600 to-red-500 rounded-2xl shadow-lg shadow-red-500/20 flex items-center justify-center mb-4">
              <span className="text-white font-black text-3xl">D</span>
            </div>
            <h2 className="text-2xl font-black tracking-tight" style={{ color: 'var(--text-primary)' }}>Devoteam</h2>
          </div>
          <div className="mb-10 text-center lg:text-left">
            <h2 className="text-3xl font-black tracking-tight mb-2" style={{ color: 'var(--text-primary)' }}>
              {isForgotPassword ? 'Reset Password' : isRegister ? 'Create an Account' : 'Welcome back'}
            </h2>
            <p className="text-sm font-medium" style={{ color: 'var(--text-secondary)' }}>
              {isForgotPassword ? 'Enter your email to receive a reset link' : isRegister ? 'Set up your enterprise profile' : 'Enter your credentials to access the platform'}
            </p>
          </div>
          <form onSubmit={handleSubmit} className="space-y-5">
            <AnimatePresence>
              {error && (
                <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }} className="overflow-hidden">
                  <div className={`p-4 text-[13px] font-bold rounded-xl flex items-center gap-3 border ${error.includes('successful') ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-red-500/10 text-red-400 border-red-500/20'}`}>
                    <div className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${error.includes('successful') ? 'bg-emerald-500' : 'bg-red-500'}`} />
                    {error}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
            {isForgotPassword ? (
              <div>
                <label className="block text-[11px] font-bold uppercase tracking-widest mb-2 ml-1" style={labelStyle}>Email</label>
                <div className="relative group">
                  <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 group-focus-within:text-red-400 transition-colors" style={iconStyle} />
                  <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} className={inputCls} style={inputStyle} placeholder="name@devoteam.com" required />
                </div>
              </div>
            ) : (
              <>
                {isRegister && (
                  <div>
                    <label className="block text-[11px] font-bold uppercase tracking-widest mb-2 ml-1" style={labelStyle}>Email</label>
                    <div className="relative group">
                      <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 group-focus-within:text-red-400 transition-colors" style={iconStyle} />
                      <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} className={inputCls} style={inputStyle} placeholder="name@devoteam.com" required />
                    </div>
                  </div>
                )}
                <div>
                  <label className="block text-[11px] font-bold uppercase tracking-widest mb-2 ml-1" style={labelStyle}>Username</label>
                  <div className="relative group">
                    <User className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 group-focus-within:text-red-400 transition-colors" style={iconStyle} />
                    <input type="text" value={username} onChange={(e) => setUsername(e.target.value)} className={inputCls} style={inputStyle} placeholder="admin" required />
                  </div>
                </div>
                <div>
                  <div className="flex items-center justify-between mb-2 ml-1">
                    <label className="block text-[11px] font-bold uppercase tracking-widest" style={labelStyle}>Password</label>
                    {!isRegister && (
                      <button type="button" onClick={() => { setIsForgotPassword(true); setError(''); }} className="text-[11px] font-bold text-red-400 hover:text-red-300 transition-colors">Forgot password?</button>
                    )}
                  </div>
                  <div className="relative group">
                    <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 group-focus-within:text-red-400 transition-colors" style={iconStyle} />
                    <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} className={`${inputCls} tracking-widest placeholder:tracking-normal`} style={inputStyle} placeholder="••••••••" required />
                  </div>
                </div>
              </>
            )}
            <button type="submit" disabled={isLoading} className="w-full mt-8 py-3.5 px-4 primary-gradient rounded-xl font-bold text-[14px] text-white transition-all flex items-center justify-center gap-2 active:scale-[0.98] disabled:opacity-70 hover:opacity-90">
              {isLoading ? <span className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : <>{isForgotPassword ? 'Send Reset Link' : isRegister ? 'Create Account' : 'Sign In'}<ArrowRight className="w-4 h-4" /></>}
            </button>
          </form>
          <div className="mt-10 text-center lg:text-left">
            <p className="text-[13px] font-medium" style={{ color: 'var(--text-muted)' }}>
              {isForgotPassword ? 'Remembered your password?' : isRegister ? 'Already have an account?' : "Don't have an account?"}{' '}
              <button onClick={() => { setIsRegister(isForgotPassword ? false : !isRegister); setIsForgotPassword(false); setError(''); }} className="font-bold hover:text-red-400 transition-colors ml-1" style={{ color: 'var(--text-primary)' }}>
                {isForgotPassword ? 'Back to login' : isRegister ? 'Sign in instead' : 'Create one'}
              </button>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
