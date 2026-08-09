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

export const CameraGrid: React.FC<CameraGridProps> = React.memo(({
  connectedDirections,
  selectedDirection,
  onSelectDirection,
}) => {
  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(2, 1fr)',
        gap: '16px',
        minHeight: '520px',
        width: '100%',
      }}
    >
      {DIRECTIONS.map((dir: DirectionType) => {
        const isConfigured = connectedDirections.includes(dir);
        const isSelected = selectedDirection === dir;

        return (
          <div
            key={dir}
            className="scada-card"
            role="button"
            tabIndex={0}
            aria-selected={isSelected}
            style={{
              padding: '12px',
              display: 'flex',
              flexDirection: 'column',
              minHeight: '260px',
              border: isSelected ? '2px solid var(--border-highlight)' : '1px solid var(--border-color)',
              boxShadow: isSelected ? '0 0 12px rgba(88, 166, 255, 0.25)' : 'none',
              position: 'relative',
              cursor: 'pointer',
              borderRadius: '6px',
              transition: 'border-color 0.2s ease, box-shadow 0.2s ease',
              outline: 'none',
            }}
            onClick={() => onSelectDirection(dir)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                onSelectDirection(dir);
              }
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span
                  style={{
                    width: '8px',
                    height: '8px',
                    borderRadius: '50%',
                    backgroundColor: isSelected ? '#58a6ff' : isConfigured ? '#10b981' : '#64748b',
                  }}
                />
                <span style={{ fontSize: '0.85rem', fontWeight: 800, color: '#ffffff' }}>
                  {DIRECTION_LABELS[dir]}
                </span>
              </div>
              <span
                style={{
                  fontSize: '0.7rem',
                  fontWeight: 800,
                  color: isConfigured ? '#10b981' : '#8b949e',
                  backgroundColor: isConfigured ? 'rgba(16, 185, 129, 0.1)' : 'rgba(255, 255, 255, 0.05)',
                  padding: '2px 8px',
                  borderRadius: '4px',
                  border: isConfigured ? '1px solid rgba(16, 185, 129, 0.3)' : '1px solid var(--border-color)',
                }}
              >
                {isConfigured ? 'LIVE STREAM' : 'UNASSIGNED'}
              </span>
            </div>

            <div style={{ flex: 1, minHeight: '200px', display: 'flex', flexDirection: 'column' }}>
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
});

CameraGrid.displayName = 'CameraGrid';

