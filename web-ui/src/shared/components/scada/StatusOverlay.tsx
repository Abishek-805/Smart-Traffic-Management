/**
 * SCADA StatusOverlay Component
 * Reusable presentational overlay player for camera streams & hardware status states.
 * Renders CONNECTING, LIVE, STALE, OFFLINE, RECONNECTING treatments.
 */

import React from 'react';
import { Camera, RefreshCw, AlertTriangle, WifiOff } from 'lucide-react';

export type StreamStatusType = 'CONNECTING' | 'LIVE' | 'STALE' | 'OFFLINE' | 'RECONNECTING' | 'DISCONNECTED';

interface StatusOverlayProps {
  status: StreamStatusType;
  title?: string;
  message?: string;
}

export const StatusOverlay: React.FC<StatusOverlayProps> = ({ status, title, message }) => {
  if (status === 'LIVE') return null;

  let bg = 'rgba(7, 11, 20, 0.85)';
  let icon = <Camera size={24} color="#64748b" />;
  let defaultTitle = 'Camera Offline';
  let defaultMsg = 'No active stream feed';
  let accentColor = '#64748b';

  if (status === 'CONNECTING') {
    icon = <RefreshCw size={24} color="#3b82f6" className="spin" />;
    defaultTitle = 'Connecting Stream';
    defaultMsg = 'Establishing video socket link...';
    accentColor = '#3b82f6';
  } else if (status === 'RECONNECTING') {
    icon = <RefreshCw size={24} color="#f59e0b" className="spin" />;
    defaultTitle = 'Reconnecting';
    defaultMsg = 'Retrying video stream link...';
    accentColor = '#f59e0b';
  } else if (status === 'STALE') {
    icon = <AlertTriangle size={24} color="#f59e0b" />;
    defaultTitle = 'Stream Stale';
    defaultMsg = 'Telemetry frame updates delayed';
    accentColor = '#f59e0b';
  } else if (status === 'DISCONNECTED') {
    icon = <WifiOff size={24} color="#ef4444" />;
    defaultTitle = 'DISCONNECTED';
    defaultMsg = 'Telemetry gateway unreachable';
    accentColor = '#ef4444';
  } else if (status === 'OFFLINE') {
    icon = <WifiOff size={24} color="#64748b" />;
    defaultTitle = 'OFFLINE';
    defaultMsg = 'No camera connected';
    accentColor = '#64748b';
  }

  return (
    <div
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        backgroundColor: bg,
        backdropFilter: 'blur(4px)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 15,
        padding: '12px',
        textAlign: 'center',
      }}
    >
      <div style={{ marginBottom: '8px' }}>{icon}</div>
      <span style={{ fontSize: '0.82rem', fontWeight: 800, color: accentColor, marginBottom: '2px' }}>
        {title || defaultTitle}
      </span>
      <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
        {message || defaultMsg}
      </span>
    </div>
  );
};
