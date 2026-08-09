/**
 * ConfigAccordions (Settings Feature Sub-Component)
 * Five accordion panels extracted from SettingsPage:
 * 1. AI & Perception Parameters
 * 2. Camera Slots & Hardware Assignments
 * 3. Signal Controller Hardware (ESP32)
 * 4. Application Settings
 * 5. Developer Controls & Observability (gated by FEATURE_FLAGS.enableDeveloperOverlay)
 */

import React, { useState } from 'react';
import { useSettings } from '../../contexts/SettingsContext';
import { useObservability } from '../../shared/hooks/useObservability';
import { useNotifications } from '../../contexts/NotificationContext';
import { useCameraConfigs } from '../../shared/hooks/useSystemQueries';
import { StatusBadge } from '../../shared/components/scada/StatusBadge';
import { FEATURE_FLAGS } from '../../config/featureFlags';
import {
  Sliders, Cpu, ChevronDown, ChevronUp, Smartphone, Layers, Sparkles, Activity,
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const inputStyle: React.CSSProperties = {
  width: '100%',
  padding: '8px 12px',
  borderRadius: '6px',
  backgroundColor: 'rgba(0,0,0,0.2)',
  border: '1px solid var(--border-color)',
  color: 'var(--text-main)',
  fontSize: '0.8rem',
};

const labelStyle: React.CSSProperties = {
  fontSize: '0.75rem',
  fontWeight: 700,
  display: 'block',
  marginBottom: '4px',
  color: 'var(--text-muted)',
};

interface AccordionHeaderProps {
  icon: React.ReactNode;
  title: string;
  isOpen: boolean;
  onToggle: () => void;
  badge?: React.ReactNode;
}

const AccordionHeader: React.FC<AccordionHeaderProps> = ({ icon, title, isOpen, onToggle, badge }) => (
  <button
    onClick={onToggle}
    aria-expanded={isOpen}
    style={{
      width: '100%',
      backgroundColor: 'transparent',
      border: 'none',
      color: 'var(--text-main)',
      padding: '16px 20px',
      fontSize: '0.95rem',
      fontWeight: 800,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      cursor: 'pointer',
    }}
  >
    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
      {icon}
      <span>{title}</span>
    </div>
    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
      {badge}
      {isOpen
        ? <ChevronUp size={18} aria-hidden="true" />
        : <ChevronDown size={18} aria-hidden="true" />}
    </div>
  </button>
);

export const ConfigAccordions: React.FC = () => {
  const navigate = useNavigate();
  const { settings, updateSettings } = useSettings();
  const { addToast } = useNotifications();
  const { data: cameraConfigs } = useCameraConfigs();
  const obs = useObservability();
  const [openSection, setOpenSection] = useState<string | null>('ai');

  const toggle = (s: string) => setOpenSection(openSection === s ? null : s);

  const handleResetFirstLaunch = () => {
    if (confirm('Are you sure you want to reset the first launch state? This will clear paired cameras and direct you to the initial setup.')) {
      localStorage.removeItem('scc_connected_cameras');
      localStorage.removeItem('scc_setup_complete');
      addToast('warning', 'First Launch Reset', 'System states cleared. Redirecting to setup initialization.');
      navigate('/');
      window.location.reload();
    }
  };

  const handleLoadDemoData = () => {
    localStorage.setItem('scc_connected_cameras', JSON.stringify(['north', 'south', 'east', 'west']));
    localStorage.setItem('scc_setup_complete', 'true');
    addToast('success', 'Demo Data Loaded', 'Configured 4 default camera slots.');
    navigate('/');
    window.location.reload();
  };

  const handleClearLocalStorage = () => {
    if (confirm('Are you sure you want to clear all local storage settings? This is destructive and will purge all local preferences.')) {
      localStorage.clear();
      addToast('error', 'Local Cache Purged', 'Cleared all local storage settings.');
      navigate('/');
      window.location.reload();
    }
  };

  const devBtnStyle = (color: string): React.CSSProperties => ({
    backgroundColor: `rgba(${color}, 0.12)`,
    color: `rgb(${color})`,
    border: `1px solid rgba(${color}, 0.3)`,
    borderRadius: '6px',
    padding: '8px 14px',
    fontWeight: 700,
    fontSize: '0.78rem',
    cursor: 'pointer',
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>

      {/* 1. AI & Perception */}
      <div className="scada-card" style={{ overflow: 'hidden' }}>
        <AccordionHeader
          icon={<Sliders size={18} color="var(--color-primary)" aria-hidden="true" />}
          title="AI & Perception Parameters"
          isOpen={openSection === 'ai'}
          onToggle={() => toggle('ai')}
          badge={<StatusBadge status="ACTIVE" color="#10b981" bg="rgba(16,185,129,0.12)" />}
        />
        {openSection === 'ai' && (
          <div style={{ padding: '20px', borderTop: '1px solid var(--border-color)', display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                <label style={{ fontSize: '0.82rem', fontWeight: 700 }}>YOLO11 Detection Confidence Threshold</label>
                <span style={{ fontSize: '0.82rem', fontWeight: 800, color: 'var(--color-primary)' }}>
                  {(settings.confidenceThreshold * 100).toFixed(0)}%
                </span>
              </div>
              <input
                type="range" min={0.1} max={0.9} step={0.05}
                value={settings.confidenceThreshold}
                onChange={(e) => updateSettings({ confidenceThreshold: parseFloat(e.target.value) })}
                aria-label="YOLO11 confidence threshold"
                style={{ width: '100%' }}
              />
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '16px' }}>
              <div>
                <label style={labelStyle}>MINIMUM GREEN TIME (SECONDS)</label>
                <input type="number" value={settings.minGreenTime}
                  onChange={(e) => updateSettings({ minGreenTime: Number(e.target.value) })}
                  aria-label="Minimum green time in seconds" style={inputStyle} />
              </div>
              <div>
                <label style={labelStyle}>MAXIMUM GREEN TIME (SECONDS)</label>
                <input type="number" value={settings.maxGreenTime}
                  onChange={(e) => updateSettings({ maxGreenTime: Number(e.target.value) })}
                  aria-label="Maximum green time in seconds" style={inputStyle} />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* 2. Camera Slots */}
      <div className="scada-card" style={{ overflow: 'hidden' }}>
        <AccordionHeader
          icon={<Smartphone size={18} color="#10b981" aria-hidden="true" />}
          title="Camera Slots & Hardware Assignments"
          isOpen={openSection === 'devices'}
          onToggle={() => toggle('devices')}
        />
        {openSection === 'devices' && (
          <div style={{ padding: '20px', borderTop: '1px solid var(--border-color)', fontSize: '0.82rem' }}>
            <p style={{ color: 'var(--text-muted)', marginBottom: '12px' }}>
              Camera streams are matched dynamically to approach directions.
            </p>
            <div style={{ padding: '12px', borderRadius: '6px', backgroundColor: 'rgba(0,0,0,0.2)', border: '1px solid var(--border-color)', display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '10px' }}>
              <div><strong>North Slot:</strong> {cameraConfigs?.streams?.['north']?.source || 'North Approach Feed'}</div>
              <div><strong>South Slot:</strong> {cameraConfigs?.streams?.['south']?.source || 'South Approach Feed'}</div>
              <div><strong>East Slot:</strong> {cameraConfigs?.streams?.['east']?.source || 'East Approach Feed'}</div>
              <div><strong>West Slot:</strong> {cameraConfigs?.streams?.['west']?.source || 'West Approach Feed'}</div>
            </div>
          </div>
        )}
      </div>

      {/* 3. ESP32 Signal Controller */}
      <div className="scada-card" style={{ overflow: 'hidden' }}>
        <AccordionHeader
          icon={<Cpu size={18} color="#06b6d4" aria-hidden="true" />}
          title="Signal Controller Hardware (ESP32)"
          isOpen={openSection === 'controller'}
          onToggle={() => toggle('controller')}
        />
        {openSection === 'controller' && (
          <div style={{ padding: '20px', borderTop: '1px solid var(--border-color)', display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '16px' }}>
            <div>
              <label style={labelStyle}>SERIAL PORT (COM / TTY)</label>
              <input type="text" value={settings.comPort}
                onChange={(e) => updateSettings({ comPort: e.target.value })}
                aria-label="Serial port" style={inputStyle} />
            </div>
            <div>
              <label style={labelStyle}>BAUD RATE</label>
              <select value={settings.baudRate}
                onChange={(e) => updateSettings({ baudRate: Number(e.target.value) })}
                aria-label="Baud rate" style={inputStyle}>
                <option value={9600}>9600 Baud</option>
                <option value={115200}>115200 Baud</option>
              </select>
            </div>
          </div>
        )}
      </div>

      {/* 4. Application Settings */}
      <div className="scada-card" style={{ overflow: 'hidden' }}>
        <AccordionHeader
          icon={<Layers size={18} color="#f59e0b" aria-hidden="true" />}
          title="Application Settings"
          isOpen={openSection === 'app'}
          onToggle={() => toggle('app')}
        />
        {openSection === 'app' && (
          <div style={{ padding: '20px', borderTop: '1px solid var(--border-color)', display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <input
                type="checkbox" id="notifications-enabled"
                checked={settings.enableNotifications}
                onChange={(e) => updateSettings({ enableNotifications: e.target.checked })}
                style={{ width: '16px', height: '16px', cursor: 'pointer' }}
              />
              <label htmlFor="notifications-enabled" style={{ fontSize: '0.82rem', fontWeight: 600, cursor: 'pointer' }}>
                Enable Audio Alerts on Phase Preemptions
              </label>
            </div>
          </div>
        )}
      </div>

      {/* 5. Developer Controls — gated by feature flag */}
      {FEATURE_FLAGS.enableDeveloperOverlay && (
        <div className="scada-card" style={{ overflow: 'hidden' }}>
          <AccordionHeader
            icon={<Sparkles size={18} color="#ef4444" aria-hidden="true" />}
            title="Developer Controls & Observability Diagnostics"
            isOpen={openSection === 'developer'}
            onToggle={() => toggle('developer')}
          />
          {openSection === 'developer' && (
            <div style={{ padding: '20px', borderTop: '1px solid var(--border-color)', display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {/* Observability Panel */}
              <div style={{ padding: '14px', borderRadius: '6px', backgroundColor: 'rgba(59,130,246,0.08)', border: '1px solid rgba(59,130,246,0.2)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
                  <Activity size={16} color="#3b82f6" aria-hidden="true" />
                  <strong style={{ fontSize: '0.85rem' }}>Real-Time Observability Diagnostics</strong>
                  <StatusBadge
                    status={obs.isPerformingWell ? 'PERFORMING EXCELLENT' : 'DEGRADED'}
                    color={obs.isPerformingWell ? '#10b981' : '#f59e0b'}
                  />
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '10px', fontSize: '0.78rem' }}>
                  <div>FPS Target: <strong>{obs.fps} FPS</strong></div>
                  <div>Render Duration: <strong>{obs.renderDurationMs} ms (&lt;16ms target)</strong></div>
                  <div>WS Latency: <strong>{obs.wsLatencyMs} ms</strong></div>
                  <div>Frame Age: <strong>{obs.frameAgeMs} ms</strong></div>
                </div>
              </div>

              {/* Developer Action Buttons */}
              <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                <button onClick={handleResetFirstLaunch} aria-label="Reset first launch state" style={devBtnStyle('245, 158, 11')}>
                  Reset First Launch
                </button>
                <button onClick={handleLoadDemoData} aria-label="Load demo data" style={devBtnStyle('16, 185, 129')}>
                  Load Demo Data
                </button>
                <button onClick={handleClearLocalStorage} aria-label="Clear local cache" style={devBtnStyle('239, 68, 68')}>
                  Clear Local Cache
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
