/**
 * DevicesManagerPage (Devices Feature Module)
 * Thin composition controller per v3.1 architecture.
 * Delegates rendering to VideoWall + InspectorPanel sub-components.
 */

import React, { useState, useEffect } from 'react';
import { VideoWall } from '../devices/VideoWall';
import { InspectorPanel } from '../devices/InspectorPanel';
import { useCameraConfigs, useMobileNodes } from '../../shared/hooks/useSystemQueries';
import { useNotifications } from '../../contexts/NotificationContext';
import { RefreshCw } from 'lucide-react';

export const DevicesManagerPage: React.FC = () => {
  const { data: configData, refetch: refetchCameras } = useCameraConfigs();
  const { refetch: refetchNodes } = useMobileNodes();
  const { addToast } = useNotifications();

  const [connectedCams, setConnectedCams] = useState<string[]>([]);
  const [selectedDirection, setSelectedDirection] = useState<string>('north');

  useEffect(() => {
    const cams = localStorage.getItem('scc_connected_cameras');
    if (cams) {
      setConnectedCams(JSON.parse(cams));
    } else {
      const defaultCams = ['north', 'south', 'east', 'west'];
      setConnectedCams(defaultCams);
      localStorage.setItem('scc_connected_cameras', JSON.stringify(defaultCams));
    }
  }, []);

  const handleDisconnect = () => {
    const next = connectedCams.filter((c) => c !== selectedDirection.toLowerCase());
    setConnectedCams(next);
    localStorage.setItem('scc_connected_cameras', JSON.stringify(next));
    addToast('warning', 'Camera Disconnected', `${selectedDirection.toUpperCase()} camera slot is now offline.`);
  };

  const selectedInfo = configData?.streams?.[selectedDirection];
  const isConfigured = connectedCams.includes(selectedDirection.toLowerCase());

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Header */}
      <div className="scada-card" style={{ padding: '16px 20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 style={{ fontSize: '1.2rem', fontWeight: 800 }}>Intersection Camera Video Wall</h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>
            Continuous 2×2 live video feeds. Click any stream to view inspector telemetry below.
          </p>
        </div>
        <button
          onClick={() => { refetchCameras(); refetchNodes(); }}
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
            fontWeight: 600,
            cursor: 'pointer',
            fontSize: '0.8rem',
          }}
        >
          <RefreshCw size={14} aria-hidden="true" /> Refresh Hardware
        </button>
      </div>

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
