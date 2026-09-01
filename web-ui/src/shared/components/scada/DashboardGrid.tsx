/**
 * DashboardGrid Component (2×2 Equal-Sized Camera Grid)
 * Contract Section: Camera Grid
 * Equal-sized square camera cards for North, South, East, West.
 */

import React from 'react';
import { DashboardViewModel } from '../../../features/dashboard/useDashboardViewModel';
import { LaneCard } from './LaneCard';

interface DashboardGridProps {
  vm: DashboardViewModel;
  onSelectLane?: (direction: string) => void;
  selectedDirection?: string;
}

export const DashboardGrid: React.FC<DashboardGridProps> = ({ vm, onSelectLane, selectedDirection }) => {
  const isEmergency = vm.statusBar.operatingMode === 'EMERGENCY_OVERRIDE';

  return (
    <div className="camera-grid dashboard-camera-grid"
      style={{
        flex: 1,
        display: 'grid',
        gridTemplateColumns: 'repeat(2, 1fr)',
        gridAutoRows: 'minmax(440px, 1fr)',
        gap: '10px',
        height: '100%',
        width: '100%',
        minHeight: 0,
        minWidth: 0,
      }}
    >
      {/* North Camera Card */}
      <LaneCard
        lane={vm.lanes.north}
        remainingSeconds={vm.activePhase.remainingSeconds}
        isEmergencyMode={isEmergency}
        onSelect={() => onSelectLane?.('north')}
        isSelected={selectedDirection === 'north'}
      />

      {/* South Camera Card */}
      <LaneCard
        lane={vm.lanes.south}
        remainingSeconds={vm.activePhase.remainingSeconds}
        isEmergencyMode={isEmergency}
        onSelect={() => onSelectLane?.('south')}
        isSelected={selectedDirection === 'south'}
      />

      {/* East Camera Card */}
      <LaneCard
        lane={vm.lanes.east}
        remainingSeconds={vm.activePhase.remainingSeconds}
        isEmergencyMode={isEmergency}
        onSelect={() => onSelectLane?.('east')}
        isSelected={selectedDirection === 'east'}
      />

      {/* West Camera Card */}
      <LaneCard
        lane={vm.lanes.west}
        remainingSeconds={vm.activePhase.remainingSeconds}
        isEmergencyMode={isEmergency}
        onSelect={() => onSelectLane?.('west')}
        isSelected={selectedDirection === 'west'}
      />
    </div>
  );
};
