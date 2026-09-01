import React from 'react';
import { useNavigate } from 'react-router-dom';
import { AlertTriangle, ArrowLeft } from 'lucide-react';

export const NotFoundPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div
      style={{
        flex: 1,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: 'var(--bg-main)',
        padding: '24px',
        minHeight: '400px',
      }}
    >
      <div
        className="scada-card"
        style={{
          maxWidth: '420px',
          width: '100%',
          padding: '32px',
          textAlign: 'center',
          backgroundColor: 'var(--bg-secondary)',
          border: '1px solid #30363d',
          borderRadius: '8px',
          boxShadow: '0 8px 24px rgba(0, 0, 0, 0.4)',
        }}
      >
        <div
          style={{
            width: '56px',
            height: '56px',
            borderRadius: '50%',
            backgroundColor: 'rgba(245, 158, 11, 0.12)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 16px auto',
          }}
        >
          <AlertTriangle size={28} color="#f59e0b" />
        </div>
        <h2 style={{ fontSize: '1.3rem', fontWeight: 800, marginBottom: '8px', color: 'var(--text-main)' }}>
          404 — Page Not Found
        </h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '24px', lineHeight: 1.5 }}>
          The requested operational view or telemetry path does not exist on this SCADA node.
        </p>
        <button
          onClick={() => navigate('/')}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            backgroundColor: 'var(--color-primary)',
            color: 'var(--text-main)',
            border: 'none',
            borderRadius: '6px',
            padding: '10px 20px',
            fontSize: '0.85rem',
            fontWeight: 700,
            cursor: 'pointer',
            transition: 'all 0.15s ease',
          }}
        >
          <ArrowLeft size={14} /> Return to Dashboard
        </button>
      </div>
    </div>
  );
};

export default NotFoundPage;
