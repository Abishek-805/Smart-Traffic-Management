/**
 * LaneCard Component (SCADA Camera Card)
 * Contract Specifications:
 * Top: [ Direction ] [ LIVE ] [ 30 FPS ] [ Remaining Countdown (18s) ]
 * Center: Live Camera Feed with YOLO Bounding Boxes & Track IDs
 * Bottom Strip: Vehicles | Avg Wait | Queue | PCE | Latency
 * Border Colors: Green (#10b981), Yellow (#f59e0b), Red (#ef4444), Emergency Pulse
 */

import React from 'react';
import { LaneViewModel } from '../../../features/dashboard/useDashboardViewModel';
import { LiveCameraPreview } from './LiveCameraPreview';
import { Shield, AlertTriangle } from 'lucide-react';

interface LaneCardProps {
  lane: LaneViewModel;
  remainingSeconds?: number;
  isEmergencyMode?: boolean;
  onSelect?: () => void;
  isSelected?: boolean;
}

const MetricCard: React.FC<{ label: string; value: React.ReactNode; color?: string }> = ({ label, value, color = 'var(--text-main)' }) => (
  <div style={{
    backgroundColor: 'var(--bg-primary)',
    border: '1px solid #30363d',
    borderRadius: '4px',
    padding: '8px 10px',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    minWidth: 0,
    flex: 1,
  }}>
    <span style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '2px' }}>{label}</span>
    <strong style={{ fontSize: '28px', color: color, fontWeight: 900, lineHeight: '1' }} className="font-mono-num">{value}</strong>
  </div>
);

