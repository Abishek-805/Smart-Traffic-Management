/**
 * SCADA OperationalProgressBar Component (48px Height)
 * Dedicated horizontal operational bar for the active green phase:
 * Direction indicator + progress animation bar + remaining countdown seconds.
 */

import React from 'react';
import { PhaseViewModel } from '../../../features/dashboard/useDashboardViewModel';

interface OperationalProgressBarProps {
  phase: PhaseViewModel;
}

export const OperationalProgressBar: React.FC<OperationalProgressBarProps> = ({ phase }) => {
  return (
    <div
      className="scada-card"
      style={{
        height: '48px',
        padding: '0 20px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '20px',
        backgroundColor: 'rgba(16, 185, 129, 0.04)',
        border: '1px solid rgba(16, 185, 129, 0.2)',
      }}
    >
      {/* Active Phase Badge */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', minWidth: '160px' }}>
        <span className="pulse-active" style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: '#10b981', display: 'inline-block' }} />
        <span style={{ fontSize: '0.88rem', fontWeight: 800, color: '#10b981', letterSpacing: '0.04em' }}>
          🟢 {phase.activeDirection.toUpperCase()} APPROACH
        </span>
      </div>

      {/* Countdown Progress Bar Track */}
      <div style={{ flex: 1, height: '8px', backgroundColor: 'rgba(255, 255, 255, 0.08)', borderRadius: '4px', overflow: 'hidden' }}>
        <div
          style={{
            height: '100%',
            width: `${phase.progressPercentage}%`,
            backgroundColor: '#10b981',
            boxShadow: '0 0 10px rgba(16, 185, 129, 0.5)',
            transition: 'width 250ms cubic-bezier(0.16, 1, 0.3, 1)',
          }}
        />
      </div>

      {/* Countdown Text */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', minWidth: '150px', justifyContent: 'flex-end' }}>
        <span style={{ fontSize: '0.88rem', fontWeight: 800, color: '#10b981' }}>
          {phase.remainingSeconds} seconds remaining
        </span>
      </div>
    </div>
  );
};
