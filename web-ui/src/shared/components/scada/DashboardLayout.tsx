/**
 * SCADADashboardLayout Component
 * Composes LeftControlPanel and 2×2 DashboardGrid within zero-scroll viewport.
 */

import React from 'react';
import { DashboardViewModel } from '../../../features/dashboard/useDashboardViewModel';
import { LeftControlPanel } from './LeftControlPanel';
import { DashboardGrid } from './DashboardGrid';

import { DirectionType } from '../../../constants/directions';

interface SCADADashboardLayoutProps {
  vm: DashboardViewModel;
  onSelectLane?: (direction: string) => void;
  selectedDirection: DirectionType;
  setSelectedDirection: (dir: DirectionType) => void;
}

export const SCADADashboardLayout: React.FC<SCADADashboardLayoutProps> = ({
  vm,
  onSelectLane,
  selectedDirection,
  setSelectedDirection,
}) => {
  return (
    <div
      style={{
        display: 'flex',
        gap: '10px',
        flex: 1,
        height: '100%',
        width: '100%',
        minHeight: 0,
        minWidth: 0,
        overflow: 'hidden',
      }}
    >
      {/* Fixed Left Control Panel (280-320px) */}
      <LeftControlPanel
        vm={vm}
        selectedDirection={selectedDirection}
        setSelectedDirection={setSelectedDirection}
      />

      {/* 2×2 Camera Grid Area (Primary Focus) */}
      <DashboardGrid vm={vm} onSelectLane={onSelectLane} selectedDirection={selectedDirection} />
    </div>
  );
};
