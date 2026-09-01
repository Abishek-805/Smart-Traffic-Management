/**
 * LeftControlPanel Component (SCADA Sidebar Panel)
 * Width: 280-320px fixed width panel containing:
 * 1. Live Cameras Status List
 * 2. Inline QR Pairing
 * 3. Connected Nodes
 * 4. AI Status Card
 * 5. Collapsible Digital Twin
 */

import React, { useState } from 'react';
import { Video, Cpu, Server, ChevronDown, ChevronRight, Layers, Radio, Activity } from 'lucide-react';
import { DIRECTIONS, DIRECTION_LABELS, DirectionType } from '../../../constants/directions';
import { InlineQRPairing } from '../../../features/devices/InlineQRPairing';
import { SpatialIntersectionSchematic } from './SpatialIntersectionSchematic';
import { DashboardViewModel } from '../../../features/dashboard/useDashboardViewModel';
import { useMobileNodes } from '../../../shared/hooks/useSystemQueries';

interface LeftControlPanelProps {
  vm: DashboardViewModel;
  selectedDirection: DirectionType;
  setSelectedDirection: (dir: DirectionType) => void;
}

export const LeftControlPanel: React.FC<LeftControlPanelProps> = ({
  vm,
  selectedDirection,
  setSelectedDirection,
}) => {
  const [isDigitalTwinExpanded, setIsDigitalTwinExpanded] = useState<boolean>(false);
  const { data: mobileNodesData } = useMobileNodes();
  const mobileNodes = mobileNodesData?.nodes || [];

  return (
    <div
      style={{
        width: '300px',
        minWidth: '280px',
        maxWidth: '320px',
        display: 'flex',
        flexDirection: 'column',
        gap: '10px',
        height: '100%',
        overflowY: 'auto',
        paddingRight: '4px',
        userSelect: 'none',
      }}
    >
      {/* 1. Live Cameras Section */}
      <div className="scada-card" style={{ padding: '10px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Video size={14} color="#58a6ff" />
            <span style={{ fontSize: '11px', fontWeight: 800, color: 'var(--text-main)', letterSpacing: '0.04em' }}>LIVE CAMERAS</span>
          </div>
          <span className="font-mono-num" style={{ fontSize: '10px', color: '#10b981', fontWeight: 700 }}>
            {vm.statusBar.activeCameraCount}/4 ONLINE
          </span>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
          {DIRECTIONS.map((dir: DirectionType) => {
            const lane = vm.lanes[dir];
            const isOnline = lane.isConfigured;
            const isSelected = selectedDirection === dir;

            return (
              <div
                key={dir}
                onClick={() => setSelectedDirection(dir)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    setSelectedDirection(dir);
                  }
                }}
                role="button"
                tabIndex={0}
                aria-selected={isSelected}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  backgroundColor: isSelected ? 'var(--bg-secondary)' : 'var(--bg-primary)',
                  border: `1px solid ${isSelected ? '#58a6ff' : lane.isGreen ? '#10b981' : 'var(--border-color)'}`,
                  borderRadius: '3px',
                  padding: '4px 8px',
                  fontSize: '11px',
                  cursor: 'pointer',
                  boxShadow: isSelected ? '0 0 4px rgba(88, 166, 255, 0.3)' : 'none',
                  outline: 'none',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: lane.isGreen ? '#10b981' : isOnline ? '#58a6ff' : '#484f58' }} />
                  <span style={{ fontWeight: 700, color: isSelected ? 'var(--text-main)' : '#c9d1d9' }}>{DIRECTION_LABELS[dir]}</span>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }} className="font-mono-num">
                  <span style={{ fontSize: '10px', color: isOnline ? '#10b981' : '#484f58', fontWeight: 700 }}>
                    {isOnline ? 'ONLINE' : 'OFFLINE'}
                  </span>
                  <span style={{ fontSize: '9px', color: '#bc8cff', backgroundColor: 'var(--bg-secondary)', padding: '1px 4px', borderRadius: '2px', border: '1px solid #30363d' }}>
                    {vm.statusBar.fps > 0 ? `${vm.statusBar.fps.toFixed(0)} FPS` : '0 FPS'}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 2. AI Status Card (Moved near the top) */}
      <div className="scada-card" style={{ padding: '10px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '6px' }}>
          <Cpu size={14} color="#bc8cff" />
          <span style={{ fontSize: '11px', fontWeight: 800, color: 'var(--text-main)', letterSpacing: '0.04em' }}>AI PIPELINE STATUS</span>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', fontSize: '10px' }} className="font-mono-num">
          <div style={{ display: 'flex', justifyContent: 'space-between', backgroundColor: 'var(--bg-primary)', padding: '4px 6px', borderRadius: '3px', border: '1px solid #30363d' }}>
            <span style={{ color: '#bc8cff', fontWeight: 700 }}>DETECTOR</span>
            <span style={{ color: '#10b981' }}>{vm.statusBar.aiHealthy ? `Loaded | ${vm.metrics.inferenceTimeMs}ms` : 'Inactive'}</span>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', backgroundColor: 'var(--bg-primary)', padding: '4px 6px', borderRadius: '3px', border: '1px solid #30363d' }}>
            <span style={{ color: '#58a6ff', fontWeight: 700 }}>ByteTrack</span>
            <span style={{ color: '#10b981' }}>Running | {vm.metrics.totalVehicles} Objects</span>
          </div>
        </div>
      </div>

      {/* 3. QR Pairing (Inline Card - Selected camera automatically updates it) */}
      <InlineQRPairing
        selectedDirection={selectedDirection}
        setSelectedDirection={setSelectedDirection}
      />

      {/* 4. Connected Nodes Section (Cleaned up, no fake metrics) */}
      <div className="scada-card" style={{ padding: '10px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Server size={14} color="#58a6ff" />
            <span style={{ fontSize: '11px', fontWeight: 800, color: 'var(--text-main)', letterSpacing: '0.04em' }}>CONNECTED NODES</span>
          </div>
          <span className="font-mono-num" style={{ fontSize: '10px', color: '#10b981' }}>
            {mobileNodes.filter(n => n.status === 'CONNECTED').length} ACTIVE
          </span>
        </div>

        {mobileNodes.length > 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {mobileNodes.map((node) => {
              const isConnected = node.status === 'CONNECTED';
              return (
                <div key={node.node_id} style={{ backgroundColor: 'var(--bg-primary)', padding: '6px 8px', borderRadius: '3px', border: `1px solid ${isConnected ? 'var(--border-color)' : '#22272e'}`, fontSize: '10px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px', fontWeight: 700, color: '#c9d1d9' }}>
                    <span>{node.assigned_lane?.split(' ')[0] || 'Unassigned'} Slot</span>
                    <span style={{ color: isConnected ? '#10b981' : '#f59e0b' }}>
                      {isConnected ? 'CONNECTED' : 'Waiting...'}
                    </span>
                  </div>
                  {isConnected ? (
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '4px', color: 'var(--text-muted)', marginTop: '2px' }} className="font-mono-num">
                      <div>Device: <span style={{ color: 'var(--text-main)', fontWeight: 600 }}>{node.name.split(' (')[0]}</span></div>
                      <div>Battery: <span style={{ color: '#10b981' }}>{node.battery_pct}%</span></div>
                      <div>FPS: <span style={{ color: '#bc8cff' }}>{node.fps.toFixed(0)}</span></div>
                      <div>Signal: <span style={{ color: '#10b981' }}>{node.signal_dbm} dBm</span></div>
                    </div>
                  ) : (
                    <div style={{ color: 'var(--text-muted)', fontSize: '9px', fontStyle: 'italic', marginTop: '2px' }}>
                      Scan QR Code to pair device
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        ) : (
          <div style={{ backgroundColor: 'var(--bg-primary)', padding: '8px', borderRadius: '3px', border: '1px solid #30363d', fontSize: '10px', color: 'var(--text-muted)', textAlign: 'center' }}>
            No mobile camera slots configured
          </div>
        )}
      </div>

      {/* 5. Collapsible Digital Twin */}
      <div className="scada-card" style={{ padding: '10px' }}>
        <button
          onClick={() => setIsDigitalTwinExpanded(!isDigitalTwinExpanded)}
          style={{
            width: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            background: 'none',
            border: 'none',
            color: 'inherit',
            cursor: 'pointer',
            padding: 0,
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Layers size={14} color="#f59e0b" />
            <span style={{ fontSize: '11px', fontWeight: 800, color: 'var(--text-main)', letterSpacing: '0.04em' }}>DIGITAL TWIN</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px', color: 'var(--text-muted)', fontSize: '10px' }}>
            <span>{isDigitalTwinExpanded ? 'Hide' : 'Expand'}</span>
            {isDigitalTwinExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
          </div>
        </button>

        {isDigitalTwinExpanded && (
          <div style={{ marginTop: '8px', paddingTop: '8px', borderTop: '1px solid #30363d' }}>
            <SpatialIntersectionSchematic
              activePhase={vm.activePhase.activeDirection}
              remainingTime={vm.activePhase.remainingSeconds}
              lanes={vm.lanes}
            />
          </div>
        )}
      </div>
    </div>
  );
};
