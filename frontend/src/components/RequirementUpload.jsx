import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload, FileText, CheckCircle2, Loader2, ArrowRight, ArrowLeft, Zap, File, Link } from 'lucide-react';
import toast from 'react-hot-toast';
import { apiService } from '../services/api';

const STEPS = [
  { id: 1, label: 'Select Type', description: 'Choose format' },
  { id: 2, label: 'Add Content', description: 'Enter details' },
  { id: 3, label: 'AI Analysis', description: 'Processing' },
];

const REQ_TYPES = [
  { id: 'user-story', icon: FileText, label: 'Manual User Story', description: 'Type your user story manually (Given/When/Then)', bg: 'rgba(237, 28, 36, 0.1)', border: 'rgba(237, 28, 36, 0.3)', iconColor: '#ED1C24' },
  { id: 'jira', icon: Link, label: 'Import from Jira', description: 'Import a user story directly from a Jira ticket URL', bg: 'rgba(139, 92, 246, 0.1)', border: 'rgba(139, 92, 246, 0.3)', iconColor: '#8B5CF6' },
  { id: 'docs', icon: File, label: 'PDF / Document', description: 'Upload a PDF or specification document', bg: 'rgba(245, 158, 11, 0.1)', border: 'rgba(245, 158, 11, 0.3)', iconColor: '#F59E0B' },
];

const fadeSlide = { initial: { opacity: 0, x: 24 }, animate: { opacity: 1, x: 0 }, exit: { opacity: 0, x: -24 }, transition: { type: 'spring', stiffness: 300, damping: 28 } };

