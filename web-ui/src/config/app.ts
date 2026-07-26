/**
 * Application Configuration Module
 * Reads environment variables and exposes unified configuration parameters.
 */

export const API_BASE_URL = import.meta.env.VITE_API_BASE || '/api/v1';
export const WS_TELEMETRY_URL = import.meta.env.VITE_WS_URL || '/ws/telemetry';
export const WS_CAMERA_URL = import.meta.env.VITE_CAMERA_WS_URL || '/ws/camera';

export const APP_VERSION = '1.0.0';
export const PROTOCOL_VERSION = '1.0';
export const DEFAULT_POLL_INTERVAL_MS = 5000;
