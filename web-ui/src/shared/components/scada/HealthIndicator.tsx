/**
 * SCADA HealthIndicator Component
 * Compact health pill with dot status indicator.
 */

import React from 'react';

interface HealthIndicatorProps {
  label: string;
  isHealthy: boolean;
  tooltip?: string;
}

export const HealthIndicator: React.FC<HealthIndicatorProps> = ({ label, isHealthy, tooltip }) => {
  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '6px',
        fontSize: '0.72rem',
        fontWeight: 700,
        padding: '3px 8px',
        borderRadius: '6px',
        backgroundColor: 'rgba(255, 255, 255, 0.03)',
        border: '1px solid var(--border-color)',
        color: 'var(--text-main)',
      }}
      title={tooltip || `${label} status`}
    >
      <span
        style={{
          width: '6px',
          height: '6px',
          borderRadius: '50%',
          backgroundColor: isHealthy ? '#10b981' : '#ef4444',
          boxShadow: `0 0 6px ${isHealthy ? 'rgba(16,185,129,0.5)' : 'rgba(239,68,68,0.5)'}`,
        }}
      />
      <span>{label}</span>
    </span>
  );
};
