import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { CheckCircle, XCircle, Clock, Database, ExternalLink, Loader2, ChevronDown, ChevronUp, Search, Terminal, Timer } from 'lucide-react';
import { apiService } from '../services/api';

const STATUS = {
  passed: { bg: 'bg-emerald-500/10', text: 'text-emerald-400', border: 'border-emerald-500/20', iconBg: 'bg-emerald-500/10 border border-emerald-500/20', barColor: '#10B981' },
  Passed: { bg: 'bg-emerald-500/10', text: 'text-emerald-400', border: 'border-emerald-500/20', iconBg: 'bg-emerald-500/10 border border-emerald-500/20', barColor: '#10B981' },
  failed: { bg: 'bg-red-500/10', text: 'text-red-400', border: 'border-red-500/20', iconBg: 'bg-red-500/10 border border-red-500/20', barColor: '#EF4444' },
  Failed: { bg: 'bg-red-500/10', text: 'text-red-400', border: 'border-red-500/20', iconBg: 'bg-red-500/10 border border-red-500/20', barColor: '#EF4444' },
};

const stagger = { hidden: { opacity: 0 }, visible: { opacity: 1, transition: { staggerChildren: 0.05 } } };
const itemAnim = { hidden: { opacity: 0, y: 12 }, visible: { opacity: 1, y: 0 } };

