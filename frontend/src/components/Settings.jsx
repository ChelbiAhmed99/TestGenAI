import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Settings as SettingsIcon, Globe, Cpu, GitBranch, Shield, Save, CheckCircle2, AlertTriangle, ChevronDown } from 'lucide-react';
import toast from 'react-hot-toast';

const MODELS = [
  { id: 'gemini-2.0-flash', label: 'Gemini 2.0 Flash', desc: 'Fast, cost-effective (recommended)', badge: 'Default' },
  { id: 'gemini-1.5-pro', label: 'Gemini 1.5 Pro', desc: 'High quality, slower', badge: null },
  { id: 'llama-3.3-70b-versatile', label: 'Llama 3.3 70B', desc: 'Meta Llama 3.3 via Groq API', badge: 'Free' },
  { id: 'llama-3.1-8b-instant', label: 'Llama 3.1 8B', desc: 'Fast Meta Llama 3.1 via Groq', badge: 'Free' },
];

const TOOLS = [
  { id: 'playwright', label: 'Playwright', desc: 'Modern E2E with TypeScript' },
  { id: 'selenium', label: 'Selenium', desc: 'Classic cross-browser testing' },
  { id: 'karate', label: 'Karate DSL', desc: 'API testing framework' },
];

const stagger = { hidden: { opacity: 0 }, visible: { opacity: 1, transition: { staggerChildren: 0.06 } } };
const itemAnim = { hidden: { opacity: 0, y: 12 }, visible: { opacity: 1, y: 0 } };

