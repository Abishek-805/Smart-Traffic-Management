/**
 * DevicesManagerPage (Devices Feature Module)
 * Thin composition controller per v3.1 architecture.
 * Delegates rendering to VideoWall + InspectorPanel sub-components.
 */

import React, { useState } from 'react';
import { apiFetch } from '../../services/api/client';
import { VideoWall } from '../devices/VideoWall';
import { InspectorPanel } from '../devices/InspectorPanel';
import { InlineQRPairing } from '../devices/InlineQRPairing';
import { useCameraConfigs, useMobileNodes } from '../../shared/hooks/useSystemQueries';
import { useNotifications } from '../../contexts/NotificationContext';
import { RefreshCw, QrCode, Video, Activity } from 'lucide-react';

export const DevicesManagerPage: React.FC = () => {
  const { data: configData, refetch: refetchCameras } = useCameraConfigs();
  const { refetch: refetchNodes } = useMobileNodes();
  const { addToast } = useNotifications();

  const connectedCams = Object.entries(configData?.streams ?? {}).filter(([, c]) => c.status === 'CONNECTED').map(([d]) => d);
  const [selectedDirection, setSelectedDirection] = useState<string>('north');
  const [showQRPairing, setShowQRPairing] = useState<boolean>(false);

  const handleDisconnect = async () => {
    try {
      await apiFetch('/cameras/' + selectedDirection, { method: 'DELETE' });
      await Promise.all([refetchCameras(), refetchNodes()]);
      addToast('success', 'Camera disconnected', selectedDirection.toUpperCase());
    } catch (error) {
      addToast('error', 'Disconnect failed', error instanceof Error ? error.message : 'Runtime unavailable');
    }
  };

  const selectedInfo = configData?.streams?.[selectedDirection];
  const isConfigured = connectedCams.includes(selectedDirection.toLowerCase());

  const activeCount = connectedCams.length;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', paddingBottom: '48px' }}>
      {/* Header */}
      <div
        className="scada-card page-toolbar"
        style={{
          padding: '18px 24px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          borderRadius: '8px',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px' }}>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-main)', margin: 0 }}>
              Intersection Camera Video Wall
            </h2>
            <span
              style={{
                fontSize: '0.72rem',
                fontWeight: 800,
                color: activeCount > 0 ? '#10b981' : '#ef4444',
                backgroundColor: activeCount > 0 ? 'rgba(16, 185, 129, 0.12)' : 'rgba(239, 68, 68, 0.12)',
                border: activeCount > 0 ? '1px solid rgba(16, 185, 129, 0.3)' : '1px solid rgba(239, 68, 68, 0.3)',
                borderRadius: '4px',
                padding: '2px 8px',
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
              }}
            >
              <Activity size={10} />
              {activeCount}/4 CAMERAS CONNECTED
            </span>
          </div>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.82rem', margin: 0 }}>
            Continuous 2×2 live video wall with telemetry overlays. Select any stream for real-time inspector diagnostics.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <button
            onClick={() => setShowQRPairing(!showQRPairing)}
            aria-label="Toggle QR Pairing Drawer"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              backgroundColor: showQRPairing ? 'rgba(88, 166, 255, 0.15)' : 'rgba(255, 255, 255, 0.05)',
              color: showQRPairing ? '#58a6ff' : 'var(--text-main)',
              border: showQRPairing ? '1px solid #58a6ff' : '1px solid var(--border-color)',
              borderRadius: '8px',
              padding: '8px 14px',
              fontWeight: 700,
              cursor: 'pointer',
              fontSize: '0.8rem',
              transition: 'all 0.2s ease',
            }}
          >
            <QrCode size={14} aria-hidden="true" />
            {showQRPairing ? 'Hide QR Pairing' : 'Pair Camera Node'}
          </button>

          <button
            onClick={() => { refetchCameras(); refetchNodes(); addToast('info', 'Hardware Status', 'Refreshed camera configs & mobile node telemetry.'); }}
            aria-label="Refresh hardware status"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              backgroundColor: 'rgba(255, 255, 255, 0.05)',
              color: 'var(--text-main)',
              border: '1px solid var(--border-color)',
              borderRadius: '8px',
              padding: '8px 14px',
              fontWeight: 700,
              cursor: 'pointer',
              fontSize: '0.8rem',
            }}
          >
            <RefreshCw size={14} aria-hidden="true" /> Refresh Hardware
          </button>
        </div>
      </div>

      {/* Expandable QR Code Node Pairing Drawer */}
      {showQRPairing && (
        <div style={{ maxWidth: '400px', width: '100%' }}>
          <InlineQRPairing
            selectedDirection={selectedDirection as any}
            setSelectedDirection={setSelectedDirection as any}
          />
        </div>
      )}

      {/* 2×2 Video Wall */}
      <VideoWall
        connectedDirections={connectedCams}
        selectedDirection={selectedDirection}
        onSelectDirection={setSelectedDirection}
      />

      {/* Camera Inspector Panel */}
      <InspectorPanel
        selectedDirection={selectedDirection}
        isConfigured={isConfigured}
        latencyMs={selectedInfo?.latency_ms}
        source={selectedInfo?.source}
        onDisconnect={handleDisconnect}
      />
    </div>
  );
};

export default DevicesManagerPage;

