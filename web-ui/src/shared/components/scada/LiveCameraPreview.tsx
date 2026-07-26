/**
 * SCADA LiveCameraPreview Component
 * Continuous live MJPEG camera stream viewer with StatusOverlay integration.
 */

import React, { useState } from 'react';
import { StatusOverlay, StreamStatusType } from './StatusOverlay';

interface LiveCameraPreviewProps {
  streamUrl: string;
  streamStatus: StreamStatusType;
  directionLabel?: string;
  height?: string;
  onClick?: () => void;
}

export const LiveCameraPreview: React.FC<LiveCameraPreviewProps> = ({
  streamUrl,
  streamStatus,
  directionLabel,
  height = '100%',
  onClick,
}) => {
  const [imgError, setImgError] = useState(false);

  const effectiveStatus: StreamStatusType = imgError ? 'OFFLINE' : streamStatus;

  return (
    <div
      onClick={onClick}
      style={{
        position: 'relative',
        width: '100%',
        height: height,
        backgroundColor: '#000000',
        borderRadius: '6px',
        overflow: 'hidden',
        cursor: onClick ? 'pointer' : 'default',
      }}
    >
      {/* Live Stream Image Feed */}
      {effectiveStatus === 'LIVE' && !imgError && (
        <img
          src={streamUrl}
          alt={`${directionLabel || 'Camera'} feed`}
          onError={() => setImgError(true)}
          style={{ width: '100%', height: '100%', objectFit: 'cover' }}
        />
      )}

      {/* Stream Status Overlay */}
      {effectiveStatus !== 'LIVE' && <StatusOverlay status={effectiveStatus} />}

      {/* Direction Overlay Pill */}
      {directionLabel && (
        <div
          style={{
            position: 'absolute',
            top: '8px',
            left: '8px',
            backgroundColor: 'rgba(0, 0, 0, 0.65)',
            backdropFilter: 'blur(4px)',
            color: '#ffffff',
            padding: '2px 8px',
            borderRadius: '4px',
            fontSize: '0.72rem',
            fontWeight: 800,
            zIndex: 10,
          }}
        >
          {directionLabel.toUpperCase()}
        </div>
      )}
    </div>
  );
};
