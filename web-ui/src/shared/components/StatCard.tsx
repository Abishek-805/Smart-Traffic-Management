import React from 'react';
import { LucideIcon } from 'lucide-react';

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  color?: string;
  trend?: string;
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  color = '#3b82f6',
  trend,
}) => {
  return (
    <div className="glass-card" style={{ padding: '20px', display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
      <div>
        <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
          {title}
        </span>
        <h3 style={{ fontSize: '1.75rem', fontWeight: 800, margin: '6px 0 2px 0', letterSpacing: '-0.02em' }}>
          {value}
        </h3>
        {subtitle && (
          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '2px' }}>
            {subtitle}
          </p>
        )}
        {trend && (
          <span style={{ fontSize: '0.75rem', color: '#10b981', fontWeight: 600, marginTop: '4px', display: 'inline-block' }}>
            {trend}
          </span>
        )}
      </div>
      <div style={{
        padding: '10px',
        borderRadius: '10px',
        backgroundColor: `${color}18`,
        border: `1px solid ${color}30`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}>
        <Icon size={22} color={color} />
      </div>
    </div>
  );
};
