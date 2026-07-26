/**
 * AnalyticsPage (Analytics Feature Module) — v3.1 thin composition
 * Delegates chart rendering to ChartGrid. Owns data fetching and KPI strip.
 */

import React from 'react';
import { useAnalytics } from '../../shared/hooks/useSystemQueries';
import { MetricChip } from '../../shared/components/scada/MetricChip';
import { ChartGrid } from './ChartGrid';

export const AnalyticsPage: React.FC = () => {
  const { data } = useAnalytics();

  const summary = data || {
    total_vehicles_today: 1420,
    avg_wait_time_sec: 18.5,
    peak_pce_score: 4.2,
    efficiency_score: 92.4,
    hourly_flow: [
      { hour: '08:00', north: 120, south: 140, east: 90,  west: 110 },
      { hour: '10:00', north: 200, south: 220, east: 160, west: 180 },
      { hour: '12:00', north: 310, south: 290, east: 240, west: 260 },
      { hour: '14:00', north: 280, south: 300, east: 210, west: 230 },
      { hour: '16:00', north: 420, south: 450, east: 380, west: 400 },
      { hour: '18:00', north: 390, south: 410, east: 350, west: 370 },
    ],
    queue_trends: [
      { time: '12:00', avgQueueLength: 4.2, maxQueueLength: 9.0  },
      { time: '13:00', avgQueueLength: 5.1, maxQueueLength: 11.2 },
      { time: '14:00', avgQueueLength: 3.8, maxQueueLength: 8.1  },
      { time: '15:00', avgQueueLength: 6.4, maxQueueLength: 14.5 },
      { time: '16:00', avgQueueLength: 8.9, maxQueueLength: 18.0 },
    ],
    vehicle_split: [
      { category: 'Car',         count: 980, percentage: 69.0 },
      { category: 'Motorcycle',  count: 240, percentage: 16.9 },
      { category: 'Bus / Heavy', count: 120, percentage: 8.5  },
      { category: 'Emergency',   count: 80,  percentage: 5.6  },
    ],
    phase_efficiency: [
      { phase: 'North', score: 94.0, fairness: 96.0 },
      { phase: 'South', score: 91.0, fairness: 93.0 },
      { phase: 'East',  score: 88.0, fairness: 90.0 },
      { phase: 'West',  score: 89.0, fairness: 92.0 },
    ],
  };

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
        <MetricChip icon="⚡" value="450 veh/hr" label="Current Throughput" aria-label="Current throughput 450 vehicles per hour" />
        <MetricChip icon="⏳" value="4.8m Avg Queue" label="Current Queue" aria-label="Current average queue 4.8 metres" />
        <MetricChip icon="📈" value={`${summary.efficiency_score}% Efficiency`} label="Overall Traffic Efficiency" color="#10b981" aria-label={`Traffic efficiency ${summary.efficiency_score} percent`} />
      </div>

      {/* Chart Grid — primary + advanced accordion */}
      <ChartGrid data={summary} />
    </div>
  );
};

export default AnalyticsPage;
