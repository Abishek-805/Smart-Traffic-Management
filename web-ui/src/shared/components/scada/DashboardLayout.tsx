import React from 'react';
import { DashboardViewModel } from '../../../features/dashboard/useDashboardViewModel';
import { DashboardGrid } from './DashboardGrid';
import { DirectionType } from '../../../constants/directions';
import { InlineQRPairing } from '../../../features/devices/InlineQRPairing';
import { QrCode } from 'lucide-react';
interface Props {
  vm: DashboardViewModel;
  onSelectLane?: (direction: string) => void;
  selectedDirection: DirectionType;
  setSelectedDirection: (dir: DirectionType) => void;
}
export const SCADADashboardLayout: React.FC<Props> = ({ vm, onSelectLane, selectedDirection, setSelectedDirection }) => (
  <section style={{ display: 'flex', flexDirection: 'column', gap: 12, minHeight: '100%' }}>
    <div className="phase-bar scada-card" role="status">
      <div><span className="phase-label">Current signal</span><strong>{vm.activePhase.activeDirection === 'None' ? 'Waiting for fresh camera data' : vm.activePhase.activeDirection + ' approach'}</strong></div>
      <div><strong className="font-mono-num">{vm.activePhase.remainingSeconds}s</strong><span className="phase-label">{vm.activePhase.phaseReason}</span></div>
      <div><strong>{vm.statusBar.activeCameraCount} / 4 cameras</strong><span className="phase-label">Hardware simulation · JPEG samples</span></div>
    </div>
    <div className="dashboard-workspace">
      <aside className="pairing-sidebar" aria-label="Connect mobile camera">
        <div className="pairing-sidebar-heading">
          <QrCode size={18} aria-hidden="true" />
          <div>
            <strong>Connect mobile camera</strong>
            <span>Select a direction, generate its QR, then scan it in the native app.</span>
          </div>
        </div>
        <InlineQRPairing selectedDirection={selectedDirection} setSelectedDirection={setSelectedDirection} />
      </aside>
      <DashboardGrid vm={vm} onSelectLane={onSelectLane} selectedDirection={selectedDirection} />
    </div>
  </section>
);
