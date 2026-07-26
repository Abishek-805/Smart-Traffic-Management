/**
 * SCADA LaneCard Component (60/40 Height Split)
 * Camera-first approach module for North, East, South, West.
 * Top 60% height: LiveCameraPreview + StatusBadge.
 * Bottom 40% height: Compact icon metric chips (🚗, ⏳, ⭐, ⚡, ⏱).
 */

import React from 'react';
import { LaneViewModel } from '../../../features/dashboard/useDashboardViewModel';
import { LiveCameraPreview } from './LiveCameraPreview';
import { StatusBadge } from './StatusBadge';
import { MetricChip } from './MetricChip';

interface LaneCardProps {
  lane: LaneViewModel;
  gridArea?: string;
  onSelect?: () => void;
}

export const LaneCard: React.FC<LaneCardProps> = ({ lane, gridArea, onSelect }) => {
  return (
    <div
      role="region"
      aria-label={`${lane.label} approach camera`}
      className={`scada-card ${lane.isGreen ? 'active-green-card' : ''}`}
      style={{
        gridArea: gridArea,
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        padding: '12px',
        borderLeft: `4px solid ${lane.statusColor}`,
        opacity: lane.isConfigured ? 1 : 0.75,
        cursor: onSelect ? 'pointer' : 'default',
      }}
      onClick={onSelect}
      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onSelect?.(); } }}
      tabIndex={onSelect ? 0 : undefined}
    >
      {/* Header Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
        <h4 style={{ fontSize: '0.92rem', fontWeight: 800 }}>{lane.label}</h4>
        <StatusBadge status={lane.statusLabel} color={lane.statusColor} bg={`${lane.statusColor}20`} />
      </div>

      {/* Top 60% Height: Live Camera Stream */}
      <div style={{ flex: '6 1 0%', minHeight: '130px', marginBottom: '8px' }}>
        <LiveCameraPreview
          streamUrl={lane.streamUrl}
          streamStatus={lane.streamStatus}
          directionLabel={lane.direction}
        />
      </div>

      {/* Bottom 40% Height: Compact Icon Metric Chips */}
      <div style={{ flex: '4 1 0%', display: 'flex', flexWrap: 'wrap', gap: '6px', alignItems: 'center', paddingTop: '4px' }}>
        <MetricChip icon="🚗" value={lane.vehicleCount} label="Vehicle Count" highlight={lane.isGreen} aria-label={`${lane.vehicleCount} vehicles`} />
        <MetricChip icon="⏳" value={lane.queueLengthMeters} label="PCE Queue Length" aria-label={`Queue length ${lane.queueLengthMeters}`} />
        <MetricChip icon="⭐" value={lane.pceScore} label="Priority PCE Score" aria-label={`PCE score ${lane.pceScore}`} />
        <MetricChip icon="⏱" value={`${lane.waitTimeSeconds}s`} label="Approach Wait Time" aria-label={`Wait time ${lane.waitTimeSeconds} seconds`} />
        <MetricChip icon="⚡" value={`${lane.latencyMs}ms`} label="Camera Latency" aria-label={`Camera latency ${lane.latencyMs} milliseconds`} />
      </div>
    </div>
  );
};
