/**
 * SCADA StatusBadge Component
 * Presentational SCADA 5-state badge with FDS color coding, tabular typography, and pulse support.
 * FDS Section 92, 106
 */

import React from 'react';

export interface StatusBadgeProps {
  status: string;
  color?: string;
  bg?: string;
  icon?: React.ReactNode;
  label?: string;
  size?: 'sm' | 'md' | 'lg';
  showPulse?: boolean;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  color,
  bg,
  icon,
  label,
  size = 'md',
  showPulse = false,
}) => {
  const getStyle = () => {
    const s = status.toUpperCase();
    if (color && bg) {
      return { bg, text: color, border: color, dot: color };
    }

    switch (s) {
      case 'HEALTHY':
      case 'GREEN':
      case 'ONLINE':
      case 'RUNNING':
      case 'ACTIVE':
      case 'CONNECTED':
      case 'CURRENT GREEN':
        return { bg: 'rgba(63, 185, 80, 0.15)', text: '#3fb950', border: 'rgba(63, 185, 80, 0.4)', dot: '#3fb950' };

      case 'WARNING':
      case 'YELLOW':
      case 'MEDIUM':
      case 'WAITING':
      case 'DEGRADED':
        return { bg: 'rgba(242, 193, 78, 0.15)', text: '#f2c14e', border: 'rgba(242, 193, 78, 0.4)', dot: '#f2c14e' };

      case 'CRITICAL':
      case 'EMERGENCY':
      case 'HIGH':
      case 'RED':
      case 'STALLED':
      case 'DISCONNECTED':
      case 'FAILED':
        return { bg: 'rgba(229, 83, 75, 0.15)', text: '#e5534b', border: 'rgba(229, 83, 75, 0.4)', dot: '#e5534b' };

      case 'OFFLINE':
      case 'LOW':
      case 'INFO':
      default:
        return { bg: 'rgba(92, 102, 112, 0.15)', text: '#b0bac5', border: 'rgba(92, 102, 112, 0.4)', dot: '#7e8791' };
    }
  };

  const style = getStyle();
  const displayLabel = label || status;
  const padding = size === 'sm' ? '2px 6px' : size === 'lg' ? '6px 12px' : '3px 8px';
  const fontSize = size === 'sm' ? '0.68rem' : size === 'lg' ? '0.8rem' : '0.72rem';

  return (
    <span
      className="font-mono-num"
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '6px',
        padding,
        borderRadius: '4px',
        fontSize,
        fontWeight: 700,
        backgroundColor: style.bg,
        color: style.text,
        border: `1px solid ${style.border}`,
        letterSpacing: '0.04em',
        textTransform: 'uppercase',
      }}
    >
      {icon || (
        <span
          className={showPulse ? 'pulse-active' : ''}
          style={{
            width: '6px',
            height: '6px',
            borderRadius: '50%',
            backgroundColor: style.dot,
          }}
        />
      )}
      <span>{displayLabel}</span>
    </span>
  );
};
