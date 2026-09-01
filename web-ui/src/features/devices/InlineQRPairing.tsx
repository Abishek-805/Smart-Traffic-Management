import React, { useEffect, useRef, useState } from 'react';
import { nodeApi } from '../../services/api/node';
import { apiFetch } from '../../services/api/client';
import { DIRECTIONS, DIRECTION_LABELS, DirectionType } from '../../constants/directions';
import { useMobileNodes } from '../../shared/hooks/useSystemQueries';
import { useNotifications } from '../../contexts/NotificationContext';
interface Props { selectedDirection: DirectionType; setSelectedDirection: (dir: DirectionType) => void; }
export const InlineQRPairing: React.FC<Props> = ({ selectedDirection, setSelectedDirection }) => {
  const [qr, setQr] = useState<{ image: string; expires: number; address: string } | null>(null);
  const [busy, setBusy] = useState(false);
  const [now, setNow] = useState(Date.now());
  const generation = useRef(0);
  const { addToast } = useNotifications();
  const { data, refetch } = useMobileNodes();
  const connected = data?.nodes.find(n => n.assigned_lane.toLowerCase().startsWith(selectedDirection))?.status === 'CONNECTED';
  useEffect(() => { generation.current++; setQr(null); setBusy(false); }, [selectedDirection]);
  useEffect(() => { const timer = setInterval(() => setNow(Date.now()), 1000); return () => clearInterval(timer); }, []);
  const generate = async () => {
    const id = ++generation.current;
    setBusy(true);
    setQr(null);
    try {
      const res = await nodeApi.generateQRCode(selectedDirection);
      if (id !== generation.current) return;
      if (!res.qr_image) throw new Error('Server did not generate a QR code');
      setQr({ image: res.qr_image, expires: res.payload.expires, address: res.payload.server + ':' + res.payload.port });
      await refetch();
    } catch (e) { addToast('error', 'Pairing failed', e instanceof Error ? e.message : 'Runtime unavailable'); }
    finally { if (id === generation.current) setBusy(false); }
  };
  const disconnect = async () => {
    setBusy(true);
    try { await apiFetch('/cameras/' + selectedDirection, { method: 'DELETE' }); await refetch(); setQr(null); }
    catch (e) { addToast('error', 'Disconnect failed', e instanceof Error ? e.message : 'Runtime unavailable'); }
    finally { setBusy(false); }
  };
  const remaining = qr ? Math.max(0, Math.ceil((qr.expires - now) / 1000)) : 0;
  return <section className="scada-card pairing-card" style={{ padding: 14, display: 'grid', gap: 12 }}>
    <label htmlFor="pairing-direction" style={{ fontWeight: 800 }}>Camera direction</label>
    <select id="pairing-direction" value={selectedDirection} onChange={e => setSelectedDirection(e.target.value as DirectionType)}
      style={{ padding: 10, background: 'var(--bg-primary)', color: 'var(--text-main)' }}>
      {DIRECTIONS.map(d => <option key={d} value={d}>{DIRECTION_LABELS[d]}</option>)}
    </select>
    {connected ? <><p>Camera connected. Live status appears in the feed below.</p><button disabled={busy} onClick={disconnect}>Disconnect camera</button></>
      : <><p style={{ margin: 0, color: 'var(--text-muted)', fontSize: 12 }}>Use the native camera app on the same trusted LAN. Each phone needs a different direction.</p>
        {qr && remaining > 0 && <><img src={qr.image} alt={selectedDirection + ' camera pairing QR'} style={{ width: 240, maxWidth: '100%', justifySelf: 'center' }} />
          <span className="font-mono-num" style={{ textAlign: 'center', overflowWrap: 'anywhere' }}>{qr.address}<br />Expires in {remaining}s</span></>}
        {qr && remaining === 0 && <p>Code expired. Generate a new code.</p>}
        <button className="pairing-button" onClick={generate} disabled={busy}>{busy ? 'Generating…' : `Generate ${DIRECTION_LABELS[selectedDirection]} QR`}</button>
      </>}
  </section>;
};
