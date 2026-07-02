import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Play, Copy, RotateCcw, ChevronRight, CheckCircle, Zap, Loader2, AlertCircle, Code2, FileCode, Terminal, Download, GitBranch, X, ExternalLink, MessageSquare, ThumbsUp } from 'lucide-react';
import toast from 'react-hot-toast';
import { apiService } from '../services/api';
import { useSearchParams } from 'react-router-dom';

const VIEWS = [
  { id: 'gherkin', label: 'Gherkin Feature', icon: FileCode },
  { id: 'code', label: 'TypeScript Script', icon: Code2 },
];

export default function ScenarioEditor() {
  const [searchParams] = useSearchParams();
  const requirementId = searchParams.get('req');
  const [scenarios, setScenarios] = useState([]);
  const [selected, setSelected] = useState(null);
  const [script, setScript] = useState(null);
  const [view, setView] = useState('gherkin');
  const [isRunning, setIsRunning] = useState(false);
  const [result, setResult] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [showResult, setShowResult] = useState(false);
  const [isPushing, setIsPushing] = useState(false);
  const [isEditingGherkin, setIsEditingGherkin] = useState(false);
  const [editedGherkin, setEditedGherkin] = useState('');
  const [isGeneratingCode, setIsGeneratingCode] = useState(false);
  const [showReviewPanel, setShowReviewPanel] = useState(false);
  const [reviewPrompt, setReviewPrompt] = useState('');
  const [isReviewing, setIsReviewing] = useState(false);
  const [isValidated, setIsValidated] = useState(false);

  useEffect(() => {
    (async () => {
      setIsLoading(true);
      try {
        const data = requirementId ? await apiService.getScenarios(requirementId) : await apiService.getScenarios();
        setScenarios(data || []);
        if (data?.length) selectScenario(data[0]);
      } catch { /* empty */ }
      finally { setIsLoading(false); }
    })();
  }, [requirementId]);

  const selectScenario = async (scenario) => {
    setSelected(scenario); setResult(null); setShowResult(false);
    setEditedGherkin(scenario.gherkin_content || '');
    setIsEditingGherkin(false);
    try { const s = await apiService.getScript(scenario.id); setScript(s); } catch { setScript(null); }
  };

  const runTest = async () => {
    if (!script) return;
    setIsRunning(true); setShowResult(false);
    const tid = toast.loading('Running tests in Docker container…');
    try {
      const res = await apiService.executeTest(script.id);
      setResult(res); setShowResult(true);
      const status = (res.status || '').toLowerCase();
      if (status === 'passed') toast.success('Tests Passed!', { id: tid }); else toast.error('Tests Failed', { id: tid });
    } catch { toast.error('Execution failed', { id: tid }); }
    finally { setIsRunning(false); }
  };

  const pushToGithub = async () => {
    if (!selected) return;
    setIsPushing(true);
    const tid = toast.loading('Pushing script to GitHub repository…');
    try {
      const res = await apiService.pushToGithub(selected.id);
      toast.success(res.message || 'Successfully pushed to GitHub!', { id: tid, duration: 6000 });
    } catch (e) { toast.error(e.message || 'GitHub push failed', { id: tid }); }
    finally { setIsPushing(false); }
  };

  const saveGherkin = async () => {
    if (!selected) return;
    const tid = toast.loading('Saving scenario...');
    try {
      const updated = await apiService.updateScenario(selected.id, { gherkin_content: editedGherkin });
      setSelected(updated);
      setIsEditingGherkin(false);
      toast.success('Scenario saved!', { id: tid });
    } catch (e) { toast.error('Failed to save', { id: tid }); }
  };

  const generateCode = async () => {
    if (!selected) return;
    setIsGeneratingCode(true);
    const tid = toast.loading('AI is generating Playwright code...');
    try {
      await apiService.generateScenarioCode(selected.id);
      // reload script
      const s = await apiService.getScript(selected.id);
      setScript(s);
      setView('code');
      toast.success('TypeScript code generated!', { id: tid });
    } catch (e) { toast.error(e.message || 'Generation failed', { id: tid }); }
    finally { setIsGeneratingCode(false); }
  };

  const handleValidate = () => {
    setIsValidated(true);
    toast.success(view === 'gherkin' ? 'Scénario validé ✅' : 'Code validé ✅');
  };

  const handleReview = async () => {
    if (!reviewPrompt.trim()) return;
    setIsReviewing(true);
    const tid = toast.loading('AI is reviewing and improving...');
    try {
      const content = view === 'gherkin' ? (selected?.gherkin_content || '') : (script?.code || '');
      const res = view === 'gherkin'
        ? await apiService.reviewScenario(content, reviewPrompt)
        : await apiService.reviewCode(content, reviewPrompt);
      if (res.improved_content) {
        if (view === 'gherkin') {
          setEditedGherkin(res.improved_content);
          setIsEditingGherkin(true);
        } else {
          setScript({ ...script, code: res.improved_content });
        }
        toast.success('Review complete! Check the improved version.', { id: tid });
      }
    } catch (e) { toast.error(e.message || 'Review failed', { id: tid }); }
    finally { setIsReviewing(false); setReviewPrompt(''); setShowReviewPanel(false); }
  };

  const getContent = () => view === 'gherkin' ? selected?.gherkin_content || '' : script?.code || '';
  const lines = getContent().split('\n');

  // Simple Gherkin syntax highlighting
  const highlightGherkin = (line) => {
    if (/^\s*(Feature|Background|Scenario|Scenario Outline|Examples):/.test(line)) return 'text-red-400 font-bold';
    if (/^\s*(Given|When|Then|And|But)\s/.test(line)) return 'text-emerald-400';
    if (/^\s*@/.test(line)) return 'text-amber-400';
    if (/^\s*\|/.test(line)) return 'text-blue-400';
    if (/^\s*#/.test(line)) return 'text-[var(--text-faint)] italic';
    return 'text-[var(--text-secondary)]';
  };

  if (isLoading) return (
    <div className="flex items-center justify-center h-64 gap-3">
      <Loader2 className="w-6 h-6 animate-spin text-red-500" />
      <span className="text-sm text-[var(--text-muted)] font-bold tracking-wider uppercase">Loading editor…</span>
    </div>
  );

  if (scenarios.length === 0) return (
    <div className="card p-16 text-center">
      <div className="w-20 h-20 bg-red-500/10 border border-red-500/20 rounded-2xl flex items-center justify-center mx-auto mb-6"><Zap className="w-10 h-10 text-red-500" /></div>
      <h3 className="text-xl font-bold text-[var(--text-primary)] mb-3 tracking-tight">No Scenarios Generated Yet</h3>
      <p className="text-sm text-[var(--text-secondary)] max-w-sm mx-auto leading-relaxed">Analyze a requirement from the Requirements tab to generate Gherkin scenarios and TypeScript test scripts.</p>
    </div>
  );

  return (
    <div className="grid grid-cols-1 xl:grid-cols-4 gap-6 h-full">
      {/* Left Panel */}
      <div className="xl:col-span-1 space-y-4">
        <div className="card overflow-hidden flex flex-col max-h-[420px]">
          <div className="px-5 py-4 border-b border-[var(--border-color)] flex items-center justify-between bg-[var(--bg-card)]">
            <span className="text-[14px] font-bold text-[var(--text-primary)]">Scenarios</span>
            <span className="text-[11px] text-red-400 bg-red-500/10 border border-red-500/20 px-2.5 py-0.5 rounded-full font-black">{scenarios.length}</span>
          </div>
          <div className="divide-y divide-white/[0.04] overflow-y-auto custom-scrollbar flex-1">
            {scenarios.map((s) => {
              const isActive = selected?.id === s.id;
              return (
                <button key={s.id} onClick={() => selectScenario(s)} className={`w-full text-left px-5 py-4 text-sm transition-all flex items-center gap-3 group ${isActive ? 'bg-red-500/10 border-l-2 border-red-500' : 'hover:bg-[var(--bg-hover)] border-l-2 border-transparent'}`}>
                  <div className="flex-1 min-w-0">
                    <div className={`text-[13px] font-bold truncate ${isActive ? 'text-red-400' : 'text-[var(--text-secondary)] group-hover:text-[var(--text-primary)]'}`}>{s.title}</div>
                    <div className="text-[11px] text-[var(--text-faint)] mt-0.5 uppercase tracking-wider">SCN-{s.id}</div>
                  </div>
                  {isActive && <ChevronRight className="w-4 h-4 text-red-400 flex-shrink-0" />}
                </button>
              );
            })}
          </div>
        </div>

        <div className="card p-5 space-y-3 bg-[var(--bg-card)]">
          <div className="text-[11px] font-black text-[var(--text-muted)] uppercase tracking-widest mb-1">Execution</div>
          <button onClick={runTest} disabled={isRunning || !script} className="w-full flex items-center justify-center gap-2.5 py-3 rounded-xl primary-gradient disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-bold transition-all active:scale-[0.98] hover:opacity-90">
            {isRunning ? <><Loader2 className="w-4 h-4 animate-spin" /> Running…</> : <><Play className="w-4 h-4 fill-white" /> Run in Docker</>}
          </button>
          <div className="pt-1">
            <button onClick={generateCode} disabled={isGeneratingCode || !selected} className={`w-full flex items-center justify-center gap-2.5 py-2.5 rounded-xl border disabled:opacity-50 disabled:cursor-not-allowed text-[13px] font-bold transition-all active:scale-[0.98] ${script ? 'border-amber-500/30 bg-amber-500/10 text-amber-400 hover:bg-amber-500/20' : 'border-emerald-500/30 bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20'}`}>
              {isGeneratingCode ? <><Loader2 className="w-4 h-4 animate-spin" /> Generating Code…</> : <><Code2 className="w-4 h-4" /> {script ? 'Regenerate Code' : 'Generate Playwright Code'}</>}
            </button>
          </div>
        </div>

        <div className="card p-5 bg-[var(--bg-card)]">
          <div className="text-[11px] font-black text-[var(--text-muted)] uppercase tracking-widest mb-3">DevOps / Export</div>
          <div className="space-y-2">
            <button onClick={pushToGithub} disabled={isPushing || !script} className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-[13px] font-bold bg-[var(--bg-hover)] hover:bg-[var(--bg-hover-strong)] text-[var(--text-primary)] border border-[var(--border-color)] disabled:opacity-50 transition-all active:scale-[0.98]">
              {isPushing ? <><Loader2 className="w-4 h-4 animate-spin" /> Pushing…</> : <><GitBranch className="w-4 h-4" /> Inject to GitHub</>}
            </button>
            <button onClick={() => apiService.exportGitlabCI?.()} className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-[13px] font-bold text-[var(--text-secondary)] hover:bg-[var(--bg-hover)] border border-[var(--border-color)] transition-all text-left"><Download className="w-4 h-4" />.github/workflows</button>
            <button onClick={() => apiService.exportReport?.(1)} className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-[13px] font-bold text-[var(--text-secondary)] hover:bg-[var(--bg-hover)] border border-[var(--border-color)] transition-all text-left"><Download className="w-4 h-4" />PDF Report</button>
          </div>
        </div>
      </div>

      {/* Right Panel: Editor */}
      <div className="xl:col-span-3 space-y-5 flex flex-col">
        <div className="card overflow-hidden flex flex-col">
          <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--border-color)] bg-[var(--bg-card)]">
            <div className="flex items-center gap-1 bg-[var(--bg-hover)] border border-[var(--border-color)] rounded-xl p-1">
              {VIEWS.map((v) => (<button key={v.id} onClick={() => setView(v.id)} className={`flex items-center gap-2 px-4 py-2 rounded-lg text-[12px] font-bold transition-all ${view === v.id ? 'bg-red-600 text-white shadow-md' : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)]'}`}><v.icon className="w-4 h-4" />{v.label}</button>))}
            </div>
            <button onClick={() => { navigator.clipboard.writeText(getContent()); toast.success('Copied!'); }} className="flex items-center gap-1.5 px-3 py-2 text-[12px] font-bold text-[var(--text-secondary)] bg-[var(--bg-hover)] border border-[var(--border-color)] hover:bg-[var(--bg-hover)] rounded-lg transition-all"><Copy className="w-3.5 h-3.5" /> Copy</button>
          </div>
          <div className="relative bg-[var(--bg-input)] flex-1 min-h-[460px] flex flex-col">
            <div className="flex items-center gap-3 px-5 py-2 border-b border-[var(--border-color)] bg-[var(--bg-input)]">
              <div className="flex items-center gap-1.5"><div className="w-2.5 h-2.5 rounded-full bg-red-400/60" /><div className="w-2.5 h-2.5 rounded-full bg-amber-400/60" /><div className="w-2.5 h-2.5 rounded-full bg-emerald-400/60" /></div>
              <span className="text-[11px] text-[var(--text-muted)] font-mono tracking-wide">{view === 'gherkin' ? `features/scenario_${selected?.id || 0}.feature` : `tests/script_${script?.id || 0}.spec.ts`}</span>
              {script?.language && <span className="ml-auto text-[10px] font-black px-2 py-0.5 rounded bg-[var(--bg-hover)] border border-[var(--border-color)] text-[var(--text-secondary)] uppercase tracking-wider">{script.language}</span>}
            </div>
            <div className="flex overflow-auto flex-1 custom-scrollbar relative">
              {view === 'gherkin' && isEditingGherkin ? (
                <div className="flex-1 flex flex-col p-4 bg-[var(--bg-input)]">
                  <textarea 
                    className="flex-1 w-full bg-[var(--bg-card)] text-[var(--text-primary)] font-mono text-[13px] leading-6 p-4 rounded-xl border border-[var(--border-color)] outline-none focus:border-red-500 resize-none custom-scrollbar"
                    value={editedGherkin}
                    onChange={(e) => setEditedGherkin(e.target.value)}
                  />
                  <div className="flex justify-end gap-3 mt-4">
                    <button onClick={() => setIsEditingGherkin(false)} className="px-5 py-2.5 rounded-xl font-bold text-[var(--text-secondary)] hover:bg-[var(--bg-hover)] transition-colors text-[13px]">Cancel</button>
                    <button onClick={saveGherkin} className="px-5 py-2.5 rounded-xl font-bold text-[var(--text-primary)] bg-emerald-600 hover:bg-emerald-500 transition-colors text-[13px] flex items-center gap-2">Save Gherkin</button>
                  </div>
                </div>
              ) : (
                <>
                  <div className="flex-shrink-0 px-4 py-5 text-right select-none bg-[var(--bg-input)] border-r border-[var(--border-color)] min-w-[48px]">
                    {Array.from({ length: Math.max(lines.length, 20) }).map((_, i) => (<div key={i} className="text-[12px] font-mono text-[var(--text-faint)] leading-7">{i + 1}</div>))}
                  </div>
                  <pre className="flex-1 px-6 py-5 text-[13.5px] font-mono leading-7 overflow-x-auto whitespace-pre">
                    {getContent() ? (view === 'gherkin'
                      ? lines.map((line, i) => <div key={i} className={highlightGherkin(line)}>{line}</div>)
                      : <span className="text-sky-300">{getContent()}</span>
                    ) : <span className="text-[var(--text-faint)] italic">{view === 'gherkin' ? '# Select a scenario to view its Gherkin feature file' : '// TypeScript Playwright test script will appear here'}</span>}
                  </pre>
                  {view === 'gherkin' && selected && !isEditingGherkin && (
                    <button onClick={() => { setEditedGherkin(selected.gherkin_content || ''); setIsEditingGherkin(true); }} className="absolute top-4 right-6 bg-[var(--bg-hover)] hover:bg-[var(--bg-hover-strong)] border border-[var(--border-color)] text-[var(--text-secondary)] px-4 py-2 rounded-lg text-xs font-bold transition-colors">Edit Scenario</button>
                  )}
                </>
              )}
            </div>
          </div>

          {/* ── Valider / Review Buttons ── */}
          <div className="flex items-center justify-between px-6 py-3 border-t border-[var(--border-color)] bg-[var(--bg-card)]">
            <div className="flex items-center gap-2">
              {isValidated && (
                <span className="flex items-center gap-1.5 text-xs font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-3 py-1.5 rounded-lg">
                  <CheckCircle className="w-3.5 h-3.5" /> Validé
                </span>
              )}
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={() => setShowReviewPanel(!showReviewPanel)}
                className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-[13px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20 hover:bg-amber-500/20 transition-all active:scale-[0.98]"
              >
                <MessageSquare className="w-4 h-4" /> Review
              </button>
              <button
                onClick={handleValidate}
                disabled={isValidated}
                className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-[13px] font-bold bg-emerald-600 text-white hover:bg-emerald-500 transition-all active:scale-[0.98] disabled:opacity-50"
              >
                <ThumbsUp className="w-4 h-4" /> Valider
              </button>
            </div>
          </div>

          {/* ── Review Panel ── */}
          <AnimatePresence>
            {showReviewPanel && (
              <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="overflow-hidden border-t border-[var(--border-color)]">
                <div className="p-5 bg-[var(--bg-card)] space-y-3">
                  <div className="text-[11px] font-black text-amber-400 uppercase tracking-widest">🔄 AI Review — Describe your improvement</div>
                  <textarea
                    rows={3}
                    value={reviewPrompt}
                    onChange={(e) => setReviewPrompt(e.target.value)}
                    placeholder={view === 'gherkin' ? 'Ex: Ajouter des scénarios négatifs, couvrir les cas edge...' : 'Ex: Ajouter des assertions, utiliser des data-testid...'}
                    className="w-full bg-[var(--bg-input)] border border-[var(--border-color)] rounded-xl px-4 py-3 text-[13px] text-[var(--text-primary)] placeholder:text-[var(--text-faint)] outline-none focus:border-amber-500 resize-none"
                  />
                  <div className="flex justify-end gap-3">
                    <button onClick={() => setShowReviewPanel(false)} className="px-4 py-2 text-[13px] font-bold text-[var(--text-secondary)] hover:bg-[var(--bg-hover)] rounded-xl transition-colors">Annuler</button>
                    <button onClick={handleReview} disabled={isReviewing || !reviewPrompt.trim()} className="flex items-center gap-2 px-5 py-2 primary-gradient text-white text-[13px] font-bold rounded-xl transition-all hover:opacity-90 disabled:opacity-50">
                      {isReviewing ? <><Loader2 className="w-4 h-4 animate-spin" /> Reviewing...</> : <><Zap className="w-4 h-4" /> Send to AI</>}
                    </button>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        <AnimatePresence>
          {showResult && result && (
            <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -12 }} className="card overflow-hidden">
              <div className={`flex items-center justify-between px-6 py-5 border-b ${(result.status || '').toLowerCase() === 'passed' ? 'bg-emerald-500/10 border-emerald-500/20' : 'bg-red-500/10 border-red-500/20'}`}>
                <div className={`flex items-center gap-4 ${(result.status || '').toLowerCase() === 'passed' ? 'text-emerald-400' : 'text-red-400'}`}>
                  <div className={`p-2 rounded-xl ${(result.status || '').toLowerCase() === 'passed' ? 'bg-emerald-500/20 border border-emerald-500/30' : 'bg-red-500/20 border border-red-500/30'}`}>
                    {(result.status || '').toLowerCase() === 'passed' ? <CheckCircle className="w-5 h-5" /> : <AlertCircle className="w-5 h-5" />}
                  </div>
                  <div><div className="text-[15px] font-black tracking-wide uppercase">Test Suite {result.status}</div><div className="text-[12px] font-semibold mt-0.5 opacity-80">Duration: {result.duration}s · Coverage: {result.kpis?.coverage ?? '—'}%</div></div>
                </div>
                <div className="flex items-center gap-2">
                  <button onClick={runTest} className="flex items-center gap-2 px-4 py-2 text-[12px] font-bold text-[var(--text-primary)] bg-[var(--bg-hover)] border border-[var(--border-color)] rounded-xl hover:bg-[var(--bg-hover-strong)] transition-all"><RotateCcw className="w-4 h-4" /> Retry</button>
                  <button onClick={() => setShowResult(false)} className="p-2 rounded-xl text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)] transition-all"><X className="w-5 h-5" /></button>
                </div>
              </div>
              <div className="p-6">
                <div className="flex items-center gap-2 mb-3"><Terminal className="w-4 h-4 text-[var(--text-muted)]" /><span className="text-[11px] text-[var(--text-muted)] font-mono font-bold uppercase tracking-widest">stdout</span></div>
                <div className="bg-[var(--bg-input)] rounded-xl p-5 overflow-x-auto custom-scrollbar max-h-56">
                  <pre className={`text-[13px] font-mono leading-relaxed whitespace-pre-wrap ${(result.status || '').toLowerCase() === 'passed' ? 'text-emerald-400' : 'text-red-300'}`}>{result.output || 'No output captured.'}</pre>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
