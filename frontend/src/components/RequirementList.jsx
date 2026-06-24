import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Search, FileText, Zap, Edit3, Trash2, Filter, SortDesc, CheckCircle2, Loader2, Calendar, X, Save } from 'lucide-react';
import { apiService } from '../services/api';
import toast from 'react-hot-toast';

const TYPE_CONFIG = {
  'USER_STORY': { label: 'User Story', bg: 'bg-blue-500/10', text: 'text-blue-400', dot: 'bg-blue-500' },
  'user-story': { label: 'User Story', bg: 'bg-blue-500/10', text: 'text-blue-400', dot: 'bg-blue-500' },
  'SWAGGER':   { label: 'Swagger API', bg: 'bg-violet-500/10', text: 'text-violet-400', dot: 'bg-violet-500' },
  'swagger':   { label: 'Swagger API', bg: 'bg-violet-500/10', text: 'text-violet-400', dot: 'bg-violet-500' },
  'DOCUMENT':  { label: 'Tech Doc', bg: 'bg-amber-500/10', text: 'text-amber-400', dot: 'bg-amber-500' },
  'docs':      { label: 'Tech Doc', bg: 'bg-amber-500/10', text: 'text-amber-400', dot: 'bg-amber-500' },
};

const stagger = { hidden: { opacity: 0 }, visible: { opacity: 1, transition: { staggerChildren: 0.04 } } };
const rowVariant = { hidden: { opacity: 0, x: -8 }, visible: { opacity: 1, x: 0 } };