export default function Settings() {
  const loadSettings = () => {
    try { 
      const loaded = JSON.parse(localStorage.getItem('tg_settings') || '{}'); 
      if (loaded.aiModel && loaded.aiModel.includes('llama3-')) {
        loaded.aiModel = loaded.aiModel.includes('70b') ? 'llama-3.3-70b-versatile' : 'llama-3.1-8b-instant';
        localStorage.setItem('tg_settings', JSON.stringify(loaded));
      }
      return loaded;
    } catch { return {}; }
  };

  const [settings, setSettings] = useState(() => ({
    aiModel: 'gemini-2.0-flash',
    googleApiKey: '',
    groqApiKey: '',
    tool: 'playwright',
    language: 'en',
    theme: 'system',
    gitlabUrl: 'https://gitlab.com',
    gitlabToken: '',
    gitlabNamespace: '',
    jiraBaseUrl: '',
    jiraEmail: '',
    jiraToken: '',
    ...loadSettings(),
  }));

  const update = (key, val) => setSettings(prev => ({ ...prev, [key]: val }));

  const applyTheme = (theme) => {
    const root = document.documentElement;
    if (theme === 'dark' || (theme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
  };

  const handleSave = () => {
    localStorage.setItem('tg_settings', JSON.stringify(settings));
    applyTheme(settings.theme);
    toast.success('Settings saved successfully');
  };

  const SectionTitle = ({ icon: Icon, title, sub }) => (
    <div className="flex items-center gap-4 mb-6">
      <div className="w-10 h-10 rounded-xl bg-red-500/10 border border-red-500/20 flex items-center justify-center"><Icon className="w-5 h-5 text-red-400" /></div>
      <div><h3 className="text-[16px] font-bold text-[var(--text-primary)]">{title}</h3><p className="text-xs text-[var(--text-muted)] mt-0.5">{sub}</p></div>
    </div>
  );

  const inputCls = "w-full px-4 py-3 text-sm bg-[var(--bg-input)] border border-[var(--border-color)] rounded-xl outline-none focus:ring-2 focus:ring-red-500/20 focus:border-red-500 transition-all font-semibold text-[var(--text-primary)] placeholder:text-[var(--text-faint)]";

  return (
    <motion.div variants={stagger} initial="hidden" animate="visible" className="max-w-4xl mx-auto space-y-6 pb-12">
      {/* Header */}
      <motion.div variants={itemAnim} className="card p-6 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl primary-gradient flex items-center justify-center shadow-lg shadow-red-500/20">
            <SettingsIcon className="w-6 h-6 text-white" />
          </div>
          <div>
            <h2 className="text-xl font-black text-[var(--text-primary)] tracking-tight">Platform Settings</h2>
            <p className="text-sm text-[var(--text-secondary)] mt-0.5">Configure AI engines, integrations, and preferences</p>
          </div>
        </div>
        <button onClick={handleSave} className="hidden sm:flex items-center gap-2 px-5 py-2.5 primary-gradient rounded-xl text-sm font-bold text-white transition-all hover:opacity-90 active:scale-[0.98]">
          <Save className="w-4 h-4" /> Save All
        </button>
      </motion.div>

      {/* AI Engine */}
      <motion.div variants={itemAnim} className="card p-6">
        <SectionTitle icon={Cpu} title="AI Engine Configuration" sub="Select the LLM and test generation framework" />
        <div className="space-y-6">
          <div>
            <label className="block text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider mb-3">AI Model</label>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {MODELS.map((m) => (
                <button key={m.id} onClick={() => update('aiModel', m.id)}
                  className={`relative p-4 rounded-xl text-left transition-all border-2 ${settings.aiModel === m.id ? 'border-red-500/50 bg-red-500/5' : 'border-[var(--border-color)] bg-[var(--bg-hover)] hover:bg-[var(--bg-hover)]'}`}>
                  {settings.aiModel === m.id && <div className="absolute top-3 right-3 w-5 h-5 rounded-full bg-red-500 flex items-center justify-center"><CheckCircle2 className="w-3 h-3 text-white" /></div>}
                  <div className="text-[14px] font-bold text-[var(--text-primary)]">{m.label}</div>
                  <div className="text-[12px] text-[var(--text-muted)] mt-1">{m.desc}</div>
                  {m.badge && <span className="inline-block mt-2 text-[10px] font-black uppercase tracking-wider text-red-400 bg-red-500/10 px-2 py-0.5 rounded border border-red-500/20">{m.badge}</span>}
                </button>
              ))}
            </div>
          </div>
          <div>
            <label className="block text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider mb-3">Google API Key (Gemini Models)</label>
            <input type="password" value={settings.googleApiKey || ''} onChange={e => update('googleApiKey', e.target.value)} className={`${inputCls} tracking-widest placeholder:tracking-normal mb-4`} placeholder="AIzaSy..." />

            <label className="block text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider mb-3">Groq API Key (Llama 3 Models)</label>
            <input type="password" value={settings.groqApiKey || ''} onChange={e => update('groqApiKey', e.target.value)} className={`${inputCls} tracking-widest placeholder:tracking-normal`} placeholder="gsk_..." />
          </div>
          <div>
            <label className="block text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider mb-3">Test Framework</label>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {TOOLS.map((t) => (
                <button key={t.id} onClick={() => update('tool', t.id)}
                  className={`p-4 rounded-xl text-left transition-all border-2 ${settings.tool === t.id ? 'border-red-500/50 bg-red-500/5' : 'border-[var(--border-color)] bg-[var(--bg-hover)] hover:bg-[var(--bg-hover)]'}`}>
                  <div className="text-[14px] font-bold text-[var(--text-primary)]">{t.label}</div>
                  <div className="text-[12px] text-[var(--text-muted)] mt-1">{t.desc}</div>
                </button>
              ))}
            </div>
          </div>
        </div>
      </motion.div>

      {/* GitLab Integration */}
      <motion.div variants={itemAnim} className="card p-6">
        <SectionTitle icon={GitBranch} title="GitLab Integration" sub="Configure GitLab CI/CD push settings" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          <div><label className="block text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider mb-2">GitLab URL</label><input value={settings.gitlabUrl} onChange={e => update('gitlabUrl', e.target.value)} className={inputCls} placeholder="https://gitlab.com" /></div>
          <div><label className="block text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider mb-2">Namespace</label><input value={settings.gitlabNamespace} onChange={e => update('gitlabNamespace', e.target.value)} className={inputCls} placeholder="my-group" /></div>
          <div className="md:col-span-2">
            <label className="block text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider mb-2">Personal Access Token</label>
            <input type="password" value={settings.gitlabToken} onChange={e => update('gitlabToken', e.target.value)} className={`${inputCls} tracking-widest placeholder:tracking-normal`} placeholder="glpat-xxxxxxxxxxxxxxxxxxxx" />
            <div className="flex items-center gap-2 mt-3 p-3 rounded-xl bg-amber-500/5 border border-amber-500/10">
              <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0" />
              <p className="text-[12px] text-amber-400 font-medium">Token requires <code className="text-xs bg-[var(--bg-hover)] px-1.5 py-0.5 rounded font-bold">api</code>, <code className="text-xs bg-[var(--bg-hover)] px-1.5 py-0.5 rounded font-bold">write_repository</code> scopes</p>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Jira Integration */}
      <motion.div variants={itemAnim} className="card p-6">
        <SectionTitle icon={Globe} title="Jira Integration" sub="Connect to Atlassian Jira Cloud for automatic import" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          <div><label className="block text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider mb-2">Jira Base URL</label><input value={settings.jiraBaseUrl} onChange={e => update('jiraBaseUrl', e.target.value)} className={inputCls} placeholder="https://company.atlassian.net" /></div>
          <div><label className="block text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider mb-2">Atlassian Email</label><input value={settings.jiraEmail} onChange={e => update('jiraEmail', e.target.value)} className={inputCls} placeholder="user@company.com" /></div>
          <div className="md:col-span-2">
            <label className="block text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider mb-2">API Token</label>
            <input type="password" value={settings.jiraToken} onChange={e => update('jiraToken', e.target.value)} className={`${inputCls} tracking-widest placeholder:tracking-normal`} placeholder="••••••••••••••••" />
          </div>
        </div>
      </motion.div>

      {/* Preferences */}
      <motion.div variants={itemAnim} className="card p-6">
        <SectionTitle icon={Shield} title="Preferences" sub="Localization and display" />
        <div>
          <label className="block text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider mb-2">Interface Language</label>
          <select value={settings.language} onChange={e => update('language', e.target.value)} className={`${inputCls} cursor-pointer`}>
            <option value="en">English</option>
            <option value="fr">Français</option>
          </select>
        </div>
      </motion.div>

      {/* Mobile Save */}
      <motion.div variants={itemAnim} className="sm:hidden">
        <button onClick={handleSave} className="w-full py-4 primary-gradient rounded-xl text-sm font-bold text-white flex items-center justify-center gap-2 active:scale-[0.98]">
          <Save className="w-4 h-4" /> Save All Settings
        </button>
      </motion.div>
    </motion.div>
  );
}
