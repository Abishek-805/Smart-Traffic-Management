/**
 * Telemetry Domain Constants & Fallbacks
 */

import { TelemetryPayload } from '../types';

export const DEFAULT_TELEMETRY_PAYLOAD: TelemetryPayload = {
  activePhase: 'North',
  greenDuration: 25,
  timeRemaining: 18,
  totalVehicles: 42,
  queueLength: 4.8,
  pceScore: 2.4,
  operatingMode: 'AUTOMATIC',
  streamStatus: 'CONNECTING',
  frameAgeMs: 12,
  pipelineHealthy: true,
  pipelineStalled: false,
};
