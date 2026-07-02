import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { ArrowUpRight, CheckCircle2, XCircle, Clock, FileText, Play, Zap, TrendingUp, Activity, AlertTriangle, BarChart3, Target, Layers, FolderDot, GitBranch, Loader2, Shield } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { apiService } from '../services/api';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-hot-toast';

const STAT_CARDS = [
  { label: 'Projets Créés', key: 'total_projects', default: 0, icon: FolderDot, bg: 'rgba(99, 102, 241, 0.1)', iconColor: '#818CF8' },
  { label: 'US Traitées', key: 'total_requirements', default: 0, icon: FileText, bg: 'rgba(245, 158, 11, 0.1)', iconColor: '#FBBF24' },
  { label: 'Scénarios Générés', key: 'total_scenarios', default: 0, icon: Zap, bg: 'rgba(16, 185, 129, 0.1)', iconColor: '#34D399' },
  { label: 'Code Implémenté', key: 'total_scripts', default: 0, icon: Play, bg: 'rgba(237, 28, 36, 0.1)', iconColor: '#ED1C24' },
];

const staggerContainer = { hidden: { opacity: 0 }, visible: { opacity: 1, transition: { staggerChildren: 0.07 } } };
const staggerItem = { hidden: { opacity: 0, y: 16 }, visible: { opacity: 1, y: 0, transition: { type: 'spring', stiffness: 300, damping: 24 } } };

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-[var(--bg-elevated)] border border-[var(--border-color)] rounded-xl p-3 shadow-xl text-xs">
      <div className="font-bold text-[var(--text-primary)] mb-2">{label}</div>
      {payload.map((p) => (
        <div key={p.name} className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full" style={{ background: p.color }} />
          <span className="text-[var(--text-secondary)] capitalize">{p.name}</span>
          <span className="font-bold text-[var(--text-primary)] ml-auto pl-4">{p.value}</span>
        </div>
      ))}
    </div>
  );
};

