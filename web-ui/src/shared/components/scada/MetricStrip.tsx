/**
 * SCADA MetricStrip Component
 * Compact single-row operational bottom metrics bar (56px height).
 */

import React from 'react';
import { MetricStripViewModel } from '../../../features/dashboard/useDashboardViewModel';
import { MetricChip } from './MetricChip';

interface MetricStripProps {
  metrics: MetricStripViewModel;
}

export const MetricStrip: React.FC<MetricStripProps> = ({ metrics }) => {
  return (
    <div
      className="scada-card"
      style={{
        height: '56px',
        padding: '0 20px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'nowrap',
        overflowX: 'auto',
        gap: '12px',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.75rem', fontWeight: 800, color: 'var(--text-muted)' }}>
        <span>GLOBAL INTERSECTION METRICS</span>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        <MetricChip icon="🚗" value={`${metrics.totalVehicles} Vehicles`} label="Total Intersecting Vehicles" highlight />
        <MetricChip icon="⚡" value={`${metrics.avgFps.toFixed(1)} FPS`} label="System Perception Rate" />
        <MetricChip icon="⏱" value={`${metrics.inferenceTimeMs}ms Inference`} label="YOLO Model Inference Time" />
        <MetricChip icon="⏳" value={`${metrics.processingQueueLength} dropped`} label="Frames dropped this session" />
        <MetricChip icon="📡" value={`${metrics.pipelineLatencyMs}ms Latency`} label="Pipeline Latency" />
        <MetricChip icon="🎞" value={`${metrics.frameAgeMs}ms Age`} label="Last Frame Latency" />
        <MetricChip
          icon="🟢"
          value={metrics.connectionHealth}
          label="Telemetry System Connection Health"
          color={metrics.connectionHealth === 'HEALTHY' ? '#10b981' : '#ef4444'}
        />
      </div>
    </div>
  );
};