export default function ExecutionHistory() {
  const [executions, setExecutions] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [expanded, setExpanded] = useState(null);
  const [filter, setFilter] = useState('all');
  const [search, setSearch] = useState('');

  useEffect(() => { (async () => { try { const d = await apiService.getExecutions(); setExecutions(d || []); } catch { } finally { setIsLoading(false); } })(); }, []);

  const filtered = executions.filter(e => {
    const st = (e.status || '').toLowerCase();
    const matchF = filter === 'all' || st === filter.toLowerCase();
    const matchS = `Script #${e.test_script_id}`.toLowerCase().includes(search.toLowerCase());
    return matchF && matchS;
  });

  const summary = {
    total: executions.length,
    passed: executions.filter(e => (e.status || '').toLowerCase() === 'passed').length,
    failed: executions.filter(e => (e.status || '').toLowerCase() === 'failed').length,
    avgDuration: executions.length ? (executions.reduce((a, e) => a + (e.duration || 0), 0) / executions.length).toFixed(1) : 0,
  };

  return (
    <motion.div variants={stagger} initial="hidden" animate="visible" className="space-y-6">
      {/* KPIs */}
      <motion.div variants={itemAnim} className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {[
          { label: 'Total Runs', value: summary.total, icon: Database, bg: 'rgba(237, 28, 36, 0.1)', ic: '#ED1C24' },
          { label: 'Passed', value: summary.passed, icon: CheckCircle, bg: 'rgba(16, 185, 129, 0.1)', ic: '#34D399' },
          { label: 'Failed', value: summary.failed, icon: XCircle, bg: 'rgba(239, 68, 68, 0.1)', ic: '#F87171' },
          { label: 'Avg Duration', value: `${summary.avgDuration}s`, icon: Timer, bg: 'rgba(245, 158, 11, 0.1)', ic: '#FBBF24' },
        ].map((k) => (
          <div key={k.label} className="card p-5">
            <div className="flex items-start justify-between mb-4"><div className="p-2.5 rounded-xl" style={{ background: k.bg }}><k.icon className="w-5 h-5" style={{ color: k.ic }} /></div></div>
            <div className="text-3xl font-black text-[var(--text-primary)] tracking-tight">{k.value}</div>
            <div className="text-xs font-bold text-[var(--text-muted)] mt-1 uppercase tracking-wider">{k.label}</div>
          </div>
        ))}
      </motion.div>

      {/* Toolbar */}
      <motion.div variants={itemAnim} className="card p-5 flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1"><Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--text-muted)]" />
          <input value={search} onChange={e => setSearch(e.target.value)} type="text" placeholder="Search executions…"
            className="w-full pl-11 pr-4 py-3 text-sm bg-[var(--bg-input)] border border-[var(--border-color)] rounded-xl outline-none focus:ring-2 focus:ring-red-500/20 focus:border-red-500 transition-all text-[var(--text-primary)] placeholder:text-[var(--text-faint)]" />
        </div>
        <div className="flex items-center gap-2">
          {['all', 'passed', 'failed'].map(f => (
            <button key={f} onClick={() => setFilter(f)} className={`px-4 py-2.5 rounded-xl text-[13px] font-bold capitalize transition-all ${filter === f ? 'bg-red-600 text-[var(--text-primary)] shadow-lg shadow-red-500/25' : 'text-[var(--text-secondary)] bg-[var(--bg-hover)] border border-[var(--border-color)] hover:bg-[var(--bg-hover)]'}`}>{f === 'all' ? 'All' : f}</button>
          ))}
        </div>
      </motion.div>

      {/* Execution List */}
      {isLoading ? (
        <div className="card flex flex-col items-center justify-center py-24 gap-4"><Loader2 className="w-8 h-8 animate-spin text-red-500" /><p className="text-sm text-[var(--text-muted)] font-bold uppercase tracking-wider">Loading…</p></div>
      ) : filtered.length === 0 ? (
        <motion.div variants={itemAnim} className="card py-24 text-center">
          <div className="w-20 h-20 bg-[var(--bg-hover)] border border-[var(--border-color)] rounded-2xl flex items-center justify-center mx-auto mb-6"><Database className="w-10 h-10 text-[var(--text-faint)]" /></div>
          <p className="text-[15px] font-bold text-[var(--text-primary)]">No execution records</p>
          <p className="text-sm text-[var(--text-muted)] mt-2">{search || filter !== 'all' ? 'Try adjusting filters' : 'Run a test to populate'}</p>
        </motion.div>
      ) : (
        <div className="space-y-4">
          {filtered.map((exe) => {
            const st = (exe.status || 'failed').toLowerCase();
            const s = STATUS[st] || STATUS.failed;
            const isOpen = expanded === exe.id;
            const dateStr = exe.executed_at || exe.created_at;
            return (
              <motion.div key={exe.id} variants={itemAnim} className="card overflow-hidden">
                <div className={`flex items-center gap-5 px-6 py-5 cursor-pointer hover:bg-[var(--bg-hover)] transition-colors ${isOpen ? 'border-b border-[var(--border-color)] bg-[var(--bg-hover)]' : ''}`} onClick={() => setExpanded(isOpen ? null : exe.id)}>
                  <div className={`w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0 ${s.iconBg}`}>
                    {st === 'passed' ? <CheckCircle className="w-6 h-6 text-emerald-400" /> : <XCircle className="w-6 h-6 text-red-400" />}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 flex-wrap">
                      <span className="text-[15px] font-bold text-[var(--text-primary)]">Script #{exe.test_script_id}</span>
                      <span className="text-[11px] font-bold px-2.5 py-1 rounded-md bg-[var(--bg-hover)] text-[var(--text-muted)] font-mono tracking-widest border border-[var(--border-color)]">EXE-{exe.id}</span>
                      <span className={`text-[11px] font-bold px-2.5 py-1 rounded-md border uppercase tracking-wider ${s.bg} ${s.text} ${s.border}`}>{exe.status}</span>
                    </div>
                    <div className="flex items-center gap-4 mt-2">
                      <span className="text-[12px] text-[var(--text-muted)] flex items-center gap-1.5"><Clock className="w-3.5 h-3.5" />{dateStr ? new Date(dateStr).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : '—'}</span>
                      <span className="text-[12px] text-[var(--text-muted)] flex items-center gap-1.5"><Timer className="w-3.5 h-3.5" />{exe.duration}s</span>
                    </div>
                  </div>
                  <div className="hidden sm:flex flex-col items-end gap-1.5 flex-shrink-0 mr-4">
                    <span className="text-[13px] font-bold text-[var(--text-secondary)]">{exe.duration}s</span>
                    <div className="w-28 h-2 bg-[var(--bg-hover)] rounded-full overflow-hidden"><div className="h-full rounded-full" style={{ width: `${Math.min((exe.duration / 10) * 100, 100)}%`, background: s.barColor }} /></div>
                  </div>
                  <button className="p-2 rounded-xl text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)] transition-all flex-shrink-0">{isOpen ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}</button>
                </div>
                {isOpen && (
                  <div className="bg-[var(--bg-input)]">
                    <div className="flex items-center justify-between px-6 py-3.5 border-b border-[var(--border-color)] bg-[var(--bg-input)]">
                      <div className="flex items-center gap-2.5"><Terminal className="w-4 h-4 text-[var(--text-muted)]" /><span className="text-[11px] text-[var(--text-muted)] font-mono font-bold uppercase tracking-widest">stdout · Docker Container</span></div>
                      <button className="flex items-center gap-1.5 text-[11px] font-bold text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors"><ExternalLink className="w-3.5 h-3.5" /> Full log</button>
                    </div>
                    <div className="p-5">
                      <div className="bg-[var(--bg-input)] border border-[var(--border-color)] rounded-xl p-5 overflow-x-auto custom-scrollbar max-h-64">
                        <pre className={`text-[13px] font-mono leading-relaxed whitespace-pre-wrap ${st === 'passed' ? 'text-emerald-400' : 'text-red-300'}`}>{exe.output || `Test execution completed.\nStatus: ${exe.status}\nDuration: ${exe.duration}s`}</pre>
                      </div>
                    </div>
                  </div>
                )}
              </motion.div>
            );
          })}
        </div>
      )}
    </motion.div>
  );
}
