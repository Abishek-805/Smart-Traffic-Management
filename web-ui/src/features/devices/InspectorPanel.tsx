/**
 * InspectorPanel (Devices Feature Sub-Component)
 * Selected camera telemetry detail panel, extracted from DevicesManagerPage.
 * Shows device metadata, stream resolution, latency, battery, uptime, frame stats.
 */

import React from 'react';
import { DIRECTION_LABELS, DirectionType } from '../../constants/directions';
import { Video, ShieldCheck, Activity, Battery, Wifi, Cpu, Clock, RefreshCw } from 'lucide-react';

interface InspectorPanelProps {
  selectedDirection: string;
  isConfigured: boolean;
  latencyMs?: number;
  source?: string;
  resolution?: string;
  fps?: number;
  batteryPct?: number;
  signalDbm?: number;
  temperatureC?: number;
  uptimeSec?: number;
  droppedFrames?: number;
  reconnectCount?: number;
  onDisconnect?: () => void;
}

const DetailCell: React.FC<{
  label: string;
  value: React.ReactNode;
  icon?: React.ReactNode;
  valueColor?: string;
  badge?: string;
}> = ({ label, value, icon, valueColor, badge }) => (
  <div
    style={{
      padding: '14px',
      borderRadius: '8px',
      backgroundColor: 'var(--bg-primary)',
      border: '1px solid var(--border-color)',
      fontSize: '0.82rem',
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'space-between',
      gap: '6px',
    }}
  >
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
      <span style={{ color: 'var(--text-muted)', fontSize: '0.72rem', fontWeight: 700, letterSpacing: '0.04em' }}>
        {label}
      </span>
      {icon && <span style={{ color: 'var(--text-muted)' }}>{icon}</span>}
    </div>
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '8px', marginTop: '2px' }}>
      <strong style={{ fontSize: '0.88rem', fontWeight: 800, color: valueColor || 'var(--text-main)' }}>
        {value}
      </strong>
      {badge && (
        <span
          style={{
            fontSize: '0.65rem',
            fontWeight: 800,
            color: '#10b981',
            backgroundColor: 'rgba(16, 185, 129, 0.12)',
            padding: '2px 6px',
            borderRadius: '4px',
            border: '1px solid rgba(16, 185, 129, 0.25)',
          }}
        >
          {badge}
        </span>
      )}
    </div>
  </div>
);

export const InspectorPanel: React.FC<InspectorPanelProps> = React.memo(({
  selectedDirection,
  isConfigured,
  latencyMs = 0,
  source,
  resolution,
  fps,
  batteryPct,
  signalDbm,
  temperatureC,
  uptimeSec,
  droppedFrames,
  reconnectCount,
  onDisconnect,
}) => {
  const label = DIRECTION_LABELS[selectedDirection as DirectionType] || 'North Approach';
  const isWS = source?.startsWith('ws') ?? false;

  return (
    <div className="scada-card" style={{ padding: '20px', borderRadius: '8px' }}>
      {/* Panel Header */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '16px',
          borderBottom: '1px solid var(--border-color)',
          paddingBottom: '14px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div
            style={{
              padding: '6px',
              borderRadius: '6px',
              backgroundColor: isConfigured ? 'rgba(16, 185, 129, 0.15)' : 'rgba(100, 116, 139, 0.15)',
              border: isConfigured ? '1px solid rgba(16, 185, 129, 0.3)' : '1px solid var(--border-color)',
            }}
          >
            <Video size={20} color={isConfigured ? '#10b981' : 'var(--text-muted)'} aria-hidden="true" />
          </div>
          <div>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 800, margin: 0, color: 'var(--text-main)' }}>
              Selected Inspector: {label}
            </h3>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              {isConfigured ? 'Active Telemetry & Stream Diagnostics' : 'Slot Offline — Ready for Node Assignment'}
            </span>
          </div>
        </div>

        {isConfigured && onDisconnect && (
          <button
            onClick={onDisconnect}
            aria-label={`Disconnect ${label} camera slot`}
            style={{
              backgroundColor: 'rgba(239, 68, 68, 0.1)',
              color: '#ef4444',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              borderRadius: '6px',
              padding: '6px 14px',
              fontWeight: 700,
              fontSize: '0.78rem',
              cursor: 'pointer',
              transition: 'background-color 0.2s ease',
            }}
          >
            Disconnect Slot
          </button>
        )}
      </div>

      {/* Details Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 160px), 1fr))', gap: '14px' }}>
        <DetailCell
          label="DEVICE NAME & MODEL"
          value={isConfigured ? (isWS ? 'Mobile Node (WebSocket Gateway)' : 'IP Camera Feed') : 'Unavailable'}
          icon={<Cpu size={14} />}
        />
        <DetailCell
          label="STREAM RESOLUTION"
          value={isConfigured && resolution ? `${resolution}${fps ? ` @ ${fps.toFixed(0)} FPS` : ''}` : 'Unavailable'}
          icon={<Activity size={14} />}
          badge={isConfigured ? "LIVE STREAM" : undefined}
        />
        <DetailCell
          label="CONNECTION LATENCY & PING"
          value={isConfigured ? `${latencyMs} ms Ping` : 'Unavailable'}
          icon={<Wifi size={14} />}
          valueColor={isConfigured ? "#10b981" : undefined}
          badge={isConfigured ? "OPTIMAL" : undefined}
        />
        <DetailCell
          label="BATTERY & SIGNAL STRENGTH"
          value={isConfigured && batteryPct !== undefined ? `${batteryPct}% Battery | ${signalDbm ?? -55} dBm` : 'Unavailable'}
          icon={<Battery size={14} />}
        />
        <DetailCell
          label="OPERATING TEMPERATURE"
          value={isConfigured && temperatureC !== undefined ? `${temperatureC} °C` : 'Unavailable'}
          icon={<ShieldCheck size={14} />}
          badge={isConfigured && temperatureC !== undefined ? "THERMAL SAFE" : undefined}
        />
        <DetailCell
          label="CONNECTION TIME"
          value={isConfigured && uptimeSec !== undefined ? `${Math.floor(uptimeSec / 60)}m Uptime` : 'Unavailable'}
          icon={<Clock size={14} />}
        />
        <DetailCell
          label="DROPPED FRAMES"
          value={isConfigured && droppedFrames !== undefined ? `${droppedFrames} Frames` : 'Unavailable'}
          icon={<RefreshCw size={14} />}
          valueColor={isConfigured ? "#10b981" : undefined}
        />
        <DetailCell
          label="RECONNECT COUNT"
          value={isConfigured && reconnectCount !== undefined ? `${reconnectCount} Reconnections` : 'Unavailable'}
          icon={<Activity size={14} />}
        />
      </div>
    </div>
  );
});

InspectorPanel.displayName = 'InspectorPanel';

