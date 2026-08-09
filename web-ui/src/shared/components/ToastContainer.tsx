import React from 'react';
import { useNotifications, ToastItem } from '../../contexts/NotificationContext';
import { CheckCircle2, AlertTriangle, AlertCircle, Info, X } from 'lucide-react';

export const ToastContainer: React.FC = () => {
  const { toasts, removeToast } = useNotifications();

  if (toasts.length === 0) return null;

  // Maximum 3 visible toasts per contract
  const visibleToasts = toasts.slice(-3);

  return (
    <div style={{
      position: 'fixed',
      bottom: '30px',
      right: '24px',
      zIndex: 9999,
      display: 'flex',
      flexDirection: 'column',
      gap: '8px',
      maxWidth: '360px',
      width: '100%',
    }}>
      {visibleToasts.map((toast) => (
        <ToastCard key={toast.id} toast={toast} onClose={() => removeToast(toast.id)} />
      ))}
    </div>
  );
};

const ToastCard: React.FC<{ toast: ToastItem; onClose: () => void }> = ({ toast, onClose }) => {
  const getIcon = () => {
    switch (toast.type) {
      case 'success': return <CheckCircle2 size={18} color="#10b981" />;
      case 'warning': return <AlertTriangle size={18} color="#f59e0b" />;
      case 'error': return <AlertCircle size={18} color="#ef4444" />;
      default: return <Info size={18} color="#58a6ff" />;
    }
  };

  const getBorderColor = () => {
    switch (toast.type) {
      case 'success': return '#10b981';
      case 'warning': return '#f59e0b';
      case 'error': return '#ef4444';
      default: return '#58a6ff';
    }
  };

  return (
    <div className="scada-card" style={{
      padding: '10px 12px',
      display: 'flex',
      alignItems: 'flex-start',
      gap: '10px',
      backgroundColor: '#161b22',
      borderLeft: `3px solid ${getBorderColor()}`,
      position: 'relative',
      boxShadow: '0 4px 12px rgba(0,0,0,0.5)',
    }}>
      <div style={{ marginTop: '2px' }}>{getIcon()}</div>
      <div style={{ flex: 1 }}>
        <h4 style={{ fontSize: '0.85rem', fontWeight: 700, marginBottom: '2px', color: '#ffffff' }}>{toast.title}</h4>
        <p style={{ fontSize: '0.75rem', color: '#8b949e' }}>{toast.message}</p>
      </div>
      <button onClick={onClose} style={{
        background: 'none',
        border: 'none',
        color: '#8b949e',
        cursor: 'pointer',
        padding: 0,
      }}>
        <X size={14} />
      </button>
    </div>
  );
};
