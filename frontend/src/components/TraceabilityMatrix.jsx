import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Link2, Shield, FileCheck, Bug, Loader2, CheckCircle2, XCircle, Clock, GitMerge, TrendingUp } from 'lucide-react';
import { apiService } from '../services/api';

const STATUS_CONFIG = {
  Passed: { label: 'Passed', bg: 'bg-emerald-500/10', text: 'text-emerald-400', border: 'border-emerald-500/20', dot: 'bg-emerald-500' },
  passed: { label: 'Passed', bg: 'bg-emerald-500/10', text: 'text-emerald-400', border: 'border-emerald-500/20', dot: 'bg-emerald-500' },
  Failed: { label: 'Failed', bg: 'bg-red-500/10', text: 'text-red-400', border: 'border-red-500/20', dot: 'bg-red-500' },
  failed: { label: 'Failed', bg: 'bg-red-500/10', text: 'text-red-400', border: 'border-red-500/20', dot: 'bg-red-500' },
  Pending: { label: 'Not Run', bg: 'bg-[var(--bg-hover)]', text: 'text-[var(--text-muted)]', border: 'border-[var(--border-color)]', dot: 'bg-slate-500' },
};

const stagger = { hidden: { opacity: 0 }, visible: { opacity: 1, transition: { staggerChildren: 0.04 } } };
const rowAnim = { hidden: { opacity: 0, x: -8 }, visible: { opacity: 1, x: 0 } };

