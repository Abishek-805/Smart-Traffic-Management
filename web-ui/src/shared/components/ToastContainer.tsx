import React from 'react';
import { useNotifications, ToastItem } from '../../contexts/NotificationContext';
import { CheckCircle2, AlertTriangle, AlertCircle, Info, X } from 'lucide-react';

export const ToastContainer: React.FC = () => {
  const { toasts, removeToast } = useNotifications();

  if (toasts.length === 0) return null;

  return (
    <div style={{
      position: 'fixed',
      bottom: '24px',
      right: '24px',
      zIndex: 9999,
      display: 'flex',
      flexDirection: 'column',
      gap: '10px',
      maxWidth: '380px',
      width: '100%',
    }}>
      {toasts.map((toast) => (
        <ToastCard key={toast.id} toast={toast} onClose={() => removeToast(toast.id)} />
      ))}
    </div>
  );
};

const ToastCard: React.FC<{ toast: ToastItem; onClose: () => void }> = ({ toast, onClose }) => {
  const getIcon = () => {
    switch (toast.type) {
      case 'success': return <CheckCircle2 size={20} color="#10b981" />;
      case 'warning': return <AlertTriangle size={20} color="#f59e0b" />;
      case 'error': return <AlertCircle size={20} color="#ef4444" />;
      default: return <Info size={20} color="#3b82f6" />;
    }
  };

  const getBorderColor = () => {
    switch (toast.type) {
      case 'success': return '#10b981';
      case 'warning': return '#f59e0b';
      case 'error': return '#ef4444';
      default: return '#3b82f6';
    }
  };

  return (
    <div className="glass-card" style={{
      padding: '14px 16px',
      display: 'flex',
      alignItems: 'flex-start',
      gap: '12px',
      borderLeft: `4px solid ${getBorderColor()}`,
      position: 'relative',
    }}>
      <div style={{ marginTop: '2px' }}>{getIcon()}</div>
      <div style={{ flex: 1 }}>
        <h4 style={{ fontSize: '0.9rem', fontWeight: 600, marginBottom: '2px' }}>{toast.title}</h4>
        <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{toast.message}</p>
      </div>
      <button onClick={onClose} style={{
        background: 'none',
        border: 'none',
        color: 'var(--text-muted)',
        cursor: 'pointer',
      }}>
        <X size={16} />
      </button>
    </div>
  );
};
