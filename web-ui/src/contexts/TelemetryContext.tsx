/**
 * TelemetryContext
 * Singleton WebSocket connection manager for live stream pulse telemetry.
 */

import React, { createContext, useContext, useEffect, useState } from 'react';
import { WS_TELEMETRY_URL } from '../config/app';
import { TelemetryMessage, TelemetryPayload } from '../types';

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
  telemetry: null,
  isConnected: false,
  streamStatus: 'CONNECTING',
  frameAgeMs: 0,
  pipelineHealthy: true,
  lastUpdated: null,
  reconnectCount: 0,
  isConnectionFailed: false,
  retryConnection: () => {},
});

export const TelemetryProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [telemetry, setTelemetry] = useState<TelemetryPayload | null>(null);
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(new Date());
  const [reconnectCount, setReconnectCount] = useState<number>(0);
  const [isConnectionFailed, setIsConnectionFailed] = useState<boolean>(false);
  const [retryTrigger, setRetryTrigger] = useState<number>(0);

  const retryConnection = () => {
    setReconnectCount(0);
    setIsConnectionFailed(false);
    setRetryTrigger((prev) => prev + 1);
  };

  useEffect(() => {
    let ws: WebSocket | null = null;
    let reconnectTimeout: any = null;
    let delayTimeout: any = null;
    let isCurrent = true;

    const connect = () => {
      if (!isCurrent) return;
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}${WS_TELEMETRY_URL}`;

      try {
        ws = new WebSocket(wsUrl);

        ws.onopen = () => {
          if (!isCurrent) return;
          setIsConnected(true);
          setIsConnectionFailed(false);
          setReconnectCount(0);
        };

        ws.onmessage = (event) => {
          if (!isCurrent) return;
          try {
            const msg: TelemetryMessage = JSON.parse(event.data);
            if (msg && msg.payload) {
              const receiveTime = Date.now();
              const payload = msg.payload as any;
              payload.dashboardReceiveTimestamp = receiveTime;
              
              const capTime = payload.captureTimestamp;
              const bcastTime = payload.broadcastTimestamp;
              if (capTime) {
                const renderTime = Date.now() + 16; // Estimate React commit phase delay (16ms)
                payload.dashboardRenderTimestamp = renderTime;
                const frameAge = renderTime - capTime;
                const pipelineLatency = payload.schedulerTimestamp ? (payload.schedulerTimestamp - capTime) : 0;
                const transportLatency = bcastTime ? (receiveTime - bcastTime) : 0;
                const dashboardLatency = renderTime - receiveTime;
                
                payload.frameAgeMs = frameAge;
                console.log(`[LATENCY-PROFILE] FrameAge: ${frameAge}ms | Pipeline: ${pipelineLatency}ms | Transport: ${transportLatency}ms | Dashboard: ${dashboardLatency}ms`);
              }

              setTelemetry(msg.payload);
              setLastUpdated(new Date());
            }
          } catch (err) {
            console.error('Telemetry WebSocket parse error:', err);
          }
        };

        ws.onclose = () => {
          if (!isCurrent) return;
          setIsConnected(false);
          
          setReconnectCount((prev) => {
            const next = prev + 1;
            if (next > 5) {
              setIsConnectionFailed(true);
              return prev; // keep it at max
            }
            
            // Reconnect backoff: 1.5s, 3s, 5s, 5s...
            const delays = [1500, 3000, 5000];
            const delay = delays[next - 1] || 5000;
            reconnectTimeout = setTimeout(connect, delay);
            return next;
          });
        };

        ws.onerror = () => {
          if (!isCurrent) return;
          setIsConnected(false);
        };
      } catch (e) {
        if (!isCurrent) return;
        setIsConnected(false);
        setReconnectCount((prev) => {
          const next = prev + 1;
          if (next > 5) {
            setIsConnectionFailed(true);
            return prev;
          }
          const delays = [1500, 3000, 5000];
          const delay = delays[next - 1] || 5000;
          reconnectTimeout = setTimeout(connect, delay);
          return next;
        });
      }
    };

    const startConnection = () => {
      // 100ms connection delay only if running in development mode
      const isDev = import.meta.env.DEV;
      if (isDev) {
        delayTimeout = setTimeout(connect, 100);
      } else {
        connect();
      }
    };

    startConnection();

    return () => {
      isCurrent = false;
      if (ws) ws.close();
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
      if (delayTimeout) clearTimeout(delayTimeout);
    };
  }, [retryTrigger]);

  const currentStreamStatus: StreamStatusState = !isConnected
    ? 'DISCONNECTED'
    : telemetry?.streamStatus || 'LIVE';

  const frameAgeMs = telemetry?.frameAgeMs || 0;
  const pipelineHealthy = telemetry?.pipelineHealthy !== undefined ? telemetry.pipelineHealthy : true;

  return (
    <TelemetryContext.Provider value={{
      telemetry,
      isConnected,
      streamStatus: currentStreamStatus,
      frameAgeMs,
      pipelineHealthy,
      lastUpdated,
      reconnectCount,
      isConnectionFailed,
      retryConnection
    }}>
      {children}
    </TelemetryContext.Provider>
  );
};

export const useTelemetry = () => useContext(TelemetryContext);
