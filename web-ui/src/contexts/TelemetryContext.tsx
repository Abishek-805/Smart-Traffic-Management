import React, { createContext, useContext, useEffect, useState } from 'react';
import { WS_TELEMETRY_URL, resolveWebSocketUrl } from '../config/app';
import { TelemetryPayload } from '../types';

export type StreamStatusState = 'CONNECTING' | 'LIVE' | 'STALE' | 'DISCONNECTED';
interface TelemetryContextType {
  telemetry: TelemetryPayload | null;
  isConnected: boolean;
  streamStatus: StreamStatusState;
  frameAgeMs: number;
  pipelineHealthy: boolean;
  lastUpdated: Date | null;
  reconnectCount: number;
  isConnectionFailed: boolean;
  retryConnection: () => void;
}
const TelemetryContext = createContext<TelemetryContextType>({
  telemetry: null, isConnected: false, streamStatus: 'CONNECTING', frameAgeMs: 0,
  pipelineHealthy: false, lastUpdated: null, reconnectCount: 0,
  isConnectionFailed: false, retryConnection: () => {},
});

export const TelemetryProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [telemetry, setTelemetry] = useState<TelemetryPayload | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [now, setNow] = useState(Date.now());
  const [reconnectCount, setReconnectCount] = useState(0);
  const [isConnectionFailed, setIsConnectionFailed] = useState(false);
  const [retryTrigger, setRetryTrigger] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), 500);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    let socket: WebSocket | null = null;
    let timer: ReturnType<typeof setTimeout> | undefined;
    let active = true;
    let attempts = 0;
    setReconnectCount(0);
    setIsConnectionFailed(false);
    const retry = () => {
      if (!active) return;
      setIsConnected(false);
      attempts += 1;
      setReconnectCount(attempts);
      setIsConnectionFailed(attempts >= 5);
      timer = setTimeout(connect, Math.min(1000 * 2 ** Math.min(attempts, 5), 30000));
    };
    const connect = () => {
      if (!active) return;
      try {
        socket = new WebSocket(resolveWebSocketUrl(WS_TELEMETRY_URL));
        socket.onopen = () => { if (active) setIsConnected(true); };
        socket.onmessage = event => {
          if (!active) return;
          try {
            const msg = JSON.parse(event.data);
            if (!msg?.payload || typeof msg.payload !== 'object' || !msg.payload.lanes || typeof msg.payload.lanes !== 'object') return;
            attempts = 0;
            setReconnectCount(0);
            setIsConnectionFailed(false);
            setTelemetry(msg.payload);
            setLastUpdated(new Date());
          } catch { /* Freshness exposes malformed or stalled producers. */ }
        };
        socket.onclose = retry;
        socket.onerror = () => socket?.close();
      } catch { retry(); }
    };
    connect();
    return () => {
      active = false;
      clearTimeout(timer);
      if (socket) { socket.onclose = null; socket.close(); }
    };
  }, [retryTrigger]);

  // Age from receipt; never subtract clocks on different devices.
  const elapsed = lastUpdated ? Math.max(0, now - lastUpdated.getTime()) : 0;
  const frameAgeMs = Math.max(0, telemetry?.frameAgeMs ?? 0) + elapsed;
  const streamStatus: StreamStatusState = !isConnected ? 'DISCONNECTED'
    : !lastUpdated ? 'CONNECTING' : elapsed > 3000 ? 'STALE' : telemetry?.streamStatus ?? 'STALE';
  const pipelineHealthy = isConnected && elapsed < 3000 && telemetry?.pipelineHealthy === true;
  return <TelemetryContext.Provider value={{ telemetry, isConnected, streamStatus, frameAgeMs,
    pipelineHealthy, lastUpdated, reconnectCount, isConnectionFailed,
    retryConnection: () => setRetryTrigger(n => n + 1) }}>{children}</TelemetryContext.Provider>;
};
export const useTelemetry = () => useContext(TelemetryContext);
