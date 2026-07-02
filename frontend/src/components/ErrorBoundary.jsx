import React from 'react';
import { AlertTriangle, RotateCcw } from 'lucide-react';

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('[ErrorBoundary]', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-[var(--bg-primary)] p-8">
          <div className="card p-12 max-w-lg w-full text-center">
            <div className="w-20 h-20 mx-auto mb-6 rounded-2xl bg-red-500/10 border border-red-500/20 flex items-center justify-center">
              <AlertTriangle className="w-10 h-10 text-red-400" />
            </div>
            <h2 className="text-2xl font-bold text-[var(--text-primary)] mb-3 tracking-tight">
              Something went wrong
            </h2>
            <p className="text-sm text-[var(--text-secondary)] mb-8 leading-relaxed">
              An unexpected error occurred in the application. This has been logged automatically.
            </p>
            <pre className="text-xs text-red-300/70 bg-red-500/5 border border-red-500/10 rounded-xl p-4 mb-8 text-left overflow-auto max-h-32 font-mono">
              {this.state.error?.message || 'Unknown error'}
            </pre>
            <button
              onClick={() => window.location.reload()}
              className="inline-flex items-center gap-2 px-6 py-3 primary-gradient text-white rounded-xl font-bold text-sm transition-all hover:opacity-90 active:scale-[0.98]"
            >
              <RotateCcw className="w-4 h-4" />
              Reload Application
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
