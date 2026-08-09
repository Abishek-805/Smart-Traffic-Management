import React, { useState } from 'react';
import { useDashboardViewModel } from './useDashboardViewModel';
import { SCADADashboardLayout } from '../../shared/components/scada/DashboardLayout';
import { DirectionType } from '../../constants/directions';

export const OverviewPage: React.FC = () => {
  const vm = useDashboardViewModel();
  const [selectedDirection, setSelectedDirection] = useState<DirectionType>('north');

  const handleSelectLane = (direction: string) => {
    setSelectedDirection(direction as DirectionType);
    console.log(`Lane selected: ${direction}`);
  };

  return (
    <SCADADashboardLayout
      vm={vm}
      onSelectLane={handleSelectLane}
      selectedDirection={selectedDirection}
      setSelectedDirection={setSelectedDirection}
    />
  );
};

export default OverviewPage;
