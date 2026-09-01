/**
 * SCADA LiveCameraPreview & Telemetry Overlay Component
 * FDS Section 72, 73
 * Continuous live MJPEG camera stream viewer with telemetry overlays:
 * FPS, Latency, Frame Age, AI Status, Recording indicator, Maximize button.
 */

import React, { useEffect, useState } from 'react';
import { StatusOverlay, StreamStatusType } from './StatusOverlay';

interface LiveCameraPreviewProps {
  streamUrl: string;
  streamStatus: StreamStatusType;
  directionLabel?: string;
  height?: string;
  fps?: number;
  latencyMs?: number;
  frameAgeMs?: number;
  vehicleCount?: number;
  onClick?: () => void;
}

export const LiveCameraPreview: React.FC<LiveCameraPreviewProps> = React.memo(({
  streamUrl,
  streamStatus,
  directionLabel,
  height = '100%',
  fps = 0,
  latencyMs = 0,
  frameAgeMs = 0,
  vehicleCount = 0,
  onClick,
}) => {
  const [imgError, setImgError] = useState(false);
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    setImgError(false);
  }, [streamUrl, streamStatus]);
  useEffect(() => {
    if (!imgError || streamStatus !== 'LIVE') return;
    const timer = setTimeout(() => { setImgError(false); setRetry(v => v + 1); }, 2000);
    return () => clearTimeout(timer);
  }, [imgError, streamStatus]);
  const effectiveStatus: StreamStatusType = imgError ? 'OFFLINE' : streamStatus;

  return (
    <div
      onClick={onClick}
      style={{
        position: 'relative',
        width: '100%',
        height: height,
        minHeight: '180px',
        backgroundColor: '#070B14',
        borderRadius: '6px',
        border: '1px solid #2E3640',
        overflow: 'hidden',
        cursor: onClick ? 'pointer' : 'default',
      }}
    >
      {/* Live Stream Image Feed */}
      {effectiveStatus === 'LIVE' && !imgError && (
        <img
          src={streamUrl + (streamUrl.includes('?') ? '&' : '?') + 'attempt=' + retry}
          alt={`${directionLabel || 'Camera'} feed`}
          onError={() => setImgError(true)}
          onLoad={() => setImgError(false)}
          style={{ width: '100%', height: '100%', objectFit: 'contain', display: 'block' }}
        />
      )}

      {/* Stream Status Overlay */}
      {effectiveStatus !== 'LIVE' && <StatusOverlay status={effectiveStatus} />}

      {/* Top-Left Overlay: Direction Tag & Recording Badge */}
      {directionLabel && (
        <div
          style={{
            position: 'absolute',
            top: '8px',
            left: '8px',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            zIndex: 10,
          }}
        >
          <span
            className="font-mono-num"
            style={{
              backgroundColor: 'rgba(13, 17, 23, 0.88)',
              color: '#ffffff',
              padding: '3px 8px',
              borderRadius: '4px',
              fontSize: '10px',
              fontWeight: 800,
              border: '1px solid rgba(255, 255, 255, 0.15)',
              letterSpacing: '0.04em',
              backdropFilter: 'blur(4px)',
            }}
          >
            {directionLabel.toUpperCase()}
          </span>
          <span
            className="font-mono-num"
            style={{
              backgroundColor: 'rgba(13, 17, 23, 0.88)',
              color: '#3FB950',
              padding: '3px 7px',
              borderRadius: '4px',
              fontSize: '9px',
              fontWeight: 700,
              border: '1px solid rgba(63, 185, 80, 0.3)',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              backdropFilter: 'blur(4px)',
            }}
          >
            <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: '#3FB950' }} className="pulse-active" />
            {effectiveStatus === 'LIVE' ? 'LIVE' : 'NO FEED'}
          </span>
        </div>
      )}

      {/* Top-Right Overlay: FPS Readout */}
      <div
        style={{
          position: 'absolute',
          top: '8px',
          right: '8px',
          display: 'flex',
          gap: '6px',
          zIndex: 10,
        }}
      >
        <span
          style={{
            backgroundColor: 'rgba(188, 140, 255, 0.15)',
            color: '#bc8cff',
            padding: '3px 6px',
            borderRadius: '4px',
            fontSize: '9px',
            fontWeight: 800,
            border: '1px solid rgba(188, 140, 255, 0.3)',
            backdropFilter: 'blur(4px)',
          }}
        >
          {effectiveStatus === 'LIVE' ? fps.toFixed(1) : '—'} FPS
        </span>
      </div>

      {/* Bottom Telemetry Overlay Bar */}
      <div
        style={{
          position: 'absolute',
          bottom: 0,
          left: 0,
          right: 0,
          backgroundColor: 'rgba(13, 17, 23, 0.92)',
          borderTop: '1px solid #30363d',
          padding: '4px 8px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          fontSize: '10px',
          zIndex: 10,
          backdropFilter: 'blur(4px)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ color: '#58a6ff', fontWeight: 700 }}>DETECTOR</span>
          <span className="font-mono-num" style={{ color: '#ffffff', fontWeight: 800 }}>
            {effectiveStatus === 'LIVE' ? vehicleCount : '—'} veh
          </span>
        </div>
        <div className="font-mono-num" style={{ color: '#8b949e' }}>
          {effectiveStatus === 'LIVE' ? latencyMs + 'ms | ' + (frameAgeMs / 1000).toFixed(1) + 's age' : 'Awaiting fresh frame'}
        </div>
      </div>
    </div>
  );
});

LiveCameraPreview.displayName = 'LiveCameraPreview';

