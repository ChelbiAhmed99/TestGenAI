import React, { useState, useEffect } from 'react';
import { Routes, Route, NavLink, useNavigate, useLocation, Navigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  LayoutDashboard, FileText, Code2, GitBranch, History,
  Settings as SettingsIcon, Menu, X, Plus, ChevronRight,
  Zap, Shield, TrendingUp, CheckCircle2, LogOut, Book,
  Sun, Moon
} from 'lucide-react';
import { useTheme } from './hooks/ThemeContext';
import Dashboard from './components/Dashboard';
import RequirementUpload from './components/RequirementUpload';
import RequirementList from './components/RequirementList';
import TraceabilityMatrix from './components/TraceabilityMatrix';
import ExecutionHistory from './components/ExecutionHistory';
import ScenarioEditor from './components/ScenarioEditor';
import Settings from './components/Settings';
import Login from './components/Login';
import Documentation from './components/Documentation';
import UserManagement from './components/UserManagement';

const NAV_ITEMS = [
  {
    group: 'Core',
    roles: ['admin', 'qa', 'manager'],
    items: [
      { id: 'dashboard', path: '/', icon: LayoutDashboard, label: 'Dashboard', badge: null },
      { id: 'requirements', path: '/requirements', icon: FileText, label: 'Requirements', badge: null },
      { id: 'editor', path: '/editor', icon: Code2, label: 'AI Scenario Editor', badge: 'AI' },
    ]
  },
  {
    group: 'Quality & Admin',
    roles: ['admin', 'qa', 'manager'],
    items: [
      { id: 'matrix', path: '/matrix', icon: GitBranch, label: 'Traceability Matrix', badge: null },
      { id: 'execution', path: '/execution', icon: History, label: 'Execution History', badge: null },
    ]
  },
  {
    group: 'Security',
    roles: ['admin'],
    items: [
      { id: 'users', path: '/users', icon: Shield, label: 'User Management', badge: null },
    ]
  },
  {
    group: 'Help',
    roles: ['admin', 'qa', 'manager', 'guest'],
    items: [
      { id: 'documentation', path: '/documentation', icon: Book, label: 'Documentation', badge: null },
    ]
  }
];

const PAGE_TITLES = {
  '/': { title: 'Command Center', sub: 'Platform overview & KPIs' },
  '/requirements': { title: 'Requirements', sub: 'Manage specifications & user stories' },
  '/editor': { title: 'AI Scenario Editor', sub: 'Gherkin & automated script generation' },
  '/matrix': { title: 'Traceability Matrix', sub: 'End-to-end requirement mapping' },
  '/execution': { title: 'Execution History', sub: 'Test run audit trail & logs' },
  '/settings': { title: 'Platform Settings', sub: 'Configuration & integrations' },
  '/upload': { title: 'New Requirement', sub: 'AI-powered analysis pipeline' },
  '/documentation': { title: 'Documentation', sub: 'How to use the platform' },
  '/users': { title: 'User Management', sub: 'Platform access and roles' },
};

