import React, { useState, useEffect } from 'react';
import { QrCode, RefreshCw, Smartphone, CheckCircle, Clock, AlertCircle } from 'lucide-react';
import { nodeApi } from '../../services/api/node';
import { systemApi } from '../../services/api/system';
import { DIRECTION_LABELS, DirectionType } from '../../constants/directions';
import { useMobileNodes } from '../../shared/hooks/useSystemQueries';
import { FEATURE_FLAGS } from '../../config/featureFlags';
import { useNotifications } from '../../contexts/NotificationContext';

interface InlineQRPairingProps {
  selectedDirection: DirectionType;
  setSelectedDirection: (dir: DirectionType) => void;
}

export const InlineQRPairing: React.FC<InlineQRPairingProps> = ({
  selectedDirection,
  setSelectedDirection,
}) => {
  const { addToast } = useNotifications();
  const [qrImage, setQrImage] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [expiresInSeconds, setExpiresInSeconds] = useState<number>(300);
  const { data: mobileNodesData, refetch: refetchNodes } = useMobileNodes();
  const mobileNodes = mobileNodesData?.nodes || [];

  // Find if there is a node session for the selected direction
  const laneNode = mobileNodes.find(
    (n) => n.assigned_lane.toLowerCase().includes(selectedDirection)
  );

  const fetchQRCode = async (dir: string) => {
    setQrImage(null); // Clear stale QR immediately!
    setExpiresInSeconds(300);
    setLoading(true);
    try {
      const res = await nodeApi.generateQRCode(dir);
      if (res && res.qr_image) {
        setQrImage(res.qr_image);
      } else {
        const mockSvg = `data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="120" height="120" viewBox="0 0 120 120"><rect width="120" height="120" fill="%23161b22"/><rect x="10" y="10" width="40" height="40" fill="%23ffffff"/><rect x="20" y="20" width="20" height="20" fill="%23161b22"/><rect x="70" y="10" width="40" height="40" fill="%23ffffff"/><rect x="80" y="20" width="20" height="20" fill="%23161b22"/><rect x="10" y="70" width="40" height="40" fill="%23ffffff"/><rect x="20" y="80" width="20" height="20" fill="%23161b22"/><rect x="60" y="60" width="20" height="20" fill="%2358a6ff"/><rect x="90" y="70" width="20" height="40" fill="%2310b981"/></svg>`;
        setQrImage(mockSvg);
      }
      refetchNodes();
    } catch (err) {
      console.warn('QR API fallback active:', err);
      const mockSvg = `data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="120" height="120" viewBox="0 0 120 120"><rect width="120" height="120" fill="%23161b22"/><rect x="10" y="10" width="40" height="40" fill="%23ffffff"/><rect x="20" y="20" width="20" height="20" fill="%23161b22"/><rect x="70" y="10" width="40" height="40" fill="%23ffffff"/><rect x="80" y="20" width="20" height="20" fill="%23161b22"/><rect x="10" y="70" width="40" height="40" fill="%23ffffff"/><rect x="20" y="80" width="20" height="20" fill="%23161b22"/><rect x="60" y="60" width="20" height="20" fill="%2358a6ff"/><rect x="90" y="70" width="20" height="40" fill="%2310b981"/></svg>`;
      setQrImage(mockSvg);
      refetchNodes();
    } finally {
      setLoading(false);
    }
  };

  // Sync remaining countdown time with backend expires_at timestamp
  useEffect(() => {
    if (laneNode?.status === 'PAIRED' && laneNode.expires_at) {
      const remaining = Math.max(0, Math.floor((laneNode.expires_at - Date.now()) / 1000));
      setExpiresInSeconds(remaining);
      if (!qrImage && !loading) {
        fetchQRCode(selectedDirection);
      }
    } else {
      setQrImage(null);
    }
  }, [laneNode?.status, selectedDirection, laneNode?.expires_at]);

  // Handle active countdown timer decrement
  useEffect(() => {
    if (expiresInSeconds > 0 && laneNode?.status === 'PAIRED') {
      const timer = setInterval(() => {
        setExpiresInSeconds((prev) => prev - 1);
      }, 1000);
      return () => clearInterval(timer);
    }
  }, [expiresInSeconds, laneNode?.status]);

  const formatTimer = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
  };

  const handleDisconnect = async () => {
    if (confirm(`Are you sure you want to disconnect this camera slot? You will need to pair a mobile node again to restore the feed.`)) {
      setLoading(true);
      try {
        await systemApi.simulateDisconnect(selectedDirection);
        refetchNodes();
        addToast('warning', 'Camera Disconnected', `Disconnected ${DIRECTION_LABELS[selectedDirection]} slot.`);
      } catch (err: any) {
        addToast('error', 'Disconnect Failed', err.message || 'Failed to evict backend session.');
      } finally {
        setLoading(false);
      }
    }
  };

  const handleConnect = async () => {
    setLoading(true);
    try {
      await systemApi.simulateConnect(selectedDirection);
      refetchNodes();
      addToast('success', 'Camera Connected', `Simulated pairing connection for ${DIRECTION_LABELS[selectedDirection]} slot.`);
    } catch (err: any) {
      addToast('error', 'Simulation Failed', err.message || 'Failed to create simulated session.');
    } finally {
      setLoading(false);
    }
  };

  const label = DIRECTION_LABELS[selectedDirection] || 'North';

  return (
    <div className="scada-card" style={{ padding: '10px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
      {/* Header */}
      <div style={{ borderBottom: '1px solid #30363d', paddingBottom: '6px', marginBottom: '2px' }}>
        <span style={{ fontSize: '11px', fontWeight: 800, color: '#ffffff', letterSpacing: '0.04em' }}>
          {label.toUpperCase()} CAMERA
        </span>
      </div>

      {laneNode?.status === 'CONNECTED' ? (
        // CONNECTED state
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#10b981', fontSize: '11px', fontWeight: 700 }}>
            <CheckCircle size={12} />
            <span>{laneNode.name.split(' (')[0]} Connected</span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '4px', backgroundColor: '#0d1117', padding: '6px 8px', borderRadius: '3px', border: '1px solid #30363d', fontSize: '10px', color: '#8b949e' }} className="font-mono-num">
            <div>Battery: <span style={{ color: '#10b981' }}>{laneNode.battery_pct}%</span></div>
            <div>Signal: <span style={{ color: '#10b981' }}>{laneNode.signal_dbm} dBm</span></div>
            <div>FPS: <span style={{ color: '#bc8cff' }}>{laneNode.fps.toFixed(0)}</span></div>
            <div>Latency: <span style={{ color: '#58a6ff' }}>{laneNode.latency_ms} ms</span></div>
          </div>

          <button
            onClick={handleDisconnect}
            disabled={loading}
            style={{
              backgroundColor: 'rgba(239, 68, 68, 0.1)',
              color: '#ef4444',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              borderRadius: '3px',
              padding: '4px 8px',
              fontSize: '10px',
              fontWeight: 800,
              cursor: loading ? 'not-allowed' : 'pointer',
              marginTop: '4px',
              opacity: loading ? 0.7 : 1,
            }}
          >
            Disconnect Slot
          </button>
        </div>
      ) : laneNode?.status === 'PAIRED' ? (
        // PAIRED (Waiting for Device) state
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          {expiresInSeconds <= 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px', padding: '8px 0' }}>
              <AlertCircle size={24} color="#ef4444" />
              <span style={{ fontSize: '10px', color: '#ef4444', fontWeight: 700 }}>PAIRING TOKEN EXPIRED</span>
              <button
                onClick={() => fetchQRCode(selectedDirection)}
                disabled={loading}
                style={{
                  backgroundColor: '#21262d',
                  color: '#58a6ff',
                  border: '1px solid #30363d',
                  borderRadius: '3px',
                  padding: '4px 8px',
                  fontSize: '10px',
                  fontWeight: 800,
                  cursor: loading ? 'not-allowed' : 'pointer',
                  opacity: loading ? 0.7 : 1,
                }}
              >
                Generate New QR
              </button>
            </div>
          ) : (
            <>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '10px' }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: '4px', fontWeight: 700, color: '#f59e0b', flex: 1 }}>
                  <Smartphone size={12} className="pulse-active" />
                  Waiting for Mobile Camera...
                </span>
                <span className="font-mono-num" style={{ color: '#8b949e', display: 'flex', alignItems: 'center', gap: '3px' }}>
                  <Clock size={10} /> {formatTimer(expiresInSeconds)} remaining
                </span>
              </div>

              {qrImage && (
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '6px', backgroundColor: '#0d1117', padding: '8px', borderRadius: '4px', border: '1px solid #30363d' }}>
                  <img
                    src={qrImage.startsWith('data:') ? qrImage : `data:image/png;base64,${qrImage}`}
                    alt="Node Pairing QR Code"
                    style={{ width: '110px', height: '110px', objectFit: 'contain', borderRadius: '2px' }}
                  />
                  <span style={{ fontSize: '9px', color: '#8b949e', textAlign: 'center' }}>
                    Token: <span className="font-mono">{laneNode.node_id}</span>
                  </span>
                </div>
              )}

              <div style={{ display: 'flex', gap: '4px', marginTop: '4px' }}>
                <button
                  onClick={handleDisconnect}
                  disabled={loading}
                  style={{
                    flex: 1,
                    backgroundColor: '#21262d',
                    color: '#ef4444',
                    border: '1px solid #30363d',
                    borderRadius: '3px',
                    padding: '4px 8px',
                    fontSize: '10px',
                    fontWeight: 800,
                    cursor: loading ? 'not-allowed' : 'pointer',
                    opacity: loading ? 0.7 : 1,
                  }}
                >
                  Cancel Pairing
                </button>
                {FEATURE_FLAGS.enableDeveloperOverlay && (
                  <button
                    onClick={handleConnect}
                    disabled={loading}
                    style={{
                      flex: 1,
                      backgroundColor: '#238636',
                      color: '#ffffff',
                      border: '1px solid #30363d',
                      borderRadius: '3px',
                      padding: '4px 8px',
                      fontSize: '10px',
                      fontWeight: 800,
                      cursor: loading ? 'not-allowed' : 'pointer',
                      opacity: loading ? 0.7 : 1,
                    }}
                  >
                    Simulate Connect
                  </button>
                )}
              </div>
            </>
          )}
        </div>
      ) : (
        // UNPAIRED state
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px', padding: '12px 0' }}>
          <span style={{ fontSize: '10px', color: '#8b949e' }}>Slot Not Configured</span>
          <button
            onClick={() => fetchQRCode(selectedDirection)}
            disabled={loading}
            style={{
              width: '100%',
              backgroundColor: 'var(--color-primary)',
              color: '#ffffff',
              border: 'none',
              borderRadius: '3px',
              padding: '6px 12px',
              fontSize: '10.5px',
              fontWeight: 800,
              cursor: loading ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '4px',
              opacity: loading ? 0.7 : 1,
            }}
          >
            <QrCode size={12} />
            {loading ? 'Registering...' : 'Pair Camera Node'}
          </button>
        </div>
      )}
    </div>
  );
};
