/**
 * SCADA DashboardLayout Component (100vh 0-Scroll Viewport Shell)
 * Manages the composition of the 4 operational zones:
 * 1. GroupedStatusBar (72px)
 * 2. OperationalProgressBar (48px)
 * 3. DashboardGrid (Main Flex/Grid Viewport)
 * 4. MetricStrip (56px)
 */

import React from 'react';
import { DashboardViewModel } from '../../../features/dashboard/useDashboardViewModel';
import { GroupedStatusBar } from './GroupedStatusBar';
import { OperationalProgressBar } from './OperationalProgressBar';
import { DashboardGrid } from './DashboardGrid';
import { MetricStrip } from './MetricStrip';

interface SCADADashboardLayoutProps {
  vm: DashboardViewModel;
  onSelectLane?: (direction: string) => void;
}

export const SCADADashboardLayout: React.FC<SCADADashboardLayoutProps> = ({ vm, onSelectLane }) => {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '12px',
        height: 'calc(100vh - 88px)',
        maxHeight: 'calc(100vh - 88px)',
        overflow: 'hidden',
      }}
    >
      {/* Zone 1: Grouped Status Bar (72px) */}
      <GroupedStatusBar
        statusBar={vm.statusBar}
        activePhaseDirection={vm.activePhase.activeDirection}
        timeRemaining={vm.activePhase.remainingSeconds}
      />

      {/* Zone 2: Operational Green Phase Progress Bar (48px) */}
      <OperationalProgressBar phase={vm.activePhase} />

      {/* Zone 3: 2D Spatial Compass Dashboard Grid */}
      <DashboardGrid vm={vm} onSelectLane={onSelectLane} />

      {/* Zone 4: Compact Bottom Metric Strip (56px) */}
      <MetricStrip metrics={vm.metrics} />
    </div>
  );
};
