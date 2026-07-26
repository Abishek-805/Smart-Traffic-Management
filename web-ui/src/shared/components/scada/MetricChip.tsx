/**
 * SCADA MetricChip Component
 * High-density icon metric chip with title tooltip on hover.
 */

import React from 'react';

interface MetricChipProps {
  icon: string;
  value: string | number;
  label: string;
  color?: string;
  highlight?: boolean;
  'aria-label'?: string;
}

export const MetricChip: React.FC<MetricChipProps> = ({
  icon,
  value,
  label,
  color = 'var(--text-main)',
  highlight = false,
  'aria-label': ariaLabel,
}) => {
  return (
    <div
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '5px',
        padding: '4px 8px',
        borderRadius: '6px',
        backgroundColor: highlight ? 'rgba(59, 130, 246, 0.12)' : 'rgba(255, 255, 255, 0.04)',
        border: `1px solid ${highlight ? 'rgba(59, 130, 246, 0.3)' : 'var(--border-color)'}`,
        fontSize: '0.78rem',
        fontWeight: 700,
        color: color,
        cursor: 'help',
        transition: 'all 150ms ease',
      }}
      title={label}
      aria-label={ariaLabel || label}
    >
      <span style={{ fontSize: '0.85rem' }} aria-hidden="true">{icon}</span>
      <span>{value}</span>
    </div>
  );
};
