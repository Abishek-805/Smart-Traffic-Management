/**
 * LogFilters (Logs Feature Sub-Component)
 * Left-column filter sidebar: category nav, severity level selector, pinned critical events.
 */

import React from 'react';
import { LogCategory } from '../../types';
import { ShieldAlert } from 'lucide-react';

const CATEGORIES: LogCategory[] = ['ALL', 'INFO', 'WARNING', 'ERROR', 'AI', 'NODE', 'ESP32', 'SYSTEM'];

interface LogFiltersProps {
  selectedCategory: LogCategory;
  onSelectCategory: (cat: LogCategory) => void;
}

export const LogFilters: React.FC<LogFiltersProps> = ({ selectedCategory, onSelectCategory }) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* Category Filter */}
      <div className="scada-card" style={{ padding: '16px' }}>
        <h4
          style={{
            fontSize: '0.82rem',
            fontWeight: 800,
            color: 'var(--text-muted)',
            marginBottom: '12px',
            letterSpacing: '0.04em',
          }}
        >
          COMPONENT CATEGORY
        </h4>
        <nav aria-label="Log category filter">
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            {CATEGORIES.map((cat) => (
              <button
                key={cat}
                onClick={() => onSelectCategory(cat)}
                aria-pressed={selectedCategory === cat}
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '8px 12px',
                  borderRadius: '6px',
                  border: '1px solid transparent',
                  backgroundColor:
                    selectedCategory === cat ? 'rgba(59, 130, 246, 0.15)' : 'transparent',
                  color: selectedCategory === cat ? '#ffffff' : 'var(--text-muted)',
                  fontSize: '0.8rem',
                  fontWeight: selectedCategory === cat ? 700 : 500,
                  cursor: 'pointer',
                  textAlign: 'left',
                }}
              >
                <span>{cat}</span>
                {selectedCategory === cat && (
                  <span
                    style={{
                      width: '6px',
                      height: '6px',
                      borderRadius: '50%',
                      backgroundColor: '#3b82f6',
                    }}
                    aria-hidden="true"
                  />
                )}
              </button>
            ))}
          </div>
        </nav>
      </div>

      {/* Pinned Critical Events */}
      <div className="scada-card" style={{ padding: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
          <ShieldAlert size={16} color="#f59e0b" aria-hidden="true" />
          <h4
            style={{
              fontSize: '0.82rem',
              fontWeight: 800,
              color: 'var(--text-muted)',
              letterSpacing: '0.04em',
            }}
          >
            PINNED CRITICAL EVENTS
          </h4>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '0.75rem' }}>
          <div
            style={{
              padding: '8px',
              borderRadius: '4px',
              backgroundColor: 'rgba(16,185,129,0.06)',
              borderLeft: '3px solid #10b981',
            }}
          >
            <span style={{ fontWeight: 800, color: '#10b981' }}>13:27:30 [INFO]</span>
            <p style={{ color: 'var(--text-main)', margin: '2px 0 0 0' }}>
              YOLO11 perception engine online.
            </p>
          </div>
          <div
            style={{
              padding: '8px',
              borderRadius: '4px',
              backgroundColor: 'rgba(245,158,11,0.06)',
              borderLeft: '3px solid #f59e0b',
            }}
          >
            <span style={{ fontWeight: 800, color: '#f59e0b' }}>13:27:32 [WARNING]</span>
            <p style={{ color: 'var(--text-main)', margin: '2px 0 0 0' }}>
              Camera South frame update delayed.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
