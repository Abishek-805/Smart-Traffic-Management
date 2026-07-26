/**
 * Shared Formatters (src/shared/utils/formatters.ts)
 * Pure formatting functions for SCADA display values.
 * No React imports — usable in ViewModels, components, and tests.
 */

/** Format a vehicle count as a compact string (e.g. "1420" → "1.4k") */
export const formatVehicleCount = (count: number): string => {
  if (count >= 1000) return `${(count / 1000).toFixed(1)}k`;
  return String(count);
};

/** Format milliseconds latency to display string */
export const formatLatencyMs = (ms: number): string => `${ms} ms`;

/** Format seconds remaining for signal phase countdown */
export const formatCountdownSeconds = (seconds: number): string =>
  seconds <= 0 ? '0s' : `${Math.round(seconds)}s`;

/** Format a frames-per-second value to one decimal */
export const formatFps = (fps: number): string => `${fps.toFixed(1)} FPS`;

/** Format queue length in metres */
export const formatQueueLength = (meters: number): string => `${meters.toFixed(1)} m`;

/** Format PCE score to two decimal places */
export const formatPceScore = (score: number): string => score.toFixed(2);

/** Format uptime duration from seconds to HH:MM:SS */
export const formatUptime = (seconds: number): string => {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  return `${String(h).padStart(2, '0')}h ${String(m).padStart(2, '0')}m ${String(s).padStart(2, '0')}s`;
};

/** Format a percentage value (0–100) to one decimal place string */
export const formatPercentage = (value: number): string => `${value.toFixed(1)}%`;

/** Format a temperature reading */
export const formatTemperature = (celsius: number): string => `${celsius.toFixed(1)} °C`;
