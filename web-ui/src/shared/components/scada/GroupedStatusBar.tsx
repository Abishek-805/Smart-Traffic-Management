/**
 * SCADA GroupedStatusBar Component (72px Height)
 * Top horizontal status strip grouped into 5 distinct operational domains:
 * SYSTEM, AI, COMMUNICATION, TRAFFIC, PERFORMANCE.
 */

import React from 'react';
import { StatusBarViewModel } from '../../../features/dashboard/useDashboardViewModel';
import { HealthIndicator } from './HealthIndicator';
import { Cpu, Activity, Video, Clock, Zap } from 'lucide-react';

interface GroupedStatusBarProps {
  statusBar: StatusBarViewModel;
  activePhaseDirection?: string;
  timeRemaining?: number;
}

export const GroupedStatusBar: React.FC<GroupedStatusBarProps> = ({
  statusBar,
  activePhaseDirection = 'North',
  timeRemaining = 8,
}) => {
  return (
    <div
      className="scada-card"
      style={{
        height: '72px',
        padding: '0 24px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'nowrap',
        overflowX: 'auto',
        gap: '16px',
      }}
    >
      {/* Domain 1: SYSTEM */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.72rem', fontWeight: 800, color: 'var(--text-muted)' }}>
          <Cpu size={14} color="var(--color-primary)" />
          <span>SYSTEM</span>
        </div>
        <HealthIndicator label="Backend" isHealthy={statusBar.backendHealthy} tooltip="FastAPI Backend REST & WebSocket Gateway" />
        <HealthIndicator label="ESP32" isHealthy={statusBar.esp32Healthy} tooltip="Signal Hardware Serial Interface" />
      </div>

      <div style={{ width: '1px', height: '24px', backgroundColor: 'var(--border-color)' }} />

      {/* Domain 2: AI */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.72rem', fontWeight: 800, color: 'var(--text-muted)' }}>
          <Activity size={14} color="#10b981" />
          <span>AI</span>
        </div>
        <HealthIndicator label="YOLO11" isHealthy={statusBar.aiHealthy} tooltip="YOLO11 Object Detector Model" />
        <HealthIndicator label="ByteTrack" isHealthy={statusBar.aiHealthy} tooltip="ByteTrack Multi-Object Tracker" />
      </div>

      <div style={{ width: '1px', height: '24px', backgroundColor: 'var(--border-color)' }} />

      {/* Domain 3: COMMUNICATION */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.72rem', fontWeight: 800, color: 'var(--text-muted)' }}>
          <Video size={14} color="#06b6d4" />
          <span>COMMUNICATION</span>
        </div>
        <span
          style={{
            fontSize: '0.75rem',
            fontWeight: 800,
            padding: '3px 8px',
            borderRadius: '6px',
            backgroundColor: 'rgba(59, 130, 246, 0.12)',
            color: '#3b82f6',
            border: '1px solid rgba(59, 130, 246, 0.3)',
          }}
        >
          {statusBar.activeCameraCount}/{statusBar.totalCameraSlots} Cameras LIVE
        </span>
      </div>

      <div style={{ width: '1px', height: '24px', backgroundColor: 'var(--border-color)' }} />

      {/* Domain 4: TRAFFIC */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.72rem', fontWeight: 800, color: 'var(--text-muted)' }}>
          <Clock size={14} color="#f59e0b" />
          <span>TRAFFIC</span>
        </div>
        <span
          style={{
            fontSize: '0.75rem',
            fontWeight: 800,
            padding: '3px 8px',
            borderRadius: '6px',
            backgroundColor: 'rgba(16, 185, 129, 0.15)',
            color: '#10b981',
            border: '1px solid #10b981',
          }}
        >
          🟢 {activePhaseDirection} {timeRemaining}s
        </span>
        {/* Operating Mode Badge */}
        {(() => {
          const mode = statusBar.operatingMode;
          const modeColor =
            mode === 'EMERGENCY_OVERRIDE' ? '#ef4444'
            : mode === 'MANUAL_OVERRIDE' ? '#f59e0b'
            : '#10b981';
          const modeBg =
            mode === 'EMERGENCY_OVERRIDE' ? 'rgba(239,68,68,0.15)'
            : mode === 'MANUAL_OVERRIDE' ? 'rgba(245,158,11,0.15)'
            : 'rgba(16,185,129,0.1)';
          const modeLabel =
            mode === 'EMERGENCY_OVERRIDE' ? '🚨 EMERGENCY'
            : mode === 'MANUAL_OVERRIDE' ? '✋ MANUAL'
            : '🤖 AUTO';
          return (
            <span
              style={{
                fontSize: '0.72rem',
                fontWeight: 800,
                padding: '3px 8px',
                borderRadius: '6px',
                backgroundColor: modeBg,
                color: modeColor,
                border: `1px solid ${modeColor}`,
                animation: mode === 'EMERGENCY_OVERRIDE' ? 'green-phase-glow 1s infinite' : 'none',
              }}
            >
              {modeLabel}
            </span>
          );
        })()}
      </div>

      <div style={{ width: '1px', height: '24px', backgroundColor: 'var(--border-color)' }} />

      {/* Domain 5: PERFORMANCE */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.72rem', fontWeight: 800, color: 'var(--text-muted)' }}>
          <Zap size={14} color="#a855f7" />
          <span>PERFORMANCE</span>
        </div>
        <span style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-main)' }}>
          {statusBar.fps.toFixed(1)} FPS | {statusBar.latencyMs}ms
        </span>
      </div>

    </div>
  );
};