export default function TraceabilityMatrix() {
  const [matrix, setMatrix] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filter, setFilter] = useState('all');

  useEffect(() => { (async () => { try { const d = await apiService.getTraceability(); setMatrix(d || []); } catch {} finally { setIsLoading(false); } })(); }, []);

  const normalize = (s) => s ? s.charAt(0).toUpperCase() + s.slice(1).toLowerCase() : 'Pending';
  const filtered = filter === 'all' ? matrix
    : filter === 'passed' ? matrix.filter(r => normalize(r.last_status) === 'Passed')
    : filter === 'failed' ? matrix.filter(r => normalize(r.last_status) === 'Failed')
    : matrix.filter(r => !r.last_status);

  const summary = {
    total: matrix.length,
    passed: matrix.filter(r => normalize(r.last_status) === 'Passed').length,
    failed: matrix.filter(r => normalize(r.last_status) === 'Failed').length,
    pending: matrix.filter(r => !r.last_status).length,
  };

  return (
    <motion.div variants={stagger} initial="hidden" animate="visible" className="space-y-6">
      {/* KPIs */}
      <motion.div variants={rowAnim} className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {[
          { label: 'Total Requirements', value: summary.total, icon: GitMerge, bg: 'rgba(237, 28, 36, 0.1)', ic: '#ED1C24' },
          { label: 'Test Coverage', value: `${summary.total > 0 ? Math.round(((summary.passed + summary.failed) / summary.total) * 100) : 0}%`, icon: TrendingUp, bg: 'rgba(139, 92, 246, 0.1)', ic: '#A78BFA' },
          { label: 'Passed', value: summary.passed, icon: CheckCircle2, bg: 'rgba(16, 185, 129, 0.1)', ic: '#34D399' },
          { label: 'Failed / Blocked', value: summary.failed, icon: XCircle, bg: 'rgba(239, 68, 68, 0.1)', ic: '#F87171' },
        ].map((k) => (
          <div key={k.label} className="card p-5">
            <div className="flex items-start justify-between mb-4"><div className="p-2.5 rounded-xl" style={{ background: k.bg }}><k.icon className="w-5 h-5" style={{ color: k.ic }} /></div></div>
            <div className="text-3xl font-black text-[var(--text-primary)] tracking-tight">{k.value}</div>
            <div className="text-xs font-bold text-[var(--text-muted)] mt-1 uppercase tracking-wider">{k.label}</div>
          </div>
        ))}
      </motion.div>

      {/* Filter Bar */}
      <motion.div variants={rowAnim} className="card p-5">
        <div className="flex items-center gap-3 flex-wrap">
          <span className="text-[13px] font-bold text-[var(--text-muted)] mr-2 uppercase tracking-widest">Status:</span>
          {[
            { id: 'all', label: `All (${summary.total})` },
            { id: 'passed', label: `Passed (${summary.passed})` },
            { id: 'failed', label: `Failed (${summary.failed})` },
            { id: 'pending', label: `Not Run (${summary.pending})` },
          ].map((f) => (
            <button key={f.id} onClick={() => setFilter(f.id)} className={`px-4 py-2 rounded-xl text-[13px] font-bold transition-all ${filter === f.id ? 'bg-red-600 text-[var(--text-primary)] shadow-lg shadow-red-500/25' : 'bg-[var(--bg-hover)] text-[var(--text-secondary)] hover:bg-[var(--bg-hover)] border border-[var(--border-color)]'}`}>{f.label}</button>
          ))}
        </div>
      </motion.div>

      {/* Matrix Table */}
      <motion.div variants={rowAnim} className="card overflow-hidden">
        {isLoading ? (
          <div className="flex flex-col items-center justify-center py-24 gap-4"><Loader2 className="w-8 h-8 animate-spin text-red-500" /><p className="text-sm text-[var(--text-muted)] font-bold uppercase tracking-wider">Building map…</p></div>
        ) : (
          <div className="overflow-x-auto custom-scrollbar">
            <table className="w-full min-w-[860px]">
              <thead>
                <tr className="border-b border-[var(--border-color)] bg-[var(--bg-hover)]">
                  {['Requirement', 'Scenario ID', 'Test Script', 'Execution Status', 'Risk'].map(h => (
                    <th key={h} className="px-6 py-4 text-left text-[11px] font-black text-[var(--text-muted)] uppercase tracking-widest">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.04]">
                {filtered.length === 0 ? (
                  <tr><td colSpan={5} className="py-24 text-center">
                    <div className="w-16 h-16 bg-[var(--bg-hover)] rounded-2xl flex items-center justify-center mx-auto mb-4 border border-[var(--border-color)]"><Shield className="w-8 h-8 text-[var(--text-faint)]" /></div>
                    <p className="text-[15px] font-bold text-[var(--text-primary)]">No traceability data</p>
                    <p className="text-sm text-[var(--text-muted)] mt-1.5">Analyze requirements and run tests to populate</p>
                  </td></tr>
                ) : filtered.map((row, i) => {
                  const statusKey = normalize(row.last_status);
                  const status = STATUS_CONFIG[statusKey] || STATUS_CONFIG.Pending;
                  const isFailedStatus = statusKey === 'Failed';
                  const isPassedStatus = statusKey === 'Passed';
                  return (
                    <motion.tr key={i} variants={rowAnim} className="hover:bg-[var(--bg-hover)] transition-colors group">
                      <td className="px-6 py-5">
                        <div className="flex items-center gap-4">
                          <div className="w-10 h-10 bg-red-500/10 rounded-xl flex items-center justify-center flex-shrink-0 border border-red-500/20 group-hover:bg-red-500/20 transition-colors"><FileCheck className="w-5 h-5 text-red-400" /></div>
                          <div><div className="text-[14px] font-bold text-[var(--text-secondary)] group-hover:text-[var(--text-primary)] transition-colors">{row.req_title}</div><div className="text-[11px] text-[var(--text-faint)] font-mono mt-1 font-semibold">REQ-{row.req_id}</div></div>
                        </div>
                      </td>
                      <td className="px-6 py-5">
                        {row.scenario_id ? <span className="inline-flex items-center gap-2 text-[11px] font-bold px-3 py-1.5 rounded-lg bg-violet-500/10 text-violet-400 border border-violet-500/20"><Link2 className="w-3.5 h-3.5" />SCN-{row.scenario_id}</span>
                        : <span className="text-[12px] text-[var(--text-faint)] italic">— No scenario</span>}
                      </td>
                      <td className="px-6 py-5">
                        {row.script_id ? <span className="inline-flex items-center gap-2 text-[11px] font-bold px-3 py-1.5 rounded-lg bg-blue-500/10 text-blue-400 border border-blue-500/20"><FileCheck className="w-3.5 h-3.5" />TST-{row.script_id}</span>
                        : <span className="text-[12px] text-[var(--text-faint)] italic">— Pending</span>}
                      </td>
                      <td className="px-6 py-5">
                        <span className={`inline-flex items-center gap-2 text-[11px] font-bold px-3 py-1.5 rounded-lg border ${status.bg} ${status.text} ${status.border}`}>
                          <span className={`w-1.5 h-1.5 rounded-full ${status.dot}`} />{status.label}
                        </span>
                      </td>
                      <td className="px-6 py-5">
                        {isFailedStatus ? <span className="inline-flex items-center gap-2 text-[11px] font-bold px-3 py-1.5 rounded-lg bg-red-500/10 text-red-400 border border-red-500/20"><Bug className="w-3.5 h-3.5" />Defect</span>
                        : isPassedStatus ? <span className="text-[12px] text-emerald-400 font-bold flex items-center gap-1.5"><CheckCircle2 className="w-4 h-4" />Clear</span>
                        : <span className="text-[12px] text-[var(--text-muted)] font-bold flex items-center gap-1.5"><Clock className="w-4 h-4" />Awaiting</span>}
                      </td>
                    </motion.tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </motion.div>
    </motion.div>
  );
}
