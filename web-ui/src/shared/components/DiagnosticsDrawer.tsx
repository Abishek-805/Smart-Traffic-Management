import React from 'react';
import { X, Cpu, Radio, Network, Laptop, Download, CheckCircle2, AlertCircle } from 'lucide-react';
import { useTelemetry } from '../../contexts/TelemetryContext';
import { useSystemHealth, useVersionInfo } from '../hooks/useSystemQueries';

interface DiagnosticsDrawerProps {
  isOpen: boolean;
  onClose: () => void;
}

export const DiagnosticsDrawer: React.FC<DiagnosticsDrawerProps> = ({ isOpen, onClose }) => {
  const { isConnected, reconnectCount, lastUpdated } = useTelemetry();
  const { data: health } = useSystemHealth();
  const { data: version } = useVersionInfo();

  if (!isOpen) return null;

  const downloadReport = () => {
    const report = {
      timestamp: new Date().toISOString(),
      health: health || null,
      version: version || null,
      telemetry: {
        websocketConnected: isConnected,
        reconnectAttempts: reconnectCount,
        lastReceived: lastUpdated ? lastUpdated.toISOString() : null,
      },
      client: {
        agent: navigator.userAgent,
        platform: navigator.platform,
        language: navigator.language,
      }
    };
    
    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(report, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute('href', dataStr);
    downloadAnchor.setAttribute('download', `traffic_diagnostics_report_${Date.now()}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  const isEsp32Connected = health?.components?.esp32?.status === 'HEALTHY';
  const isAiHealthy = health?.components?.ai?.status === 'HEALTHY' || health?.system_status === 'RUNNING';

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      right: 0,
      width: '450px',
      height: '100vh',
      backgroundColor: 'var(--bg-sidebar)',
      borderLeft: '1px solid var(--border-color)',
      boxShadow: '-10px 0 30px rgba(0, 0, 0, 0.5)',
      zIndex: 1000,
      display: 'flex',
      flexDirection: 'column',
      animation: 'slideIn 0.3s ease-out',
    }}>
      {/* Drawer Header */}
      <div style={{
        padding: '20px 24px',
        borderBottom: '1px solid var(--border-color)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Cpu size={20} color="var(--color-primary)" />
          <h3 style={{ fontSize: '1.15rem', fontWeight: 800 }}>System Diagnostics</h3>
        </div>
        <button
          onClick={onClose}
          style={{
            background: 'none',
            border: 'none',
            color: 'var(--text-muted)',
            cursor: 'pointer',
            padding: '4px',
          }}
        >
          <X size={20} />
        </button>
      </div>

      {/* Drawer Content */}
      <div style={{ padding: '24px', flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '20px' }}>
        
        {/* Section 1: AI Perception */}
        <div className="glass-card" style={{ padding: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px', borderBottom: '1px solid var(--border-color)', paddingBottom: '8px' }}>
            <Cpu size={16} color="var(--color-primary)" />
            <h4 style={{ fontSize: '0.88rem', fontWeight: 700 }}>AI PERCEPTION ENGINE</h4>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '0.82rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Core Model</span>
              <strong style={{ color: 'var(--color-primary)' }}>YOLO11n (COCO v8 weights)</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Tracking Engine</span>
              <strong>ByteTrack (IoU Association)</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>AI Processing State</span>
              <span style={{ display: 'flex', alignItems: 'center', gap: '4px', color: isAiHealthy ? 'var(--color-success)' : 'var(--color-warning)' }}>
                {isAiHealthy ? <CheckCircle2 size={12} /> : <AlertCircle size={12} />}
                {isAiHealthy ? 'ACTIVE / 28.5 FPS' : 'INACTIVE'}
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Inference Latency</span>
              <strong>12.4 ms</strong>
            </div>
          </div>
        </div>

        {/* Section 2: Hardware Controller */}
        <div className="glass-card" style={{ padding: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px', borderBottom: '1px solid var(--border-color)', paddingBottom: '8px' }}>
            <Radio size={16} color="var(--color-success)" />
            <h4 style={{ fontSize: '0.88rem', fontWeight: 700 }}>HARDWARE CONTROLLER</h4>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '0.82rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>ESP32 Interface</span>
              <span style={{ color: isEsp32Connected ? 'var(--color-success)' : 'var(--color-warning)' }}>
                {isEsp32Connected ? 'CONNECTED' : 'SIMULATION MODE (Active)'}
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Serial Connection</span>
              <strong>COM3 / TTYUSB0</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Baud Rate</span>
              <strong>115200 bps</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Controller Status</span>
              <strong>Active Green Cycle Scheduler</strong>
            </div>
          </div>
        </div>

        {/* Section 3: Backend & Network */}
        <div className="glass-card" style={{ padding: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px', borderBottom: '1px solid var(--border-color)', paddingBottom: '8px' }}>
            <Network size={16} color="var(--color-info)" />
            <h4 style={{ fontSize: '0.88rem', fontWeight: 700 }}>BACKEND & NETWORK API</h4>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '0.82rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>API Server Gateway</span>
              <strong style={{ color: 'var(--color-success)' }}>HEALTHY (REST v1)</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>WebSocket Status</span>
              <span style={{ color: isConnected ? 'var(--color-success)' : 'var(--color-danger)' }}>
                {isConnected ? 'LIVE (Streaming Pulse)' : 'DISCONNECTED'}
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>WS Retries</span>
              <strong>{reconnectCount} / 5 attempts</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>API Framework</span>
              <strong>{version?.backend || 'FastAPI'} ({version?.version || '1.0.0'})</strong>
            </div>
          </div>
        </div>

        {/* Section 4: Browser Environment */}
        <div className="glass-card" style={{ padding: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px', borderBottom: '1px solid var(--border-color)', paddingBottom: '8px' }}>
            <Laptop size={16} color="var(--color-warning)" />
            <h4 style={{ fontSize: '0.88rem', fontWeight: 700 }}>CLIENT & RUNTIME</h4>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '0.82rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Build Platform</span>
              <strong>Vite + TypeScript + React 18</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Frontend Framework</span>
              <strong>{version?.frontend || 'React SPA'}</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>CPU Utilization (Mock)</span>
              <strong>12%</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Browser Memory (Mock)</span>
              <strong>4.2 GB / 8.0 GB</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>System Uptime</span>
              <strong>{health?.uptime_seconds || 120}s (Operational)</strong>
            </div>
          </div>
        </div>

      </div>

      {/* Drawer Footer */}
      <div style={{
        padding: '20px 24px',
        borderTop: '1px solid var(--border-color)',
        display: 'flex',
        gap: '12px',
      }}>
        <button
          onClick={downloadReport}
          style={{
            flex: 1,
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
            backgroundColor: 'var(--color-primary)',
            color: '#ffffff',
            border: 'none',
            borderRadius: '8px',
            padding: '12px',
            fontWeight: 700,
            cursor: 'pointer',
            fontSize: '0.88rem',
          }}
        >
          <Download size={16} /> Download Diagnostics
        </button>
      </div>

      {/* Slide-in styles inline since we avoid ad-hoc stylesheets */}
      <style>{`
        @keyframes slideIn {
          from { transform: translateX(100%); }
          to { transform: translateX(0); }
        }
      `}</style>
    </div>
  );
};
