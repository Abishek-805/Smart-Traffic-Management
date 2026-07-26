/**
 * SCADA DashboardGrid Component
 * Renders the 2D spatial intersection grid using CSS Grid template areas:
 * "north north north", "west centre east", "south south south".
 */

import React from 'react';
import { DashboardViewModel } from '../../../features/dashboard/useDashboardViewModel';
import { LaneCard } from './LaneCard';
import { SpatialIntersectionSchematic } from './SpatialIntersectionSchematic';
import { FEATURE_FLAGS } from '../../../config/featureFlags';

interface DashboardGridProps {
  vm: DashboardViewModel;
  onSelectLane?: (direction: string) => void;
}

export const DashboardGrid: React.FC<DashboardGridProps> = ({ vm, onSelectLane }) => {
  return (
    <div className="dashboard-grid-container" style={{ flex: 1, minHeight: '0' }}>
      {/* North Approach */}
      <LaneCard
        lane={vm.lanes.north}
        gridArea="north"
        onSelect={() => onSelectLane?.('north')}
      />

      {/* West Approach */}
      <LaneCard
        lane={vm.lanes.west}
        gridArea="west"
        onSelect={() => onSelectLane?.('west')}
      />

      {/* Central Spatial Intersection Schematic — feature-flag gated */}
      {FEATURE_FLAGS.enableIntersectionSchematic ? (
        <SpatialIntersectionSchematic
          activePhase={vm.activePhase.activeDirection}
          remainingTime={vm.activePhase.remainingSeconds}
        />
      ) : (
        <div
          style={{
            gridArea: 'centre',
            width: '220px',
            height: '220px',
            margin: 'auto',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            borderRadius: '50%',
            border: '2px solid rgba(255,255,255,0.08)',
          }}
        >
          <div
            style={{
              width: '16px',
              height: '16px',
              borderRadius: '50%',
              backgroundColor: '#10b981',
            }}
            className="pulse-active"
          />
        </div>
      )}

      {/* East Approach */}
      <LaneCard
        lane={vm.lanes.east}
        gridArea="east"
        onSelect={() => onSelectLane?.('east')}
      />

      {/* South Approach */}
      <LaneCard
        lane={vm.lanes.south}
        gridArea="south"
        onSelect={() => onSelectLane?.('south')}
      />
    </div>
  );
};
