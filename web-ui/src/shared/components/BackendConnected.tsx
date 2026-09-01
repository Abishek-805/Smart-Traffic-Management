import React from 'react';
import { useSystemHealth } from '../hooks/useSystemQueries';
import { WifiOff, RefreshCw } from 'lucide-react';

export const BackendConnected: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isError, refetch, isFetching } = useSystemHealth();

  if (isError) {
    return (
      <div style={{
        height: '100vh',
        width: '100vw',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: 'var(--bg-main)',
        padding: '24px',
      }}>
        <div className="glass-card" style={{
          maxWidth: '460px',
          width: '100%',
          padding: '32px',
          textAlign: 'center',
        }}>
          <div style={{
            width: '64px',
            height: '64px',
            borderRadius: '50%',
            backgroundColor: 'rgba(239, 68, 68, 0.15)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 20px auto',
          }}>
            <WifiOff size={32} color="#ef4444" />
          </div>
          <h2 style={{ fontSize: '1.4rem', fontWeight: 700, marginBottom: '8px' }}>Backend Unreachable</h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '24px', lineHeight: 1.5 }}>
            Unable to establish connection with the FastAPI backend server (`/api/v1/system/health`). Please check if the server is running on port 8000.
          </p>
          <button
            onClick={() => refetch()}
            disabled={isFetching}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              backgroundColor: 'var(--color-primary)',
              color: 'var(--text-main)',
              border: 'none',
              borderRadius: '8px',
              padding: '10px 20px',
              fontSize: '0.9rem',
              fontWeight: 600,
              cursor: isFetching ? 'not-allowed' : 'pointer',
              opacity: isFetching ? 0.7 : 1,
            }}
          >
            <RefreshCw size={16} className={isFetching ? 'spin' : ''} />
            {isFetching ? 'Reconnecting...' : 'Retry Connection'}
          </button>
        </div>
      </div>
    );
  }

  return <>{children}</>;
};
