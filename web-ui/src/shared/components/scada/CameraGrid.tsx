/**
 * SCADA CameraGrid Component
 * 2x2 Video Wall stream grid for Devices Manager page.
 */

import React from 'react';
import { DIRECTIONS, DIRECTION_LABELS, DirectionType } from '../../../constants/directions';
import { cameraApi } from '../../../services/api/camera';
import { LiveCameraPreview } from './LiveCameraPreview';

interface CameraGridProps {
  connectedDirections: string[];
  selectedDirection: string | null;
  onSelectDirection: (dir: string) => void;
}

export const CameraGrid: React.FC<CameraGridProps> = ({
  connectedDirections,
  selectedDirection,
  onSelectDirection,
}) => {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '16px', height: '420px' }}>
      {DIRECTIONS.map((dir: DirectionType) => {
        const isConfigured = connectedDirections.includes(dir);
        const isSelected = selectedDirection === dir;

        return (
          <div
            key={dir}
            className="scada-card"
            style={{
              padding: '12px',
              display: 'flex',
              flexDirection: 'column',
              border: isSelected ? '2px solid var(--color-primary)' : '1px solid var(--border-color)',
              position: 'relative',
              cursor: 'pointer',
            }}
            onClick={() => onSelectDirection(dir)}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
              <span style={{ fontSize: '0.82rem', fontWeight: 800 }}>{DIRECTION_LABELS[dir]}</span>
              <span
                style={{
                  fontSize: '0.7rem',
                  fontWeight: 800,
                  color: isConfigured ? '#10b981' : '#64748b',
                }}
              >
                {isConfigured ? 'LIVE STREAM' : 'UNASSIGNED'}
              </span>
            </div>

            <div style={{ flex: 1, minHeight: '0' }}>
              <LiveCameraPreview
                streamUrl={cameraApi.getPreviewUrl(dir)}
                streamStatus={isConfigured ? 'LIVE' : 'OFFLINE'}
                directionLabel={dir}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
};
