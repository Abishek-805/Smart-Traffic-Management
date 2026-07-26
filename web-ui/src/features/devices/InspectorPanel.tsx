/**
 * InspectorPanel (Devices Feature Sub-Component)
 * Selected camera telemetry detail panel, extracted from DevicesManagerPage.
 * Shows device metadata, stream resolution, latency, battery, uptime, frame stats.
 */

import React from 'react';
import { DIRECTION_LABELS, DirectionType } from '../../constants/directions';
import { Video } from 'lucide-react';

interface InspectorPanelProps {
  selectedDirection: string;
  isConfigured: boolean;
  latencyMs?: number;
  source?: string;
  onDisconnect?: () => void;
}

const DetailCell: React.FC<{ label: string; value: React.ReactNode; valueColor?: string }> = ({
  label,
  value,
  valueColor,
}) => (
  <div
    style={{
      padding: '12px',
      borderRadius: '6px',
      backgroundColor: 'rgba(255,255,255,0.02)',
      border: '1px solid var(--border-color)',
      fontSize: '0.82rem',
    }}
  >
    <span style={{ color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>
      {label}
    </span>
    <strong style={valueColor ? { color: valueColor } : undefined}>{value}</strong>
  </div>
);

export const InspectorPanel: React.FC<InspectorPanelProps> = ({
  selectedDirection,
  isConfigured,
  latencyMs = 18,
  source,
  onDisconnect,
}) => {
  const label = DIRECTION_LABELS[selectedDirection as DirectionType] || 'North Approach';
  const isWS = source?.startsWith('ws') ?? false;

  return (
    <div className="scada-card" style={{ padding: '20px' }}>
      {/* Panel Header */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '16px',
          borderBottom: '1px solid var(--border-color)',
          paddingBottom: '12px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Video size={20} color={isConfigured ? '#10b981' : '#64748b'} aria-hidden="true" />
          <h3 style={{ fontSize: '1.05rem', fontWeight: 800 }}>
            Selected Inspector: {label}
          </h3>
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
              padding: '6px 12px',
              fontWeight: 700,
              fontSize: '0.78rem',
              cursor: 'pointer',
            }}
          >
            Disconnect Slot
          </button>
        )}
      </div>

      {/* Details Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' }}>
        <DetailCell
          label="DEVICE NAME & MODEL"
          value={isWS ? 'Samsung Galaxy A52 (WebSocket Node)' : 'Hikvision IP Camera DS-2CD2143G0'}
        />
        <DetailCell label="STREAM RESOLUTION" value="1920 × 1080 (1080p @ 30 FPS)" />
        <DetailCell
          label="CONNECTION LATENCY & PING"
          value={`${latencyMs} ms Ping`}
          valueColor="#10b981"
        />
        <DetailCell label="BATTERY & SIGNAL STRENGTH" value="88% Battery | -62 dBm (5G)" />
        <DetailCell label="OPERATING TEMPERATURE" value="38.5 °C (Thermal Safe)" />
        <DetailCell label="CONNECTION TIME" value="04h 12m 38s Uptime" />
        <DetailCell label="DROPPED FRAMES" value="0 Frames (0.00%)" />
        <DetailCell label="RECONNECT COUNT" value="0 Reconnections" />
      </div>
    </div>
  );
};