export default function RequirementUpload({ onAnalysisComplete }) {
  const [step, setStep] = useState(1);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [selectedType, setSelectedType] = useState('user-story');
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [dragOver, setDragOver] = useState(false);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [analyzedId, setAnalyzedId] = useState(null);

  const handleFile = async (file) => {
    if (!file) return;
    if (!title) setTitle(file.name.replace(/\.[^.]+$/, ''));
    setUploadedFile(file);

    if (file.name.toLowerCase().endsWith('.pdf')) {
      // Use server-side PDF extraction
      const tid = toast.loading('Extracting text from PDF...');
      try {
        const res = await apiService.uploadPdf(file);
        setContent(res.extracted_text);
        toast.success(`PDF parsed: ${res.char_count} characters extracted`, { id: tid });
      } catch (e) {
        toast.error(e.message || 'Failed to parse PDF', { id: tid });
      }
    } else {
      // Text-based files
      const reader = new FileReader();
      reader.onload = (e) => { setContent(e.target.result); toast.success(`"${file.name}" loaded`); };
      reader.readAsText(file);
    }
  };

  const handleAnalysis = async () => {
    const tid = toast.loading('AI engine analyzing…');
    setIsAnalyzing(true); setStep(3);
    try {
      if (selectedType === 'jira') {
        if (!content.trim()) { toast.error('Enter a valid Jira URL', { id: tid }); setStep(2); setIsAnalyzing(false); return; }
        const data = await apiService.ingestJira(content.trim());
        toast.success('Jira issue imported & analyzed!', { id: tid });
        setAnalyzedId(data.requirement_id);
      } else {
        if (!title.trim() || !content.trim()) { toast.error('Provide both title and content', { id: tid }); setStep(2); setIsAnalyzing(false); return; }
        const req = await apiService.uploadRequirement({ title, content, type: selectedType, project_id: 1 });
        await apiService.analyzeRequirement(req.id);
        toast.success('Analysis complete!', { id: tid });
        setAnalyzedId(req.id);
      }
    } catch (e) { toast.error(e.message || 'Analysis failed', { id: tid }); }
    finally { setIsAnalyzing(false); }
  };

  const currentType = REQ_TYPES.find(t => t.id === selectedType);
  const inputCls = "w-full px-4 py-3 text-sm bg-[var(--bg-input)] border border-[var(--border-color)] rounded-xl outline-none focus:ring-2 focus:ring-red-500/20 focus:border-red-500 transition-all font-semibold text-[var(--text-primary)] placeholder:text-[var(--text-faint)]";

  return (
    <div className="max-w-4xl mx-auto">
      {/* Progress Steps */}
      <div className="card p-6 mb-6">
        <div className="flex items-center gap-0">
          {STEPS.map((s, i) => {
            const isDone = step > s.id, isActive = step === s.id;
            return (
              <React.Fragment key={s.id}>
                <div className="flex items-center gap-3 flex-shrink-0">
                  <div className={`w-9 h-9 rounded-xl flex items-center justify-center text-sm font-bold transition-all duration-500 ${isDone ? 'bg-emerald-500 text-white shadow-lg shadow-emerald-500/25' : isActive ? 'bg-red-600 text-white shadow-lg shadow-red-500/25' : 'bg-[var(--bg-hover)] text-[var(--text-muted)]'}`}>
                    {isDone ? <CheckCircle2 className="w-5 h-5" /> : s.id}
                  </div>
                  <div className="hidden sm:block">
                    <div className={`text-sm font-bold leading-tight ${isActive ? 'text-[var(--text-primary)]' : isDone ? 'text-emerald-400' : 'text-[var(--text-muted)]'}`}>{s.label}</div>
                    <div className="text-[11px] text-[var(--text-faint)]">{s.description}</div>
                  </div>
                </div>
                {i < STEPS.length - 1 && <div className="flex-1 mx-4"><div className={`h-0.5 rounded-full transition-all duration-700 ${isDone ? 'bg-emerald-500/50' : 'bg-white/[0.06]'}`} /></div>}
              </React.Fragment>
            );
          })}
        </div>
      </div>

      <AnimatePresence mode="wait">
        {step === 1 && (
          <motion.div key="step1" {...fadeSlide} className="space-y-4">
            <div className="card p-8">
              <div className="mb-8"><h2 className="text-xl font-bold text-[var(--text-primary)] tracking-tight">Select Requirement Type</h2><p className="text-sm text-[var(--text-secondary)] mt-1">Choose the format that matches your source.</p></div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
                {REQ_TYPES.map((type) => {
                  const Icon = type.icon; const isSel = selectedType === type.id;
                  return (
                    <button key={type.id} onClick={() => setSelectedType(type.id)}
                      className={`relative p-6 rounded-2xl border-2 text-left transition-all group active:scale-[0.98] ${isSel ? 'bg-[var(--bg-hover)]' : 'border-[var(--border-color)] bg-[var(--bg-hover)] hover:bg-[var(--bg-hover)]'}`}
                      style={isSel ? { borderColor: type.border } : { borderColor: 'transparent' }}>
                      {isSel && <div className="absolute top-3 right-3 w-5 h-5 rounded-full bg-red-500 flex items-center justify-center"><CheckCircle2 className="w-3 h-3 text-white" /></div>}
                      <div className="w-12 h-12 rounded-xl mb-5 flex items-center justify-center" style={{ background: isSel ? type.bg : 'rgba(255,255,255,0.04)' }}>
                        <Icon className="w-6 h-6" style={{ color: isSel ? type.iconColor : '#64748B' }} />
                      </div>
                      <h3 className="text-[15px] font-bold text-[var(--text-primary)] tracking-tight mb-1.5">{type.label}</h3>
                      <p className="text-xs text-[var(--text-muted)] leading-relaxed">{type.description}</p>
                    </button>
                  );
                })}
              </div>
              <div className="flex justify-end mt-8">
                <button onClick={() => setStep(2)} className="flex items-center gap-2 px-6 py-3 primary-gradient text-white text-sm font-bold rounded-xl transition-all active:scale-[0.98] hover:opacity-90">Continue <ArrowRight className="w-4 h-4" /></button>
              </div>
            </div>
          </motion.div>
        )}

        {step === 2 && (
          <motion.div key="step2" {...fadeSlide} className="space-y-4">
            <div className="card p-8">
              <div className="flex items-center gap-4 mb-8">
                <div className="w-12 h-12 rounded-xl flex items-center justify-center" style={{ background: currentType?.bg }}>
                  {currentType && <currentType.icon className="w-6 h-6" style={{ color: currentType.iconColor }} />}
                </div>
                <div><h2 className="text-xl font-bold text-[var(--text-primary)]">Add Requirement Details</h2><p className="text-sm text-[var(--text-secondary)]">Format: <span className="font-semibold text-[var(--text-primary)]">{currentType?.label}</span></p></div>
              </div>
              <div className="space-y-6">
                <div><label className="block text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider mb-2.5">Title *</label><input type="text" value={title} onChange={e => setTitle(e.target.value)} placeholder="e.g. User Authentication & Session Management" className={inputCls} /></div>
                {selectedType === 'jira' && <div><label className="block text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider mb-2.5">Jira URL *</label><input type="url" value={content} onChange={e => setContent(e.target.value)} placeholder="https://yourcompany.atlassian.net/browse/PROJ-123" className={inputCls} /></div>}
                {selectedType === 'docs' && (
                  <div><label className="block text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider mb-2.5">Upload Document *</label>
                    <div onDragOver={e => { e.preventDefault(); setDragOver(true); }} onDragLeave={() => setDragOver(false)} onDrop={e => { e.preventDefault(); setDragOver(false); handleFile(e.dataTransfer.files[0]); }}
                      className={`relative border-2 border-dashed rounded-xl transition-all ${dragOver ? 'border-red-500 bg-red-500/5' : 'border-[var(--border-color)] hover:border-[var(--border-color)]'} ${uploadedFile ? 'border-emerald-500/50 bg-emerald-500/5' : ''}`}>
                      <input type="file" accept=".pdf,.md,.txt,.doc,.docx" onChange={e => handleFile(e.target.files[0])} className="absolute inset-0 w-full h-full opacity-0 cursor-pointer" />
                      <div className="p-8 text-center flex flex-col items-center gap-3">
                        {uploadedFile ? (<><div className="w-12 h-12 bg-emerald-500/10 border border-emerald-500/20 rounded-xl flex items-center justify-center"><File className="w-6 h-6 text-emerald-400" /></div><p className="text-sm font-bold text-emerald-400">{uploadedFile.name}</p></>)
                        : (<><div className="w-12 h-12 bg-[var(--bg-hover)] rounded-xl flex items-center justify-center border border-[var(--border-color)]"><Upload className="w-6 h-6 text-[var(--text-muted)]" /></div><p className="text-sm font-bold text-[var(--text-secondary)]">Drop file here or click to browse</p></>)}
                      </div>
                    </div>
                  </div>
                )}
                {selectedType === 'user-story' && (
                  <div><label className="block text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider mb-2.5">Story Content *</label>
                    <div className="relative">
                      <textarea rows={12} value={content} onChange={e => setContent(e.target.value)} placeholder={`As a user, I want to...\n\nGiven I am logged in\nWhen I navigate to...\nThen I should see...`}
                        className="w-full px-4 py-4 text-[13px] bg-[var(--bg-input)] border border-[var(--border-color)] rounded-xl outline-none focus:ring-2 focus:ring-red-500/20 focus:border-red-500 transition-all font-mono leading-relaxed text-[var(--text-primary)] placeholder:text-[var(--text-faint)] resize-none custom-scrollbar" />
                      <div className="absolute bottom-3 right-4 text-[10px] text-[var(--text-faint)] font-bold tracking-wider">{content.length} CHARS</div>
                    </div>
                  </div>
                )}
              </div>
              <div className="flex items-center justify-between mt-8 pt-6 border-t border-[var(--border-color)]">
                <button onClick={() => setStep(1)} className="flex items-center gap-2 px-5 py-2.5 text-sm font-bold text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)] rounded-xl transition-all"><ArrowLeft className="w-4 h-4" /> Back</button>
                <button onClick={handleAnalysis} disabled={!title.trim() || !content.trim()} className="flex items-center gap-2 px-7 py-3 primary-gradient disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-bold rounded-xl transition-all active:scale-[0.98] hover:opacity-90"><Zap className="w-4 h-4" />Start AI Analysis</button>
              </div>
            </div>
          </motion.div>
        )}

        {step === 3 && (
          <motion.div key="step3" {...fadeSlide}>
            <div className="card p-12 text-center">
              {isAnalyzing ? (
                <div className="flex flex-col items-center gap-6">
                  <div className="relative w-24 h-24">
                    <div className="absolute inset-0 rounded-full bg-red-500 animate-ping opacity-20" />
                    <div className="relative w-full h-full rounded-full primary-gradient flex items-center justify-center shadow-xl shadow-red-500/30"><Loader2 className="w-10 h-10 text-white animate-spin" /></div>
                  </div>
                  <div><h3 className="text-xl font-bold text-[var(--text-primary)]">AI Engine Processing</h3><p className="text-sm text-[var(--text-secondary)] mt-2 max-w-sm mx-auto">Generating Gherkin scenarios & Playwright scripts…</p></div>
                  <div className="w-full max-w-xs bg-white/[0.06] rounded-full h-1.5 overflow-hidden"><motion.div className="h-full bg-gradient-to-r from-red-500 to-red-400 rounded-full" initial={{ width: '0%' }} animate={{ width: '85%' }} transition={{ duration: 3.5, ease: 'easeInOut' }} /></div>
                </div>
              ) : (
                <div className="flex flex-col items-center gap-6">
                  <div className="w-24 h-24 rounded-full bg-gradient-to-br from-emerald-400 to-emerald-600 flex items-center justify-center shadow-xl shadow-emerald-500/30"><CheckCircle2 className="w-12 h-12 text-white" /></div>
                  <div><h3 className="text-2xl font-black text-[var(--text-primary)] tracking-tight">Analysis Complete!</h3><p className="text-sm text-[var(--text-secondary)] mt-2 max-w-sm mx-auto">Gherkin scenarios and test scripts are ready.</p></div>
                  <div className="flex items-center gap-4 mt-2">
                    <button onClick={() => { setStep(1); setTitle(''); setContent(''); setUploadedFile(null); }} className="px-6 py-3 text-sm font-bold text-[var(--text-secondary)] bg-[var(--bg-hover)] border border-[var(--border-color)] hover:bg-white/[0.08] rounded-xl transition-all">Analyze Another</button>
                    <button onClick={() => onAnalysisComplete(analyzedId)} className="flex items-center gap-2 px-6 py-3 primary-gradient text-white text-sm font-bold rounded-xl transition-all active:scale-[0.98] hover:opacity-90">Open in Editor <ArrowRight className="w-4 h-4" /></button>
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
