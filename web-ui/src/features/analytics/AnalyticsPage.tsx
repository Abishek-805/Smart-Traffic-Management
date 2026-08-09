/**
 * AnalyticsPage (Analytics Feature Module) — v3.1 thin composition
 * Delegates chart rendering to ChartGrid. Owns data fetching and KPI strip.
 */

import React from 'react';
import { useAnalytics } from '../../shared/hooks/useSystemQueries';
import { useTelemetry } from '../../contexts/TelemetryContext';
import { MetricChip } from '../../shared/components/scada/MetricChip';
import { ChartGrid } from './ChartGrid';

export const AnalyticsPage: React.FC = () => {
  const { data } = useAnalytics();
  const { telemetry } = useTelemetry();

  const summary = data || {
    total_vehicles_today: 0,
    avg_wait_time_sec: 0.0,
    peak_pce_score: 0.0,
    efficiency_score: 0.0,
    hourly_flow: [],
    queue_trends: [],
    vehicle_split: [],
    phase_efficiency: [],
  };

  const liveQueue = telemetry?.queueLength !== undefined ? `${telemetry.queueLength.toFixed(1)} veh` : 'Unavailable';
  const liveThroughput = 'Unavailable';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Page Header */}
      <div className="scada-card" style={{ padding: '20px' }}>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 800, marginBottom: '4px' }}>
          Historical Intelligence &amp; Operational Analytics
        </h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.82rem' }}>
          Longitudinal analysis reports and traffic pattern trends ("What happened today?").
        </p>
      </div>

      {/* Live KPI Strip */}
      <div
        className="scada-card"
        style={{
          padding: '16px 20px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '12px',
        }}
      >
        <MetricChip icon="🚗" value={`${summary.total_vehicles_today} Vehicles`} label="Vehicles Today" highlight aria-label={`${summary.total_vehicles_today} vehicles today`} />
        <MetricChip icon="⏱" value={`${summary.avg_wait_time_sec}s Delay`} label="Average Delay" aria-label={`Average delay ${summary.avg_wait_time_sec} seconds`} />
        <MetricChip icon="⭐" value={`${summary.peak_pce_score} Peak PCE`} label="Peak Hour PCE Score" aria-label={`Peak PCE score ${summary.peak_pce_score}`} />
        <MetricChip icon="⚡" value={liveThroughput} label="Current Throughput (Backend does not currently expose throughput)" aria-label="Current Throughput: Unavailable" />
        <MetricChip icon="⏳" value={liveQueue} label="Current Queue" aria-label={`Current queue ${liveQueue}`} />
        <MetricChip icon="📈" value={`${summary.efficiency_score}% Efficiency`} label="Overall Traffic Efficiency" color="#10b981" aria-label={`Traffic efficiency ${summary.efficiency_score} percent`} />
      </div>

      {/* Chart Grid — primary + advanced accordion */}
      <ChartGrid data={summary} />
    </div>
  );
};

export default AnalyticsPage;
