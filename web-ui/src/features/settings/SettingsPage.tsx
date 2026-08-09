/**
 * SettingsPage (Settings Feature Module) — v3.1 thin composition
 * Owns header actions and build info panel.
 * Delegates accordion panels to ConfigAccordions sub-component.
 */

import React from 'react';
import { useSettings } from '../../contexts/SettingsContext';
import { useVersionInfo } from '../../shared/hooks/useSystemQueries';
import { useNotifications } from '../../contexts/NotificationContext';
import { ConfigAccordions } from './ConfigAccordions';
import { Save, RotateCcw, Info } from 'lucide-react';

export const SettingsPage: React.FC = () => {
  const { resetSettings } = useSettings();
  const { data: versionInfo } = useVersionInfo();
  const { addToast } = useNotifications();

  const handleSave = () =>
    addToast('success', 'Local Settings Saved', 'These settings are stored locally in this browser. They do not modify the running backend unless the backend explicitly supports applying them.');

  const handleReset = () => {
    if (confirm('Are you sure you want to reset all configurations to their default values?')) {
      resetSettings();
      addToast('info', 'Settings Reset', 'Restored local browser configuration to default values.');
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', maxWidth: '900px' }}>
      {/* Header */}
      <div className="scada-card" style={{ padding: '20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 800 }}>System Configuration &amp; Settings</h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.82rem' }}>
            Adjust AI perception bounds, device configurations, ESP32 communications, and interface controls.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '10px' }}>
          <button
            onClick={handleReset}
            aria-label="Reset settings to defaults"
            style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', backgroundColor: 'rgba(255,255,255,0.05)', color: 'var(--text-main)', border: '1px solid var(--border-color)', borderRadius: '6px', padding: '8px 14px', fontWeight: 600, fontSize: '0.8rem', cursor: 'pointer' }}
          >
            <RotateCcw size={14} aria-hidden="true" /> Reset Defaults
          </button>
          <button
            onClick={handleSave}
            aria-label="Save settings"
            style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', backgroundColor: 'var(--color-primary)', color: '#ffffff', border: 'none', borderRadius: '6px', padding: '8px 16px', fontWeight: 700, fontSize: '0.8rem', cursor: 'pointer' }}
          >
            <Save size={14} aria-hidden="true" /> Save Changes
          </button>
        </div>
      </div>

      {/* Disclaimer Banner */}
      <div
        className="scada-card"
        style={{
          padding: '12px 16px',
          backgroundColor: 'rgba(245, 158, 11, 0.1)',
          border: '1px solid rgba(245, 158, 11, 0.25)',
          borderRadius: '6px',
          color: '#f59e0b',
          fontSize: '0.8rem',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
        }}
      >
        <Info size={16} style={{ flexShrink: 0 }} />
        <span>
          <strong>System Settings Scope:</strong> These settings are stored locally in this browser. They do not modify the running backend unless the backend explicitly supports applying them.
        </span>
      </div>

      {/* Accordion Panels — delegated to ConfigAccordions */}
      <ConfigAccordions />

      {/* System Build Info */}
      <div className="scada-card" style={{ padding: '20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
          <Info size={18} color="var(--color-primary)" aria-hidden="true" />
          <h3 style={{ fontSize: '1rem', fontWeight: 800 }}>System Build Info</h3>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', fontSize: '0.8rem' }}>
          <div>
            <span style={{ color: 'var(--text-muted)', display: 'block', marginBottom: '2px' }}>VERSION</span>
            <strong style={{ color: 'var(--color-primary)' }}>{versionInfo?.version || '1.0.0'}</strong>
          </div>
          <div>
            <span style={{ color: 'var(--text-muted)', display: 'block', marginBottom: '2px' }}>BACKEND</span>
            <strong>{versionInfo?.backend || 'FastAPI'}</strong>
          </div>
          <div>
            <span style={{ color: 'var(--text-muted)', display: 'block', marginBottom: '2px' }}>FRONTEND</span>
            <strong>{versionInfo?.frontend || 'React SPA'}</strong>
          </div>
          <div>
            <span style={{ color: 'var(--text-muted)', display: 'block', marginBottom: '2px' }}>PROTOCOL</span>
            <strong>{versionInfo?.protocol || '1.0'}</strong>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;
