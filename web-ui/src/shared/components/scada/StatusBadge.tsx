/**
 * SCADA StatusBadge Component
 * Presentational badge with status color, icon, and label.
 */

import React from 'react';

interface StatusBadgeProps {
  status: string;
  color?: string;
  bg?: string;
  icon?: React.ReactNode;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, color = '#10b981', bg = 'rgba(16, 185, 129, 0.15)', icon }) => {
  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '6px',
        padding: '3px 10px',
        borderRadius: '12px',
        fontSize: '0.72rem',
        fontWeight: 800,
        backgroundColor: bg,
        color: color,
        border: `1px solid ${color}`,
        letterSpacing: '0.02em',
      }}
    >
      {icon}
      <span>{status}</span>
    </span>
  );
};