export default function RequirementList({ onAnalyze }) {
  const [requirements, setRequirements] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [selectedIds, setSelectedIds] = useState([]);
  const [editingId, setEditingId] = useState(null);
  const [editTitle, setEditTitle] = useState('');
  const [deleteConfirm, setDeleteConfirm] = useState(null);

  useEffect(() => { fetchRequirements(); }, []);

  const fetchRequirements = async () => {
    setIsLoading(true);
    try {
      const data = await apiService.getRequirements();
      setRequirements(data || []);
    } catch { toast.error('Failed to load requirements'); }
    finally { setIsLoading(false); }
  };

  const handleAnalyze = async (req) => {
    const tid = toast.loading(`Generating AI pipeline for "${req.title}"…`);
    try {
      await apiService.analyzeRequirement(req.id);
      toast.success('Pipeline generated!', { id: tid });
      if (onAnalyze) onAnalyze(req.id);
    } catch { toast.error('AI generation failed', { id: tid }); }
  };

  const handleDelete = async (id) => {
    const tid = toast.loading('Deleting requirement…');
    try {
      await apiService.deleteRequirement(id);
      toast.success('Requirement deleted', { id: tid });
      setRequirements(prev => prev.filter(r => r.id !== id));
      setDeleteConfirm(null);
    } catch (e) { toast.error(e.message || 'Delete failed', { id: tid }); }
  };

  const handleEdit = async (id) => {
    if (!editTitle.trim()) return;
    const tid = toast.loading('Updating…');
    try {
      await apiService.updateRequirement(id, { title: editTitle });
      toast.success('Updated!', { id: tid });
      setRequirements(prev => prev.map(r => r.id === id ? { ...r, title: editTitle } : r));
      setEditingId(null);
    } catch (e) { toast.error(e.message || 'Update failed', { id: tid }); }
  };

  const filtered = requirements.filter(r =>
    r.title?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    r.type?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const toggleSelect = (id) => setSelectedIds(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]);

  return (
    <motion.div variants={stagger} initial="hidden" animate="visible" className="space-y-6">
      {/* Toolbar */}
      <motion.div variants={rowVariant} className="card p-5">
        <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center">
          <div className="relative flex-1 min-w-0">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--text-muted)]" />
            <input type="text" placeholder="Search requirements…" value={searchTerm} onChange={e => setSearchTerm(e.target.value)}
              className="w-full pl-11 pr-4 py-3 text-sm bg-[var(--bg-input)] border border-[var(--border-color)] rounded-xl outline-none focus:ring-2 focus:ring-red-500/20 focus:border-red-500 transition-all placeholder:text-[var(--text-faint)] text-[var(--text-primary)]" />
          </div>
          <div className="flex items-center gap-3 flex-shrink-0">
            <button className="flex items-center gap-2 px-4 py-3 text-sm font-bold text-[var(--text-secondary)] bg-[var(--bg-hover)] border border-[var(--border-color)] hover:bg-[var(--bg-hover)] rounded-xl transition-all"><Filter className="w-4 h-4" /><span className="hidden sm:inline">Filter</span></button>
            <button className="flex items-center gap-2 px-4 py-3 text-sm font-bold text-[var(--text-secondary)] bg-[var(--bg-hover)] border border-[var(--border-color)] hover:bg-[var(--bg-hover)] rounded-xl transition-all"><SortDesc className="w-4 h-4" /><span className="hidden sm:inline">Sort</span></button>
          </div>
        </div>
        <div className="flex items-center gap-4 mt-4 pt-4 border-t border-[var(--border-color)]">
          <span className="text-xs text-[var(--text-muted)]"><span className="font-bold text-[var(--text-primary)] text-sm">{filtered.length}</span> requirements</span>
          {selectedIds.length > 0 && (
            <span className="flex items-center gap-2 text-xs text-red-400 font-bold bg-red-500/10 px-3 py-1 rounded-lg border border-red-500/20">
              <CheckCircle2 className="w-4 h-4" />{selectedIds.length} selected
            </span>
          )}
        </div>
      </motion.div>

      {/* Delete Confirmation Modal */}
      {deleteConfirm !== null && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={() => setDeleteConfirm(null)}>
          <div className="card p-8 max-w-sm w-full mx-4" onClick={e => e.stopPropagation()}>
            <h3 className="text-lg font-bold text-[var(--text-primary)] mb-2">Delete Requirement?</h3>
            <p className="text-sm text-[var(--text-secondary)] mb-6">This action cannot be undone. All linked scenarios and scripts will also be removed.</p>
            <div className="flex gap-3">
              <button onClick={() => setDeleteConfirm(null)} className="flex-1 py-2.5 rounded-xl text-sm font-bold text-[var(--text-secondary)] bg-[var(--bg-hover)] border border-[var(--border-color)] hover:bg-[var(--bg-hover-strong)] transition-all">Cancel</button>
              <button onClick={() => handleDelete(deleteConfirm)} className="flex-1 py-2.5 rounded-xl text-sm font-bold text-[var(--text-primary)] bg-red-600 hover:bg-red-700 transition-all">Delete</button>
            </div>
          </div>
        </div>
      )}

      {/* Table */}
      <motion.div variants={rowVariant} className="card overflow-hidden">
        {isLoading ? (
          <div className="flex flex-col items-center justify-center py-24 gap-4">
            <Loader2 className="w-8 h-8 animate-spin text-red-500" />
            <p className="text-sm text-[var(--text-muted)] font-bold tracking-wider uppercase">Loading requirements…</p>
          </div>
        ) : (
          <div className="overflow-x-auto custom-scrollbar">
            <table className="w-full min-w-[720px]">
              <thead>
                <tr className="border-b border-[var(--border-color)] bg-[var(--bg-hover)]">
                  <th className="px-6 py-4 text-left w-12">
                    <input type="checkbox" className="w-4 h-4 rounded bg-[var(--bg-input)] border-[var(--border-color)] text-red-500 focus:ring-red-500"
                      onChange={e => setSelectedIds(e.target.checked ? filtered.map(r => r.id) : [])}
                      checked={selectedIds.length === filtered.length && filtered.length > 0} />
                  </th>
                  {['Title', 'Type', 'Project', 'Created', 'Actions'].map(h => (
                    <th key={h} className="px-6 py-4 text-left text-[11px] font-black text-[var(--text-muted)] uppercase tracking-widest">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.04]">
                {filtered.length === 0 ? (
                  <tr><td colSpan={6} className="py-24 text-center">
                    <div className="w-16 h-16 bg-[var(--bg-hover)] rounded-2xl flex items-center justify-center mx-auto mb-4 border border-[var(--border-color)]"><FileText className="w-8 h-8 text-[var(--text-faint)]" /></div>
                    <p className="text-[15px] font-bold text-[var(--text-secondary)]">{searchTerm ? 'No results found' : 'No requirements yet'}</p>
                    <p className="text-sm text-[var(--text-faint)] mt-1.5">{searchTerm ? 'Try adjusting your search' : 'Click "New Requirement" to add one'}</p>
                  </td></tr>
                ) : filtered.map((req) => {
                  const typeConf = TYPE_CONFIG[req.type] || TYPE_CONFIG['DOCUMENT'];
                  const isSelected = selectedIds.includes(req.id);
                  const isEditing = editingId === req.id;
                  return (
                    <motion.tr key={req.id} variants={rowVariant} className={`hover:bg-[var(--bg-hover)] transition-colors group ${isSelected ? 'bg-red-500/5 border-l-2 border-l-red-500' : 'border-l-2 border-l-transparent'}`}>
                      <td className="px-6 py-5">
                        <input type="checkbox" className="w-4 h-4 rounded bg-[var(--bg-input)] border-[var(--border-color)] text-red-500 focus:ring-red-500" checked={isSelected} onChange={() => toggleSelect(req.id)} />
                      </td>
                      <td className="px-6 py-5">
                        <div className="flex items-center gap-4">
                          <div className="w-10 h-10 rounded-xl bg-[var(--bg-hover)] flex items-center justify-center flex-shrink-0 group-hover:bg-[var(--bg-hover)] transition-colors border border-[var(--border-color)]">
                            <FileText className="w-5 h-5 text-[var(--text-muted)] group-hover:text-red-400 transition-colors" />
                          </div>
                          <div>
                            {isEditing ? (
                              <div className="flex items-center gap-2">
                                <input value={editTitle} onChange={e => setEditTitle(e.target.value)} className="text-[14px] font-bold text-[var(--text-primary)] bg-[var(--bg-input)] border border-[var(--border-color)] rounded-lg px-2 py-1 outline-none focus:border-red-500 w-48" autoFocus />
                                <button onClick={() => handleEdit(req.id)} className="p-1 text-emerald-400 hover:bg-emerald-500/10 rounded"><Save className="w-4 h-4" /></button>
                                <button onClick={() => setEditingId(null)} className="p-1 text-[var(--text-muted)] hover:bg-[var(--bg-hover)] rounded"><X className="w-4 h-4" /></button>
                              </div>
                            ) : (
                              <>
                                <div className="text-[14px] font-bold text-[var(--text-secondary)] group-hover:text-[var(--text-primary)] transition-colors">{req.title}</div>
                                <div className="text-[11px] font-medium text-[var(--text-faint)] mt-1 uppercase tracking-wider">ID: {req.id}</div>
                              </>
                            )}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-5">
                        <span className={`inline-flex items-center gap-2 text-[11px] font-bold px-3 py-1.5 rounded-lg border border-transparent ${typeConf.bg} ${typeConf.text}`}>
                          <span className={`w-1.5 h-1.5 rounded-full ${typeConf.dot}`} />{typeConf.label}
                        </span>
                      </td>
                      <td className="px-6 py-5"><span className="text-[13px] text-[var(--text-muted)] font-mono">PRJ-{req.project_id}</span></td>
                      <td className="px-6 py-5">
                        <span className="text-[13px] text-[var(--text-muted)] flex items-center gap-2">
                          <Calendar className="w-4 h-4 text-[var(--text-faint)]" />
                          {new Date(req.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                        </span>
                      </td>
                      <td className="px-6 py-5">
                        <div className="flex items-center gap-2.5 opacity-0 group-hover:opacity-100 transition-opacity">
                          <button onClick={() => handleAnalyze(req)} className="flex items-center gap-2 px-4 py-2 text-[11px] font-bold text-[var(--text-primary)] primary-gradient rounded-xl transition-all active:scale-95 hover:opacity-90">
                            <Zap className="w-3.5 h-3.5" />Analyze
                          </button>
                          <button onClick={() => { setEditingId(req.id); setEditTitle(req.title); }} className="p-2 rounded-xl text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)] transition-all border border-transparent hover:border-[var(--border-color)]">
                            <Edit3 className="w-4 h-4" />
                          </button>
                          <button onClick={() => setDeleteConfirm(req.id)} className="p-2 rounded-xl text-[var(--text-muted)] hover:text-red-400 hover:bg-red-500/10 transition-all border border-transparent hover:border-red-500/20">
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </motion.tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
        {!isLoading && filtered.length > 0 && (
          <div className="flex items-center justify-between px-6 py-4 border-t border-[var(--border-color)] bg-[var(--bg-hover)]">
            <span className="text-[12px] text-[var(--text-muted)]">Showing <span className="font-bold text-[var(--text-secondary)]">{filtered.length}</span> of <span className="font-bold text-[var(--text-secondary)]">{requirements.length}</span></span>
          </div>
        )}
      </motion.div>
    </motion.div>
  );
}