const Dashboard = ({ currentUser, onNewRequirement }) => {
  const [stats, setStats] = useState({ total_runs: 0, total_passed: 0, total_failed: 0, accuracy: 0, chart_data: [] });
  const [feed, setFeed] = useState([]);
  const [projects, setProjects] = useState([]);
  const [isLoadingProjects, setIsLoadingProjects] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [projectForm, setProjectForm] = useState({ name: '', type: 'Playwright', language: 'TypeScript', visibility: 'private' });
  const [isCreating, setIsCreating] = useState(false);
  const nav = useNavigate();

  const handleCreateProject = async (e) => {
    e.preventDefault();
    if (!projectForm.name) return;
    setIsCreating(true);
    try {
      const res = await apiService.createGithubProject(projectForm);
      if (res && res.github_url) {
        // Refresh projects list
        const projData = await apiService.getDashboardProjects();
        setProjects(projData);
        setShowCreateModal(false);
        toast.success(`Success! Project repository created at: ${res.github_url}`);
      }
    } catch (err) {
      toast.error(`Error creating project: ${err.message || 'Unknown error'}`);
    } finally {
      setIsCreating(false);
    }
  };

  useEffect(() => {
    (async () => {
      try {
        const [data, activity, projData] = await Promise.all([
          apiService.getDashboardStats().catch(() => null),
          apiService.getActivityFeed().catch(() => []),
          apiService.getDashboardProjects().catch(() => [])
        ]);
        if (data) setStats(data);
        if (activity?.length) setFeed(activity);
        if (projData) setProjects(projData);
      } catch (e) { /* use defaults */ }
      finally { setIsLoadingProjects(false); }
    })();
  }, []);

  const passRate = stats.total_passed + stats.total_failed > 0
    ? Math.round((stats.total_passed / (stats.total_passed + stats.total_failed)) * 100)
    : stats.accuracy || 0;

  return (
    <motion.div variants={staggerContainer} initial="hidden" animate="visible" className="space-y-6">
      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {STAT_CARDS.map((card) => {
          const Icon = card.icon;
          const value = stats[card.key] ?? card.default;
          return (
            <motion.div key={card.key} variants={staggerItem}>
              <div className="card p-5 transition-all duration-300 group cursor-default relative overflow-hidden">
          <div className="flex items-start justify-between mb-4 relative z-10">
                  <div className="p-2.5 rounded-xl" style={{ background: card.bg }}>
                    <Icon className="w-5 h-5" style={{ color: card.iconColor }} />
                  </div>
                </div>
                <div className="text-3xl font-black text-[var(--text-primary)] tracking-tight relative z-10">{value}{card.suffix || ''}</div>
                <div className="text-xs font-bold text-[var(--text-muted)] mt-1 uppercase tracking-wider relative z-10">{card.label}</div>
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <motion.div variants={staggerItem} className="lg:col-span-2 card p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-[16px] font-bold text-[var(--text-primary)]">Test Execution Trend</h3>
              <p className="text-xs text-[var(--text-muted)] mt-1">Last 7 days · Passed vs Failed</p>
            </div>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={stats.chart_data || []} margin={{ top: 4, right: 0, bottom: 0, left: -20 }}>
                <defs>
                  <linearGradient id="gPassed" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10B981" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#10B981" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="gFailed" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#EF4444" stopOpacity={0.2} />
                    <stop offset="95%" stopColor="#EF4444" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border-color)" />
                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: 'var(--text-muted)', fontSize: 11, fontWeight: 600 }} />
                <YAxis axisLine={false} tickLine={false} tick={{ fill: 'var(--text-muted)', fontSize: 11, fontWeight: 600 }} width={28} />
                <Tooltip content={<CustomTooltip />} />
                <Area type="monotone" dataKey="passed" stroke="#10B981" strokeWidth={3} fill="url(#gPassed)" dot={false} activeDot={{ r: 6, strokeWidth: 0, fill: '#10B981' }} />
                <Area type="monotone" dataKey="failed" stroke="#EF4444" strokeWidth={3} strokeDasharray="4 2" fill="url(#gFailed)" dot={false} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          <div className="flex items-center gap-4 mt-6 pt-4 border-t border-[var(--border-color)]">
            <span className="flex items-center gap-2 text-xs font-bold text-[var(--text-muted)]"><span className="w-3 h-1 bg-emerald-500 rounded-full inline-block" />Passed</span>
            <span className="flex items-center gap-2 text-xs font-bold text-[var(--text-muted)]"><span className="w-3 h-1 bg-red-500 rounded-full inline-block" />Failed</span>
          </div>
        </motion.div>

        {/* Pass Rate Donut */}
        <motion.div variants={staggerItem} className="card p-6 flex flex-col relative overflow-hidden">
          <div className="absolute top-0 right-0 w-32 h-32 bg-red-500/5 rounded-full blur-3xl" />
          <div className="flex items-center justify-between mb-6 relative z-10">
            <div>
              <h3 className="text-[16px] font-bold text-[var(--text-primary)]">Pass Rate</h3>
              <p className="text-xs text-[var(--text-muted)] mt-1">Current cycle</p>
            </div>
            <div className="w-8 h-8 rounded-full bg-[var(--bg-hover)] flex items-center justify-center">
              <BarChart3 className="w-4 h-4 text-red-400" />
            </div>
          </div>
          <div className="flex-1 flex flex-col items-center justify-center relative z-10">
            <div className="relative w-36 h-36">
              <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
                <circle cx="50" cy="50" r="40" fill="none" stroke="var(--border-color)" strokeWidth="8" />
                <circle cx="50" cy="50" r="40" fill="none" stroke={passRate >= 80 ? '#10B981' : passRate >= 60 ? '#F59E0B' : '#EF4444'} strokeWidth="8" strokeLinecap="round" strokeDasharray={`${(passRate / 100) * 251.2} 251.2`} className="transition-all duration-1000" />
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-4xl font-black text-[var(--text-primary)]">{passRate}</span>
                <span className="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-widest mt-0.5">%</span>
              </div>
            </div>
            <div className="mt-6 text-center">
              <div className={`text-sm font-bold uppercase tracking-widest ${passRate >= 80 ? 'text-emerald-500' : passRate >= 60 ? 'text-amber-500' : 'text-red-500'}`}>
                {passRate >= 80 ? 'Excellent' : passRate >= 60 ? 'Needs Attention' : 'Critical'}
              </div>
              <div className="text-xs text-[var(--text-muted)] mt-1.5">{stats.total_passed} passed · {stats.total_failed} failed</div>
            </div>
          </div>
          <div className="mt-4 pt-4 border-t border-[var(--border-color)] grid grid-cols-2 gap-3 relative z-10">
            <div className="text-center p-2 rounded-xl bg-[var(--bg-hover)]">
              <div className="text-xl font-black text-[var(--text-primary)]">{stats.total_passed}</div>
              <div className="text-[10px] text-emerald-500 font-bold uppercase tracking-wider mt-0.5">Passed</div>
            </div>
            <div className="text-center p-2 rounded-xl bg-[var(--bg-hover)]">
              <div className="text-xl font-black text-[var(--text-primary)]">{stats.total_failed}</div>
              <div className="text-[10px] text-red-500 font-bold uppercase tracking-wider mt-0.5">Failed</div>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Quick Actions + Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <motion.div variants={staggerItem} className="card p-6 space-y-3">
          <h3 className="text-[16px] font-bold text-[var(--text-primary)] mb-5">Quick Actions</h3>
          {currentUser?.role?.toLowerCase() === 'user' ? (
            <div className="text-center py-8 opacity-60">
              <Shield className="w-8 h-8 mx-auto mb-2 text-[var(--text-muted)]" />
              <p className="text-sm font-bold text-[var(--text-secondary)]">Restricted Access</p>
              <p className="text-xs text-[var(--text-muted)] mt-1">Actions disabled for guest accounts.</p>
            </div>
          ) : (
            <>
              <button onClick={onNewRequirement} className="w-full flex items-center gap-3 p-4 rounded-xl primary-gradient text-white hover:opacity-90 active:scale-[0.98] transition-all text-left group">
                <div className="w-10 h-10 bg-white/20 backdrop-blur-sm rounded-xl flex items-center justify-center flex-shrink-0">
                  <Zap className="w-5 h-5" />
                </div>
                <div className="flex-1">
                  <div className="text-[15px] font-bold leading-tight">Analyze New Requirement</div>
                  <div className="text-[11px] font-medium text-red-100 mt-1">AI-powered pipeline</div>
                </div>
                <ArrowUpRight className="w-5 h-5 opacity-70 group-hover:opacity-100 transition-all" />
              </button>

              <button onClick={() => setShowCreateModal(true)} className="w-full flex items-center gap-3 p-4 rounded-xl bg-[var(--bg-elevated)] border border-[var(--border-color)] hover:bg-[var(--bg-hover)] active:scale-[0.98] transition-all text-left group">
                <div className="w-10 h-10 bg-[var(--bg-hover-strong)] rounded-xl flex items-center justify-center flex-shrink-0">
                  <FolderDot className="w-5 h-5 text-indigo-500 dark:text-indigo-400" />
                </div>
                <div className="flex-1">
                  <div className="text-[15px] font-bold text-[var(--text-primary)] leading-tight">Créer un projet</div>
                  <div className="text-[11px] font-medium text-[var(--text-muted)] mt-1">Playwright, Selenium...</div>
                </div>
                <ArrowUpRight className="w-5 h-5 opacity-70 group-hover:opacity-100 transition-all text-[var(--text-secondary)]" />
              </button>

              {[
                { icon: Play, label: 'Run Test Suite', sub: 'Execute latest pipeline', onClick: () => nav('/execution') },
                { icon: Layers, label: 'View Traceability', sub: 'End-to-end mapping', onClick: () => nav('/matrix') },
                { icon: FileText, label: 'Export PDF Report', sub: 'Generate executive summary', onClick: () => apiService.exportReport?.(1) },
              ].map((a) => (
                <button key={a.label} onClick={a.onClick} className="w-full flex items-center gap-4 p-3.5 rounded-xl bg-[var(--bg-hover)] hover:bg-[var(--bg-hover-strong)] border border-[var(--border-color)] active:scale-[0.98] transition-all text-left group">
                  <div className="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 bg-[var(--bg-hover)] border border-[var(--border-color)]">
                    <a.icon className="w-4 h-4 text-[var(--text-secondary)]" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-[14px] font-bold text-[var(--text-secondary)] group-hover:text-[var(--text-primary)] transition-colors">{a.label}</div>
                    <div className="text-[11px] text-[var(--text-muted)] font-bold mt-0.5">{a.sub}</div>
                  </div>
                  <ArrowUpRight className="w-4 h-4 text-[var(--text-muted)] group-hover:text-[var(--text-secondary)] transition-colors flex-shrink-0" />
                </button>
              ))}
            </>
          )}
        </motion.div>

        <motion.div variants={staggerItem} className="lg:col-span-2 card p-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-[16px] font-bold text-[var(--text-primary)] flex items-center gap-2"><Activity className="w-4 h-4 text-red-500" />Live Activity</h3>
            <span className="text-[10px] font-bold text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 px-2 py-1 rounded-md uppercase tracking-wider flex items-center gap-1.5 border border-emerald-500/20">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 dark:bg-emerald-400 animate-pulse" />Real-time
            </span>
          </div>
          <div className="space-y-2">
            {feed.length === 0 ? (
              <div className="text-center py-12">
                <AlertTriangle className="w-8 h-8 text-[var(--text-muted)] mx-auto mb-3" />
                <p className="text-sm text-[var(--text-secondary)] font-bold">No recent activity</p>
                <p className="text-xs text-[var(--text-muted)] mt-1">Start by analyzing a requirement</p>
              </div>
            ) : feed.map((item, i) => (
              <div key={i} className="flex items-start gap-4 p-3.5 rounded-xl transition-colors hover:bg-[var(--bg-hover)] border border-transparent hover:border-[var(--border-color)]">
                <div className={`w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5 ${item.color === 'green' ? 'bg-emerald-500/10 border border-emerald-500/20' : item.color === 'blue' ? 'bg-blue-500/10 border border-blue-500/20' : 'bg-red-500/10 border border-red-500/20'}`}>
                  {item.icon === 'CheckCircle2' ? <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400" /> : item.icon === 'XCircle' ? <XCircle className="w-4 h-4 text-red-600 dark:text-red-400" /> : <FileText className="w-4 h-4 text-blue-600 dark:text-blue-400" />}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-[14px] text-[var(--text-secondary)] leading-snug">
                    <span className="font-bold text-[var(--text-primary)]">{item.user}</span>{' '}{item.action}{' '}<span className="font-bold text-red-500">{item.target}</span>
                  </p>
                  <p className="text-[11px] font-bold text-[var(--text-muted)] mt-1.5 flex items-center gap-1.5"><Clock className="w-3 h-3" />{item.time}</p>
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      </div>

      {/* Projects List Table */}
      <motion.div variants={staggerItem} className="card overflow-hidden">
        <div className="flex items-center justify-between p-6 border-b border-[var(--border-color)]">
          <h3 className="text-[16px] font-bold text-[var(--text-primary)] flex items-center gap-2"><FolderDot className="w-5 h-5 text-indigo-500 dark:text-indigo-400" /> Recent Projects</h3>
          <span className="text-xs font-bold text-[var(--text-muted)] bg-[var(--bg-hover)] border border-[var(--border-color)] px-3 py-1.5 rounded-lg">{projects.length} Total</span>
        </div>
        <div className="overflow-x-auto custom-scrollbar">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-[var(--bg-hover)]">
                <th className="px-6 py-4 text-xs font-bold text-[var(--text-muted)] uppercase tracking-widest whitespace-nowrap">Project Name</th>
                <th className="px-6 py-4 text-xs font-bold text-[var(--text-muted)] uppercase tracking-widest whitespace-nowrap">Creation Date</th>
                <th className="px-6 py-4 text-xs font-bold text-[var(--text-muted)] uppercase tracking-widest whitespace-nowrap">Creator</th>
                <th className="px-6 py-4 text-xs font-bold text-[var(--text-muted)] uppercase tracking-widest whitespace-nowrap">Repository</th>
                <th className="px-6 py-4 text-xs font-bold text-[var(--text-muted)] uppercase tracking-widest text-right whitespace-nowrap">Last Execution</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--border-color)]">
              {isLoadingProjects ? (
                <tr>
                  <td colSpan="5" className="px-6 py-12 text-center">
                    <Loader2 className="w-6 h-6 animate-spin text-[var(--text-muted)] mx-auto mb-2" />
                    <span className="text-sm font-bold text-[var(--text-secondary)]">Loading projects...</span>
                  </td>
                </tr>
              ) : projects.length === 0 ? (
                <tr>
                  <td colSpan="5" className="px-6 py-12 text-center">
                    <FolderDot className="w-8 h-8 text-[var(--text-muted)] mx-auto mb-3" />
                    <p className="text-sm font-bold text-[var(--text-secondary)]">No projects generated yet.</p>
                  </td>
                </tr>
              ) : projects.map((proj) => {
                const status = (proj.last_execution_status || 'unknown').toLowerCase();
                let badgeCls = 'bg-slate-500/10 text-slate-600 dark:text-slate-400 border-slate-500/20';
                if (status === 'passed') badgeCls = 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20';
                if (status === 'failed') badgeCls = 'bg-red-500/10 text-red-600 dark:text-red-400 border-red-500/20';

                return (
                  <tr key={proj.id} onClick={() => nav('/execution')} className="hover:bg-[var(--bg-hover)] transition-colors cursor-pointer group">
                    <td className="px-6 py-4">
                      <div className="font-bold text-[var(--text-primary)] group-hover:text-indigo-500 dark:group-hover:text-indigo-400 transition-colors">{proj.name}</div>
                    </td>
                    <td className="px-6 py-4 text-[13px] text-[var(--text-secondary)]">
                      {proj.created_at ? new Date(proj.created_at).toLocaleDateString() : '—'}
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <div className="w-6 h-6 rounded-full bg-[var(--bg-hover-strong)] flex items-center justify-center text-[10px] font-bold text-[var(--text-primary)] uppercase">
                          {proj.owner_username.charAt(0)}
                        </div>
                        <span className="text-[13px] font-medium text-[var(--text-secondary)]">{proj.owner_username}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      {proj.github_url ? (
                        <a href={proj.github_url} target="_blank" rel="noopener noreferrer" onClick={(e) => e.stopPropagation()} className="flex items-center gap-1.5 text-[13px] text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors">
                          <GitBranch className="w-4 h-4" /> Repository
                        </a>
                      ) : '—'}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex items-center justify-end gap-3">
                        <span className={`inline-flex items-center px-2.5 py-1 rounded-md text-[11px] font-bold uppercase tracking-widest border ${badgeCls}`}>
                          {status}
                        </span>
                        {proj.github_url && (status === 'passed' || status === 'failed') && (
                          <a
                            href={proj.github_url.replace('github.com/', '').split('/').map((part, i) => i === 0 ? `https://${part}.github.io/` : part).join('')}
                            target="_blank"
                            rel="noopener noreferrer"
                            onClick={(e) => e.stopPropagation()}
                            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[11px] font-bold bg-[var(--bg-hover)] hover:bg-[var(--bg-hover-strong)] text-[var(--text-secondary)] border border-[var(--border-color)] transition-all"
                            title="Open Allure Report"
                          >
                            <BarChart3 className="w-3.5 h-3.5 text-indigo-500 dark:text-indigo-400" /> Report
                          </a>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </motion.div>

      {/* Create Project Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-[var(--bg-modal-overlay)] backdrop-blur-sm px-4">
          <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="card w-full max-w-md overflow-hidden shadow-2xl">
            <div className="p-6 border-b border-[var(--border-color)] flex items-center justify-between">
              <h2 className="text-xl font-bold text-[var(--text-primary)]">Créer un Projet</h2>
              <button onClick={() => setShowCreateModal(false)} className="text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors">
                <XCircle className="w-6 h-6" />
              </button>
            </div>
            <form onSubmit={handleCreateProject} className="p-6 space-y-4">
              <div>
                <label className="block text-xs font-bold text-[var(--text-muted)] uppercase mb-1.5">Nom du projet</label>
                <input type="text" value={projectForm.name} onChange={e => setProjectForm({ ...projectForm, name: e.target.value })} required className="w-full bg-[var(--bg-input)] border border-[var(--border-color)] rounded-xl px-4 py-2.5 text-[var(--text-primary)] focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none transition-all" placeholder="ex: e2e-automation-suite" />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-[var(--text-muted)] uppercase mb-1.5">Type de projet</label>
                  <select value={projectForm.type} onChange={e => setProjectForm({ ...projectForm, type: e.target.value })} className="w-full bg-[var(--bg-input)] border border-[var(--border-color)] rounded-xl px-4 py-2.5 text-[var(--text-primary)] focus:border-indigo-500 outline-none">
                    <option value="Playwright">Playwright</option>
                    <option value="Selenium">Selenium</option>
                    <option value="Karate DSL">Karate DSL</option>
                    <option value="Gatling">Gatling</option>
                    <option value="Cypress">Cypress</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-bold text-[var(--text-muted)] uppercase mb-1.5">Langage</label>
                  <select value={projectForm.language} onChange={e => setProjectForm({ ...projectForm, language: e.target.value })} className="w-full bg-[var(--bg-input)] border border-[var(--border-color)] rounded-xl px-4 py-2.5 text-[var(--text-primary)] focus:border-indigo-500 outline-none">
                    <option value="TypeScript">TypeScript</option>
                    <option value="Java">Java</option>
                    <option value="Python">Python</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-xs font-bold text-[var(--text-muted)] uppercase mb-1.5">Visibilité du dépôt</label>
                <select value={projectForm.visibility} onChange={e => setProjectForm({ ...projectForm, visibility: e.target.value })} className="w-full bg-[var(--bg-input)] border border-[var(--border-color)] rounded-xl px-4 py-2.5 text-[var(--text-primary)] focus:border-indigo-500 outline-none">
                  <option value="private">Privé</option>
                  <option value="public">Public</option>
                </select>
              </div>
              <div className="pt-4 flex items-center justify-end gap-3">
                <button type="button" onClick={() => setShowCreateModal(false)} className="px-5 py-2.5 rounded-xl font-bold text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)] transition-colors">Annuler</button>
                <button type="submit" disabled={isCreating} className="px-5 py-2.5 rounded-xl font-bold text-white primary-gradient flex items-center gap-2 hover:opacity-90 transition-all disabled:opacity-50">
                  {isCreating && <Loader2 className="w-4 h-4 animate-spin" />}
                  {isCreating ? 'Création...' : 'Générer sur GitHub'}
                </button>
              </div>
            </form>
          </motion.div>
        </div>
      )}
    </motion.div>
  );
};

export default Dashboard;