function App() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(!!localStorage.getItem('token'));
  const [currentUser, setCurrentUser] = useState({ username: 'User', role: 'QA' });
  const location = useLocation();
  const navigate = useNavigate();
  const { isDark, toggleTheme } = useTheme();

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      try {
        const base64Url = token.split('.')[1];
        const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
        const jsonPayload = decodeURIComponent(window.atob(base64).split('').map(function (c) {
          return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
        }).join(''));
        const decoded = JSON.parse(jsonPayload);
        setCurrentUser({
          username: decoded.sub || 'User',
          role: decoded.role || 'QA'
        });
      } catch (e) {
        console.error("Token decoding failed", e);
      }
    }
  }, [isAuthenticated]);

  // Update document title based on route
  useEffect(() => {
    const page = PAGE_TITLES[location.pathname];
    document.title = page
      ? `${page.title} — Devoteam · TestGenAI`
      : 'Devoteam · TestGenAI Platform';
  }, [location.pathname]);

  const handleLogout = () => {
    localStorage.removeItem('token');
    setIsAuthenticated(false);
    navigate('/');
  };

  const closeSidebar = () => setIsSidebarOpen(false);

  const currentPage = PAGE_TITLES[location.pathname] || PAGE_TITLES['/'];

  if (!isAuthenticated) {
    return <Login onLogin={(token) => setIsAuthenticated(true)} />;
  }

  return (
    <div className="min-h-screen w-full flex theme-transition" style={{ background: 'var(--bg-primary)', color: 'var(--text-primary)' }}>

      {/* ── Mobile overlay ── */}
      <AnimatePresence>
        {isSidebarOpen && (
          <motion.div
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            onClick={closeSidebar}
            className="fixed inset-0 z-40 lg:hidden"
            style={{ background: 'var(--bg-modal-overlay)', backdropFilter: 'blur(4px)' }}
          />
        )}
      </AnimatePresence>

      {/* ══════════════════════════════════════════
          SIDEBAR
      ══════════════════════════════════════════ */}
      <aside className={`
        fixed lg:sticky top-0 left-0 h-screen w-64 xl:w-72
        backdrop-blur-xl flex flex-col z-50
        transition-transform duration-300 ease-in-out lg:translate-x-0
        ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full'}
      `} style={{
        background: 'var(--bg-sidebar)',
        borderRight: '1px solid var(--border-color)',
        boxShadow: isSidebarOpen ? 'var(--shadow-modal)' : 'none'
      }}>
        {/* Logo */}
        <div className="flex items-center justify-between px-6 py-5" style={{ borderBottom: '1px solid var(--border-color)' }}>
          <NavLink
            to="/"
            onClick={closeSidebar}
            className="flex items-center gap-3 group"
          >
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-red-600 to-red-500 flex items-center justify-center shadow-lg shadow-red-500/20 group-hover:shadow-red-500/30 transition-all">
              <span className="text-white font-black text-lg">D</span>
            </div>
            <div className="text-left">
              <div className="text-[17px] font-black tracking-tight leading-none" style={{ color: 'var(--text-primary)' }}>Devoteam</div>
              <div className="text-[10px] font-bold text-red-400 tracking-widest uppercase leading-none mt-1">TestGenAI</div>
            </div>
          </NavLink>
          <button
            onClick={closeSidebar}
            className="lg:hidden p-1.5 rounded-lg transition-all"
            style={{ color: 'var(--text-muted)' }}
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-6 custom-scrollbar">
          {NAV_ITEMS.filter(g => g.roles.includes((currentUser.role || 'guest').toLowerCase())).map((group) => (
            <div key={group.group}>
              <div className="px-3 mb-2 text-[10px] font-bold uppercase tracking-widest" style={{ color: 'var(--text-muted)' }}>
                {group.group}
              </div>
              <div className="space-y-0.5">
                {group.items.map((item) => (
                  <NavLink
                    key={item.id}
                    to={item.path}
                    onClick={closeSidebar}
                    className={({ isActive }) => `w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all relative group ${isActive
                      ? 'text-red-400'
                      : ''
                    }`}
                    style={({ isActive }) => ({
                      background: isActive ? 'var(--bg-active)' : 'transparent',
                      color: isActive ? undefined : 'var(--text-muted)',
                    })}
                  >
                    {({ isActive }) => (
                      <>
                        {isActive && (
                          <motion.div
                            layoutId="sidebar-indicator"
                            className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-6 bg-red-500 rounded-r-full"
                            transition={{ type: 'spring', stiffness: 400, damping: 30 }}
                          />
                        )}
                        <item.icon className={`w-[18px] h-[18px] flex-shrink-0 transition-colors ${isActive ? 'text-red-400' : ''}`} style={!isActive ? { color: 'var(--text-faint)' } : {}} />
                        <span className="flex-1 text-left">{item.label}</span>
                        {item.badge && (
                          <span className="text-[9px] font-black px-1.5 py-0.5 rounded-md bg-red-500/20 text-red-400 tracking-wider border border-red-500/30">
                            {item.badge}
                          </span>
                        )}
                      </>
                    )}
                  </NavLink>
                ))}
              </div>
            </div>
          ))}
        </nav>

        {/* Bottom: Settings + User */}
        {['admin', 'qa', 'manager'].includes((currentUser.role || 'user').toLowerCase()) && (
          <div className="px-3 py-3 space-y-0.5" style={{ borderTop: '1px solid var(--border-color)' }}>
            <NavLink
              to="/settings"
              onClick={closeSidebar}
              className={({ isActive }) => `w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${isActive
                ? 'text-red-400'
                : ''
              }`}
              style={({ isActive }) => ({
                background: isActive ? 'var(--bg-active)' : 'transparent',
                color: isActive ? undefined : 'var(--text-muted)',
              })}
            >
              <SettingsIcon className="w-[18px] h-[18px] flex-shrink-0" />
              <span>Settings</span>
            </NavLink>
          </div>
        )}

        {/* User Profile */}
        <div className="px-4 py-4" style={{ borderTop: '1px solid var(--border-color)' }}>
          <div className="flex items-center gap-3 p-3 rounded-xl cursor-pointer transition-all group" style={{ background: 'var(--bg-hover)', border: '1px solid var(--border-color)' }}>
            <div className="w-9 h-9 rounded-full bg-gradient-to-br from-red-600 to-red-500 flex items-center justify-center text-white text-sm font-bold flex-shrink-0 shadow-sm relative uppercase">
              {currentUser.username.charAt(0)}
              <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-emerald-500 rounded-full" style={{ border: '2px solid var(--bg-sidebar)' }}></div>
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-sm font-bold truncate" style={{ color: 'var(--text-primary)' }}>{currentUser.username}</div>
              <div className="text-[11px] text-red-400 truncate font-semibold uppercase">{currentUser.role}</div>
            </div>
            <button
              onClick={handleLogout}
              className="p-2 rounded-lg hover:text-red-400 hover:bg-red-500/10 transition-all"
              style={{ color: 'var(--text-faint)' }}
              title="Logout"
            >
              <LogOut className="w-4 h-4 flex-shrink-0" />
            </button>
          </div>
        </div>
      </aside>

      {/* ══════════════════════════════════════════
          MAIN CONTENT
      ══════════════════════════════════════════ */}
      <div className="flex-1 flex flex-col min-h-screen min-w-0">

        {/* ── Top Header ── */}
        <header className="sticky top-0 z-30 backdrop-blur-xl" style={{ background: 'var(--bg-header)', borderBottom: '1px solid var(--border-color)' }}>
          <div className="flex items-center gap-4 px-4 md:px-8 h-16">

            {/* Mobile menu toggle */}
            <button
              onClick={() => setIsSidebarOpen(true)}
              className="lg:hidden p-2 rounded-lg transition-all flex-shrink-0"
              style={{ color: 'var(--text-muted)' }}
            >
              <Menu className="w-5 h-5" />
            </button>

            {/* Page title + breadcrumb */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-1.5 text-[11px] font-medium mb-0.5" style={{ color: 'var(--text-muted)' }}>
                <span className="text-red-400 font-semibold">Devoteam</span>
                <ChevronRight className="w-3 h-3" style={{ color: 'var(--text-faint)' }} />
                <span>{currentPage?.title}</span>
              </div>
              <h1 className="text-[18px] font-black tracking-tight leading-none truncate" style={{ color: 'var(--text-primary)' }}>
                {currentPage?.title}
              </h1>
            </div>

            {/* Right controls */}
            <div className="flex items-center gap-3 flex-shrink-0">
              {/* Theme Toggle */}
              <button
                onClick={toggleTheme}
                className="p-2.5 rounded-xl transition-all active:scale-95"
                style={{
                  background: 'var(--bg-hover)',
                  border: '1px solid var(--border-color)',
                  color: 'var(--text-muted)',
                }}
                title={isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
              >
                {isDark ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-indigo-500" />}
              </button>

              {currentUser?.role?.toLowerCase() !== 'guest' && (
                <button
                  onClick={() => navigate('/upload')}
                  className="hidden sm:flex items-center gap-2 px-4 py-2 primary-gradient rounded-xl text-sm font-bold text-white transition-all hover:opacity-90 active:scale-[0.98]"
                >
                  <Plus className="w-4 h-4" />
                  New Requirement
                </button>
              )}
            </div>
          </div>
        </header>

        {/* ── Page Content ── */}
        <main className="flex-1 overflow-y-auto relative custom-scrollbar">
          <AnimatePresence mode="wait">
            <motion.div
              key={location.pathname}
              initial={{ opacity: 0, y: 10, scale: 0.99 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -10, scale: 0.99 }}
              transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
              className="p-4 md:p-8 max-w-[1600px] mx-auto z-10 relative"
            >
              <Routes>
                <Route path="/" element={<Dashboard currentUser={currentUser} onNewRequirement={() => navigate('/upload')} />} />
                <Route path="/requirements" element={<RequirementList onAnalyze={(id) => navigate(`/editor?req=${id}`)} />} />
                <Route path="/upload" element={<RequirementUpload onAnalysisComplete={(id) => navigate(`/editor?req=${id}`)} />} />
                <Route path="/editor" element={<ScenarioEditor />} />
                <Route path="/matrix" element={<TraceabilityMatrix />} />
                <Route path="/execution" element={<ExecutionHistory />} />
                <Route path="/settings" element={<Settings />} />
                <Route path="/users" element={<UserManagement currentUser={currentUser} />} />
                <Route path="/documentation" element={<Documentation />} />
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </motion.div>
          </AnimatePresence>
        </main>

        {/* ── Footer Status Bar ── */}
        <footer className="hidden lg:flex items-center justify-between px-8 py-2 backdrop-blur-xl text-[11px] font-semibold z-20 relative" style={{ background: 'var(--bg-header)', borderTop: '1px solid var(--border-color)', color: 'var(--text-muted)' }}>
          <div className="flex items-center gap-6">
            <span className="flex items-center gap-1.5"><CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" /> API Connected</span>
            <span className="flex items-center gap-1.5"><Shield className="w-3.5 h-3.5 text-blue-400" /> GitLab CI/CD Active</span>
            <span className="flex items-center gap-1.5"><Zap className="w-3.5 h-3.5 text-amber-400" /> Gemini 2.0 Flash</span>
          </div>
          <div className="flex items-center gap-6">
            <span style={{ color: 'var(--text-muted)' }}>Devoteam TestGenAI v4.0.0</span>
            <span className="flex items-center gap-1.5 px-2 py-0.5 rounded-md bg-emerald-500/10 border border-emerald-500/20 text-emerald-400"><TrendingUp className="w-3 h-3" /> System Optimal</span>
          </div>
        </footer>
      </div>
    </div>
  );
}

export default App;
