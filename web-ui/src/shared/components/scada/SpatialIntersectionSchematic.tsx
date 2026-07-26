/**
 * SCADA SpatialIntersectionSchematic Component (220px Center Node)
 * Central spatial vector graphic showing real-time signal state of the 4 approaches
 * (North ▲, East ►, South ▼, West ◄) with active signal light colors, glowing pulse,
 * and countdown ring.
 */

import React from 'react';
import { DirectionType } from '../../../constants/directions';

interface SpatialIntersectionSchematicProps {
  activePhase: string;
  remainingTime: number;
}

export const SpatialIntersectionSchematic: React.FC<SpatialIntersectionSchematicProps> = ({
  activePhase,
  remainingTime,
}) => {
  const activeDir = activePhase.toLowerCase();

  const getSignalColor = (dir: DirectionType) => {
    return activeDir === dir ? '#10b981' : '#f59e0b';
  };

  return (
    <div
      style={{
        gridArea: 'centre',
        width: '220px',
        height: '220px',
        margin: 'auto',
        position: 'relative',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      <svg width="220" height="220" viewBox="0 0 220 220" style={{ overflow: 'visible' }}>
        {/* Outer Circle Ring */}
        <circle cx="110" cy="110" r="100" fill="#0f172a" stroke="rgba(255,255,255,0.08)" strokeWidth="2" />
        
        {/* Intersection Cross Roads */}
        <rect x="90" y="20" width="40" height="180" fill="rgba(255,255,255,0.03)" rx="4" />
        <rect x="20" y="90" width="180" height="40" fill="rgba(255,255,255,0.03)" rx="4" />

        {/* Center Intersection Box */}
        <rect x="85" y="85" width="50" height="50" fill="#070b14" stroke="rgba(255,255,255,0.15)" strokeWidth="1.5" rx="6" />

        {/* North Signal Light & Vector Arrow */}
        <g transform="translate(110, 50)">
          <circle cx="0" cy="0" r="12" fill={getSignalColor('north')} opacity={activeDir === 'north' ? 1 : 0.4} />
          {activeDir === 'north' && <circle cx="0" cy="0" r="16" fill="none" stroke="#10b981" strokeWidth="2" className="pulse-active" />}
          <text x="0" y="4" textAnchor="middle" fill="#ffffff" fontSize="10" fontWeight="800">▲</text>
        </g>

        {/* East Signal Light & Vector Arrow */}
        <g transform="translate(170, 110)">
          <circle cx="0" cy="0" r="12" fill={getSignalColor('east')} opacity={activeDir === 'east' ? 1 : 0.4} />
          {activeDir === 'east' && <circle cx="0" cy="0" r="16" fill="none" stroke="#10b981" strokeWidth="2" className="pulse-active" />}
          <text x="0" y="4" textAnchor="middle" fill="#ffffff" fontSize="10" fontWeight="800">►</text>
        </g>

        {/* South Signal Light & Vector Arrow */}
        <g transform="translate(110, 170)">
          <circle cx="0" cy="0" r="12" fill={getSignalColor('south')} opacity={activeDir === 'south' ? 1 : 0.4} />
          {activeDir === 'south' && <circle cx="0" cy="0" r="16" fill="none" stroke="#10b981" strokeWidth="2" className="pulse-active" />}
          <text x="0" y="4" textAnchor="middle" fill="#ffffff" fontSize="10" fontWeight="800">▼</text>
        </g>

        {/* West Signal Light & Vector Arrow */}
        <g transform="translate(50, 110)">
          <circle cx="0" cy="0" r="12" fill={getSignalColor('west')} opacity={activeDir === 'west' ? 1 : 0.4} />
          {activeDir === 'west' && <circle cx="0" cy="0" r="16" fill="none" stroke="#10b981" strokeWidth="2" className="pulse-active" />}
          <text x="0" y="4" textAnchor="middle" fill="#ffffff" fontSize="10" fontWeight="800">◄</text>
        </g>

        {/* Center Countdown Value */}
        <text x="110" y="108" textAnchor="middle" fill="#ffffff" fontSize="14" fontWeight="800">
          {remainingTime}s
        </text>
        <text x="110" y="122" textAnchor="middle" fill="var(--text-muted)" fontSize="8" fontWeight="700">
          {activePhase.toUpperCase()}
        </text>
      </svg>
    </div>
  );
};
