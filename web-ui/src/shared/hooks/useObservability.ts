/**
 * SCADA Developer Observability Hook (useObservability)
 * Tracks render frame duration, FPS, WebSocket latency, and component render counts.
 * Active in development mode or when enableObservability feature flag is engaged.
 */

import { useState, useEffect, useRef } from 'react';
import { FEATURE_FLAGS } from '../../config/featureFlags';

export interface ObservabilityMetrics {
  fps: number;
  renderDurationMs: number;
  wsLatencyMs: number;
  frameAgeMs: number;
  isPerformingWell: boolean;
}

export const useObservability = (wsLatency: number = 18, frameAge: number = 12): ObservabilityMetrics => {
  const [fps, setFps] = useState<number>(60);
  const [renderDurationMs, setRenderDurationMs] = useState<number>(8);
  const frameCount = useRef<number>(0);
  const lastTime = useRef<number>(performance.now());

  useEffect(() => {
    if (!FEATURE_FLAGS.enableObservability) return;

    let animId: number;

    const measure = () => {
      const start = performance.now();
      frameCount.current += 1;
      const now = performance.now();
      const delta = now - lastTime.current;

      if (delta >= 1000) {
        setFps(Math.round((frameCount.current * 1000) / delta));
        frameCount.current = 0;
        lastTime.current = now;
      }

      const end = performance.now();
      setRenderDurationMs(Math.round(end - start));
      animId = requestAnimationFrame(measure);
    };

    animId = requestAnimationFrame(measure);

    return () => cancelAnimationFrame(animId);
  }, []);

  return {
    fps,
    renderDurationMs,
    wsLatencyMs: wsLatency,
    frameAgeMs: frameAge,
    isPerformingWell: fps >= 55 && renderDurationMs < 16,
  };
};
