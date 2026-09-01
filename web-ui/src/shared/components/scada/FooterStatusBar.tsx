/**
 * FooterStatusBar Component (Compact Single-Line Status Bar)
 * FDS SCADA v2.1.0 Specification
 */

import React, { useState, useEffect } from 'react';
import { Activity, Radio, Cpu, Server, CheckCircle, Clock } from 'lucide-react';
import { StatusBarViewModel, MetricStripViewModel } from '../../../features/dashboard/useDashboardViewModel';

interface FooterStatusBarProps {
  statusBar: StatusBarViewModel;
  metrics: MetricStripViewModel;
}

export const FooterStatusBar: React.FC<FooterStatusBarProps> = ({ statusBar, metrics }) => {
  const [timeStr, setTimeStr] = useState<string>(() => new Date().toLocaleTimeString() + ' local');

  useEffect(() => {
    const timer = setInterval(() => {
      const now = new Date();
      setTimeStr(now.toLocaleTimeString() + ' local');
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <footer
      style={{
        minHeight: '24px',
        flexShrink: 0,
        flexWrap: 'wrap',
        gap: '6px',
        backgroundColor: 'var(--bg-secondary)',
        borderTop: '1px solid #30363d',
        padding: '0 12px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        fontSize: '10px',
        color: 'var(--text-muted)',
        userSelect: 'none',
        zIndex: 80,
      }}
      className="font-mono-num"
    >
      {/* Left Group: FPS | Latency | WS | ESP32 | Scheduler */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <Activity size={10} color="#bc8cff" />
          <span>FPS: <strong style={{ color: '#bc8cff' }}>{statusBar.fps.toFixed(1)}</strong></span>
        </div>

        <span style={{ color: 'var(--border-color)' }}>|</span>

        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <span>LAST PROCESS: <strong style={{ color: '#58a6ff' }}>{statusBar.latencyMs}ms</strong></span>
        </div>

        <span style={{ color: 'var(--border-color)' }}>|</span>

        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <Radio size={10} color={statusBar.backendHealthy ? '#10b981' : '#ef4444'} />
          <span>WS: <strong style={{ color: statusBar.backendHealthy ? '#10b981' : '#ef4444' }}>{statusBar.backendHealthy ? 'CONNECTED' : 'DISCONNECTED'}</strong></span>
        </div>

        <span style={{ color: 'var(--border-color)' }}>|</span>

        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <Server size={10} color={statusBar.esp32Healthy ? '#10b981' : '#06b6d4'} />
          <span>ESP32: <strong style={{ color: statusBar.esp32Healthy ? '#10b981' : '#06b6d4' }}>{statusBar.esp32Healthy ? 'ACTIVE' : 'SIMULATION'}</strong></span>
        </div>

        <span style={{ color: 'var(--border-color)' }}>|</span>

        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <CheckCircle 
            size={10} 
            color={
              statusBar.schedulerStatus === 'RUNNING' 
                ? '#10b981' 
                : statusBar.schedulerStatus === 'PAUSED' || statusBar.schedulerStatus === 'STOPPED'
                ? '#ef4444'
                : 'var(--text-muted)'
            } 
          />
          <span>
            SCHEDULER:{' '}
            <strong 
              style={{ 
                color: 
                  statusBar.schedulerStatus === 'RUNNING' 
                    ? '#10b981' 
                    : statusBar.schedulerStatus === 'PAUSED' || statusBar.schedulerStatus === 'STOPPED'
                    ? '#ef4444'
                    : 'var(--text-muted)'
              }}
            >
              {statusBar.schedulerStatus}
            </strong>
          </span>
        </div>
      </div>

      {/* Right Group: Build | Version | Connection | Clock */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
        <div>BUILD: <span style={{ color: '#c9d1d9' }}>local</span></div>

        <span style={{ color: 'var(--border-color)' }}>|</span>

        <div>VERSION: <span style={{ color: '#58a6ff' }}>2.0.0</span></div>

        <span style={{ color: 'var(--border-color)' }}>|</span>

        <div style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#c9d1d9' }}>
          <Clock size={10} color="#58a6ff" />
          <span>{timeStr}</span>
        </div>
      </div>
    </footer>
  );
};
