/**
 * ChartGrid (Analytics Feature Sub-Component)
 * Primary and advanced chart panels extracted from AnalyticsPage.
 * Renders: Volume Trend (LineChart), Queue Trend (AreaChart),
 * and the advanced accordion with Classification (Bar), Split (Pie), Efficiency (Radar).
 */

import React, { useState } from 'react';
import {
  LineChart, Line,
  AreaChart, Area,
  BarChart, Bar,
  PieChart, Pie, Cell,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts';
import { ChevronDown, ChevronUp } from 'lucide-react';

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444'];

const CHART_TOOLTIP_STYLE = {
  contentStyle: {
    backgroundColor: '#0f172a',
    borderColor: 'rgba(255,255,255,0.1)',
    borderRadius: '6px',
  },
};

interface ChartGridProps {
  data: {
    hourly_flow: any[];
    queue_trends: any[];
    vehicle_split: any[];
    phase_efficiency: any[];
  };
}

export const ChartGrid: React.FC<ChartGridProps> = ({ data }) => {
  const [isAdvancedOpen, setIsAdvancedOpen] = useState(true);

  return (
    <>
      {/* Primary Charts Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '20px' }}>
        {/* Volume Trend */}
        <div className="scada-card" style={{ padding: '20px', height: '360px' }}>
          <h3 style={{ fontSize: '0.95rem', fontWeight: 800, marginBottom: '14px' }}>
            Approach Volume Trends
          </h3>
          <ResponsiveContainer width="100%" height="85%">
            <LineChart data={data.hourly_flow}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="hour" stroke="var(--text-muted)" fontSize={11} />
              <YAxis stroke="var(--text-muted)" fontSize={11} />
              <Tooltip {...CHART_TOOLTIP_STYLE} />
              <Legend />
              <Line type="monotone" dataKey="north" stroke="#3b82f6" strokeWidth={2} name="North" />
              <Line type="monotone" dataKey="south" stroke="#10b981" strokeWidth={2} name="South" />
              <Line type="monotone" dataKey="east"  stroke="#f59e0b" strokeWidth={2} name="East" />
              <Line type="monotone" dataKey="west"  stroke="#ef4444" strokeWidth={2} name="West" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Queue Trend */}
        <div className="scada-card" style={{ padding: '20px', height: '360px' }}>
          <h3 style={{ fontSize: '0.95rem', fontWeight: 800, marginBottom: '14px' }}>
            Queue Length Trends
          </h3>
          <ResponsiveContainer width="100%" height="85%">
            <AreaChart data={data.queue_trends}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="time" stroke="var(--text-muted)" fontSize={11} />
              <YAxis stroke="var(--text-muted)" fontSize={11} />
              <Tooltip {...CHART_TOOLTIP_STYLE} />
              <Legend />
              <Area type="monotone" dataKey="avgQueueLength" stroke="#3b82f6" fill="rgba(59,130,246,0.2)" name="Avg Queue (veh)" />
              <Area type="monotone" dataKey="maxQueueLength" stroke="#ef4444" fill="rgba(239,68,68,0.2)" name="Max Queue (veh)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Advanced Visualizer Accordion */}
      <div className="scada-card" style={{ overflow: 'hidden' }}>
        <button
          onClick={() => setIsAdvancedOpen(!isAdvancedOpen)}
          aria-expanded={isAdvancedOpen}
          style={{
            width: '100%',
            backgroundColor: 'transparent',
            border: 'none',
            color: 'var(--text-main)',
            padding: '16px 20px',
            fontSize: '0.95rem',
            fontWeight: 800,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            cursor: 'pointer',
          }}
        >
          <span>PCE Trend, Lane Comparison &amp; Classification Heatmap</span>
          {isAdvancedOpen ? <ChevronUp size={18} aria-hidden="true" /> : <ChevronDown size={18} aria-hidden="true" />}
        </button>

        {isAdvancedOpen && (
          <div
            style={{
              padding: '20px',
              borderTop: '1px solid var(--border-color)',
              display: 'grid',
              gridTemplateColumns: 'repeat(3, 1fr)',
              gap: '20px',
            }}
          >
            {/* Classification BarChart */}
            <div style={{ padding: '12px', borderRadius: '6px', backgroundColor: 'rgba(0,0,0,0.2)', height: '320px' }}>
              <h4 style={{ fontSize: '0.85rem', fontWeight: 800, marginBottom: '12px', color: 'var(--text-muted)' }}>
                Vehicle Classification
              </h4>
              <ResponsiveContainer width="100%" height="85%">
                <BarChart data={data.vehicle_split}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" />
                  <XAxis dataKey="category" stroke="var(--text-muted)" fontSize={10} />
                  <YAxis stroke="var(--text-muted)" fontSize={10} />
                  <Tooltip {...CHART_TOOLTIP_STYLE} />
                  <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Volume Split PieChart */}
            <div style={{ padding: '12px', borderRadius: '6px', backgroundColor: 'rgba(0,0,0,0.2)', height: '320px' }}>
              <h4 style={{ fontSize: '0.85rem', fontWeight: 800, marginBottom: '12px', color: 'var(--text-muted)' }}>
                Volume Split
              </h4>
              <ResponsiveContainer width="100%" height="85%">
                <PieChart>
                  <Pie data={data.vehicle_split} dataKey="count" nameKey="category" cx="50%" cy="50%" outerRadius={70} label>
                    {data.vehicle_split.map((_: any, index: number) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip {...CHART_TOOLTIP_STYLE} />
                </PieChart>
              </ResponsiveContainer>
            </div>

            {/* Phase Efficiency RadarChart */}
            <div style={{ padding: '12px', borderRadius: '6px', backgroundColor: 'rgba(0,0,0,0.2)', height: '320px' }}>
              <h4 style={{ fontSize: '0.85rem', fontWeight: 800, marginBottom: '12px', color: 'var(--text-muted)' }}>
                Phase Efficiency
              </h4>
              <ResponsiveContainer width="100%" height="85%">
                <RadarChart data={data.phase_efficiency}>
                  <PolarGrid stroke="rgba(255,255,255,0.05)" />
                  <PolarAngleAxis dataKey="phase" stroke="var(--text-muted)" fontSize={11} />
                  <PolarRadiusAxis stroke="var(--text-muted)" fontSize={9} />
                  <Radar name="Efficiency Score" dataKey="score" stroke="#10b981" fill="#10b981" fillOpacity={0.4} />
                  <Radar name="Fairness Score" dataKey="fairness" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.4} />
                  <Tooltip {...CHART_TOOLTIP_STYLE} />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}
      </div>
    </>
  );
};
