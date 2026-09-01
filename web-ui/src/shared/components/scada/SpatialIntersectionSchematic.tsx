/**
 * SCADA Spatial Intersection Schematic & Digital Twin Component
 * FDS Section 71
 * Spatial 2D vector graphic of the 4-way intersection updating live from telemetry
 */

import React from 'react';

interface SpatialIntersectionSchematicProps {
  activePhase: string;
  remainingTime: number;
  lanes?: Record<string, any>;
}

export const SpatialIntersectionSchematic: React.FC<SpatialIntersectionSchematicProps> = ({
  activePhase,
  remainingTime,
  lanes,
}) => {
  const activeDir = (activePhase || 'North').toUpperCase();

  const getSignalColor = (dir: string): string => {
    return activeDir === dir.toUpperCase() ? '#3FB950' : '#E5534B';
  };

  const getVehicleCount = (dir: string): number => {
    if (!lanes) return 4;
    const laneKey = dir.toLowerCase();
    return lanes[laneKey]?.vehicleCount || 4;
  };

  return (
    <div
      className="scada-panel p-2 flex flex-col h-full relative overflow-hidden select-none"
      style={{
        gridArea: 'centre',
        backgroundColor: '#171c22',
        border: '1px solid #2e3640',
        borderRadius: '6px',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <div className="scada-header" style={{ padding: '6px 10px', fontSize: '11px', fontWeight: 600, color: '#b0bac5', borderBottom: '1px solid #2e3640', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#4EA8DE', display: 'inline-block' }} className="pulse-active" />
          DIGITAL TWIN — SPATIAL INTERSECTION MODEL
        </span>
        <span className="font-mono-num" style={{ color: '#A371F7', fontSize: '10px' }}>
          {activeDir} GREEN ({remainingTime}s)
        </span>
      </div>

      <div style={{ flex: 1, backgroundColor: '#0D1014', borderRadius: '4px', border: '1px solid #2E3640', position: 'relative', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '8px', minHeight: '220px' }}>
        <svg viewBox="0 0 400 400" style={{ width: '100%', height: '100%', maxHeight: '340px' }}>
          <defs>
            <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
              <path d="M 20 0 L 0 0 0 20" fill="none" stroke="#171C22" strokeWidth="1" />
            </pattern>
          </defs>

          <rect width="400" height="400" fill="url(#grid)" />

          {/* Road Asphalt Base */}
          <rect x="150" y="0" width="100" height="400" fill="#181E24" />
          <rect x="0" y="150" width="400" height="100" fill="#181E24" />

          {/* Intersection Box */}
          <rect x="150" y="150" width="100" height="100" fill="#20262D" stroke="#2E3640" strokeWidth="2" />

          {/* Center Divider Lines */}
          <line x1="200" y1="0" x2="200" y2="150" stroke="#F2C14E" strokeWidth="2" strokeDasharray="6,4" />
          <line x1="200" y1="250" x2="200" y2="400" stroke="#F2C14E" strokeWidth="2" strokeDasharray="6,4" />
          <line x1="0" y1="200" x2="150" y2="200" stroke="#F2C14E" strokeWidth="2" strokeDasharray="6,4" />
          <line x1="250" y1="200" x2="400" y2="200" stroke="#F2C14E" strokeWidth="2" strokeDasharray="6,4" />

          {/* Pedestrian Crosswalk Markings */}
          <line x1="150" y1="140" x2="250" y2="140" stroke="#ffffff" strokeWidth="6" strokeDasharray="4,4" />
          <line x1="150" y1="260" x2="250" y2="260" stroke="#ffffff" strokeWidth="6" strokeDasharray="4,4" />
          <line x1="140" y1="150" x2="140" y2="250" stroke="#ffffff" strokeWidth="6" strokeDasharray="4,4" />
          <line x1="260" y1="150" x2="260" y2="250" stroke="#ffffff" strokeWidth="6" strokeDasharray="4,4" />

          {/* Labels */}
          <text x="200" y="20" fill="#7E8791" fontSize="11" fontWeight="bold" textAnchor="middle" fontFamily="monospace">NORTH (N)</text>
          <text x="200" y="385" fill="#7E8791" fontSize="11" fontWeight="bold" textAnchor="middle" fontFamily="monospace">SOUTH (S)</text>
          <text x="25" y="205" fill="#7E8791" fontSize="11" fontWeight="bold" textAnchor="middle" fontFamily="monospace">WEST (W)</text>
          <text x="375" y="205" fill="#7E8791" fontSize="11" fontWeight="bold" textAnchor="middle" fontFamily="monospace">EAST (E)</text>

          {/* Vehicles (NORTH) */}
          {Array.from({ length: Math.min(6, getVehicleCount('NORTH')) }).map((_, i) => (
            <rect key={`n-v-${i}`} x="165" y={120 - i * 16} width="14" height="10" rx="2" fill={activeDir === 'NORTH' ? '#3FB950' : '#4EA8DE'} stroke="#0D1014" strokeWidth="1" />
          ))}

          {/* Vehicles (SOUTH) */}
          {Array.from({ length: Math.min(6, getVehicleCount('SOUTH')) }).map((_, i) => (
            <rect key={`s-v-${i}`} x="220" y={270 + i * 16} width="14" height="10" rx="2" fill={activeDir === 'SOUTH' ? '#3FB950' : '#4EA8DE'} stroke="#0D1014" strokeWidth="1" />
          ))}

          {/* Vehicles (EAST) */}
          {Array.from({ length: Math.min(6, getVehicleCount('EAST')) }).map((_, i) => (
            <rect key={`e-v-${i}`} x={270 + i * 16} y="165" width="10" height="14" rx="2" fill={activeDir === 'EAST' ? '#3FB950' : '#4EA8DE'} stroke="#0D1014" strokeWidth="1" />
          ))}

          {/* Vehicles (WEST) */}
          {Array.from({ length: Math.min(6, getVehicleCount('WEST')) }).map((_, i) => (
            <rect key={`w-v-${i}`} x={120 - i * 16} y="220" width="10" height="14" rx="2" fill={activeDir === 'WEST' ? '#3FB950' : '#4EA8DE'} stroke="#0D1014" strokeWidth="1" />
          ))}

          {/* Traffic Lights */}
          <g transform="translate(140, 110)">
            <rect width="12" height="30" rx="3" fill="#101418" stroke="#2E3640" strokeWidth="1" />
            <circle cx="6" cy="6" r="4" fill={getSignalColor('NORTH') === '#E5534B' ? '#E5534B' : '#20262D'} />
            <circle cx="6" cy="24" r="4" fill={getSignalColor('NORTH') === '#3FB950' ? '#3FB950' : '#20262D'} />
          </g>

          <g transform="translate(248, 260)">
            <rect width="12" height="30" rx="3" fill="#101418" stroke="#2E3640" strokeWidth="1" />
            <circle cx="6" cy="6" r="4" fill={getSignalColor('SOUTH') === '#E5534B' ? '#E5534B' : '#20262D'} />
            <circle cx="6" cy="24" r="4" fill={getSignalColor('SOUTH') === '#3FB950' ? '#3FB950' : '#20262D'} />
          </g>

          <g transform="translate(260, 140)">
            <rect width="30" height="12" rx="3" fill="#101418" stroke="#2E3640" strokeWidth="1" />
            <circle cx="6" cy="6" r="4" fill={getSignalColor('EAST') === '#E5534B' ? '#E5534B' : '#20262D'} />
            <circle cx="24" cy="6" r="4" fill={getSignalColor('EAST') === '#3FB950' ? '#3FB950' : '#20262D'} />
          </g>

          <g transform="translate(110, 248)">
            <rect width="30" height="12" rx="3" fill="#101418" stroke="#2E3640" strokeWidth="1" />
            <circle cx="6" cy="6" r="4" fill={getSignalColor('WEST') === '#E5534B' ? '#E5534B' : '#20262D'} />
            <circle cx="24" cy="6" r="4" fill={getSignalColor('WEST') === '#3FB950' ? '#3FB950' : '#20262D'} />
          </g>

          {/* Center Signal Pulse */}
          <circle cx="200" cy="200" r="8" fill={activeDir ? '#3FB950' : '#E5534B'} className="pulse-active" />
        </svg>

        {/* Center Countdown Ring Text Overlay */}
        <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', textAlign: 'center', pointerEvents: 'none' }}>
          <div className="font-mono-num" style={{ fontSize: '18px', fontWeight: 800, color: 'var(--text-main)' }}>
            {remainingTime}s
          </div>
          <div className="font-mono-num" style={{ fontSize: '9px', fontWeight: 700, color: '#3FB950' }}>
            {activeDir}
          </div>
        </div>
      </div>
    </div>
  );
};
