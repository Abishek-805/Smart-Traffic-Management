/**
 * System Operational Domain API Client
 */

import { apiFetch } from './client';
import { SystemHealthData, SystemVersionInfo } from '../../types';

export const systemApi = {
  getHealth: () => apiFetch<SystemHealthData>('/system/health'),
  getStatus: () => apiFetch<Record<string, any>>('/system/status'),
  getVersion: () => apiFetch<SystemVersionInfo>('/version'),
  getBuild: () => apiFetch<Record<string, string>>('/build'),
  startSystem: () => apiFetch<Record<string, any>>('/system/start', { method: 'POST' }),
  stopSystem: () => apiFetch<Record<string, any>>('/system/stop', { method: 'POST' }),
  restartSystem: () => apiFetch<Record<string, any>>('/system/restart', { method: 'POST' }),
  simulateConnect: (direction: string) =>
    apiFetch<Record<string, any>>(`/system/simulate-connect?direction=${encodeURIComponent(direction)}`, { method: 'POST' }),
  simulateDisconnect: (direction: string) =>
    apiFetch<Record<string, any>>(`/system/simulate-disconnect?direction=${encodeURIComponent(direction)}`, { method: 'POST' }),
};
