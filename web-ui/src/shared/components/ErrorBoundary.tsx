import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertCircle, RotateCcw } from 'lucide-react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught component error:', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="glass-card" style={{ padding: '32px', textAlign: 'center', margin: '24px auto', maxWidth: '500px' }}>
          <AlertCircle size={40} color="#ef4444" style={{ marginBottom: '12px' }} />
          <h3 style={{ fontSize: '1.2rem', fontWeight: 700, marginBottom: '8px' }}>Something went wrong</h3>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '20px' }}>
            {this.state.error?.message || 'An unexpected rendering error occurred in this view.'}
          </p>
          <button
            onClick={() => this.setState({ hasError: false, error: null })}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              padding: '8px 16px',
              backgroundColor: 'var(--color-primary)',
              color: '#ffffff',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontWeight: 600,
            }}
          >
            <RotateCcw size={16} />
            Try Again
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