export const LaneCard: React.FC<LaneCardProps> = ({
  lane,
  remainingSeconds = 0,
  isEmergencyMode = false,
  onSelect,
  isSelected = false,
}) => {
  // Determine signal border class per contract
  let borderClass = 'signal-border-red';

  if (!lane.isConfigured || lane.streamStatus === 'OFFLINE') {
    borderClass = 'signal-border-offline';
  } else if (lane.isGreen) {
    borderClass = 'signal-border-green';
  }

  if (isEmergencyMode) {
    borderClass = 'emergency-pulse-card';
  }

  const getStatusBadge = () => {
    if (!lane.isConfigured) {
      return { text: '🔴 OFFLINE', color: '#ef4444' };
    }
    switch (lane.streamStatus) {
      case 'LIVE':
        return { text: '🟢 LIVE', color: '#10b981' };
      case 'CONNECTING':
        return { text: '🟡 CONNECTING', color: '#f59e0b' };
      case 'STALE':
      case 'DISCONNECTED':
        return { text: '🟣 PAUSED', color: '#bc8cff' };
      case 'RECONNECTING':
      default:
        return { text: '🟠 RECOVERING', color: '#ffab00' };
    }
  };

  const status = getStatusBadge();

  return (
    <div
      role="button"
      tabIndex={0}
      aria-label={`${lane.label} camera card`}
      aria-selected={isSelected}
      className={`scada-card ${borderClass}`}
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        width: '100%',
        padding: '8px',
        backgroundColor: 'var(--bg-secondary)',
        position: 'relative',
        overflow: 'hidden',
        boxSizing: 'border-box',
        boxShadow: isSelected ? '0 0 0 2px var(--border-highlight), 0 0 12px rgba(88, 166, 255, 0.3)' : 'none',
        outline: 'none',
        cursor: 'pointer',
      }}
      onClick={onSelect}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onSelect?.();
        }
      }}
    >
      {/* Top Header Bar */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '6px',
          paddingBottom: '4px',
          borderBottom: '1px solid #30363d',
          fontSize: '11px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <h3 style={{ fontSize: '0.9rem', fontWeight: 800, color: 'var(--text-main)', letterSpacing: '0.02em', margin: 0 }}>
            {lane.label} Camera
          </h3>
          <span
            style={{
              fontSize: '12px',
              fontWeight: 800,
              color: status.color,
              backgroundColor: 'rgba(0,0,0,0.2)',
              padding: '2px 6px',
              borderRadius: '4px',
              border: `1px solid ${status.color}40`,
            }}
          >
            {status.text}
          </span>
        </div>

        {/* Top-Right Remaining Green Countdown Display */}
        <div
          className="font-mono-num"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
            backgroundColor: lane.isGreen ? 'rgba(16, 185, 129, 0.2)' : 'var(--bg-primary)',
            color: lane.isGreen ? '#10b981' : '#58a6ff',
            border: `1px solid ${lane.isGreen ? '#10b981' : 'var(--border-color)'}`,
            padding: '2px 8px',
            borderRadius: '3px',
            fontSize: '13px',
            fontWeight: 900,
          }}
        >
          {lane.isGreen ? `${remainingSeconds}s` : 'WAIT'}
        </div>
      </div>

      {/* Center: Live Camera Feed & Bounding Boxes */}
      <div style={{ flex: 1, minHeight: '0', position: 'relative', marginBottom: '6px' }}>
        <LiveCameraPreview
          streamUrl={lane.streamUrl}
          streamStatus={lane.streamStatus}
          directionLabel={lane.direction}
          fps={lane.isConfigured ? lane.fps : 0.0}
          latencyMs={lane.latencyMs}
          frameAgeMs={lane.frameAgeMs}
          vehicleCount={lane.vehicleCount}
        />

        {/* Emergency Banner Overlay */}
        {isEmergencyMode && (
          <div
            style={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              backgroundColor: 'rgba(239, 68, 68, 0.95)',
              color: 'var(--text-main)',
              padding: '6px 14px',
              borderRadius: '4px',
              fontWeight: 900,
              fontSize: '12px',
              letterSpacing: '0.05em',
              zIndex: 30,
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              boxShadow: '0 0 20px rgba(0,0,0,0.8)',
            }}
          >
            <AlertTriangle size={16} /> 🚨 EMERGENCY PRIORITY
          </div>
        )}
      </div>

      {/* Current-frame measurements; missing inputs are explicitly unavailable. */}
      <div className="lane-metrics"
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(4, 1fr)',
          gridTemplateRows: 'repeat(2, 1fr)',
          gap: '6px',
        }}
      >
        <MetricCard label="Vehicles" value={lane.streamStatus === 'LIVE' ? lane.vehicleCount : '—'} color="var(--text-main)" />
        <MetricCard label="Queue (veh)" value={lane.streamStatus === 'LIVE' ? lane.queueLengthMeters.replace(' veh', '') : '—'} color="#f59e0b" />
        <MetricCard label="PCE" value={lane.streamStatus === 'LIVE' ? lane.pceScore : '—'} color="#10b981" />
        <MetricCard label="Max wait" value={lane.streamStatus === 'LIVE' ? lane.waitTimeSeconds + 's' : '—'} color="#58a6ff" />
        <MetricCard label="Priority" value={lane.streamStatus === 'LIVE' ? lane.priorityScore : '—'} color="#ef4444" />
        <MetricCard label="FPS" value={lane.streamStatus === 'LIVE' ? lane.fps.toFixed(1) : '—'} color="#bc8cff" />
        <MetricCard label="Frame age" value={lane.streamStatus === 'LIVE' ? (lane.frameAgeMs / 1000).toFixed(1) + 's' : '—'} color="#10b981" />
        <MetricCard label="Inference" value={lane.streamStatus === 'LIVE' ? Math.round(lane.inferenceTimeMs) + 'ms' : '—'} color="#bc8cff" />
        <MetricCard label="Server total" value={lane.streamStatus === 'LIVE' ? Math.round(lane.serverProcessingMs) + 'ms' : '—'} color="#58a6ff" />
        <MetricCard label="Server queue" value={lane.streamStatus === 'LIVE' ? Math.round(lane.queueWaitMs) + 'ms' : '—'} color="#f59e0b" />
      </div>
    </div>
  );
};
