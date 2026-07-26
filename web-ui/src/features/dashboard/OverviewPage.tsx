/**
 * OverviewPage (Dashboard Feature Page Controller)
 * Pure composition page that delegates rendering to SCADADashboardLayout.
 * Consumes useDashboardViewModel to maintain strict separation of operational state.
 */

import React from 'react';
import { useDashboardViewModel } from './useDashboardViewModel';
import { SCADADashboardLayout } from '../../shared/components/scada/DashboardLayout';

export const OverviewPage: React.FC = () => {
  const vm = useDashboardViewModel();

  const handleSelectLane = (direction: string) => {
    // Selection state behavior for interaction rules
    console.log(`Lane selected: ${direction}`);
  };

  return <SCADADashboardLayout vm={vm} onSelectLane={handleSelectLane} />;
};

export default OverviewPage;
