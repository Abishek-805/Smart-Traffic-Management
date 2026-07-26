import React from 'react';

interface StatusBadgeProps {
  status: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
  const s = status.toUpperCase();

  const getColors = () => {
    switch (s) {
      case 'RUNNING':
      case 'ACTIVE':
      case 'CONNECTED':
      case 'HEALTHY':
        return { bg: 'rgba(16, 185, 129, 0.15)', border: '#10b981', text: '#10b981' };
      case 'DEGRADED':
      case 'WARNING':
      case 'PAIRING':
        return { bg: 'rgba(245, 158, 11, 0.15)', border: '#f59e0b', text: '#f59e0b' };
      default:
        return { bg: 'rgba(239, 68, 68, 0.15)', border: '#ef4444', text: '#ef4444' };
    }
  };

  const { bg, border, text } = getColors();

  return (
    <span style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: '6px',
      padding: '4px 10px',
      borderRadius: '20px',
      backgroundColor: bg,
      border: `1px solid ${border}`,
      color: text,
      fontSize: '0.72rem',
      fontWeight: 700,
      letterSpacing: '0.03em',
    }}>
      <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: text }} />
      {s}
    </span>
  );
};
