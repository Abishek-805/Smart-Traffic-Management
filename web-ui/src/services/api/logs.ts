/**
 * Logs Domain API Client
 */

import { apiFetch } from './client';
import { LogsResponseData, LogCategory } from '../../types';

export const logsApi = {
  getLogs: (category: LogCategory = 'ALL', level: string = 'ALL', search?: string, limit: number = 100) => {
    const params = new URLSearchParams();
    if (category) params.append('category', category);
    if (level) params.append('level', level);
    if (search) params.append('search', search);
    params.append('limit', limit.toString());

    return apiFetch<LogsResponseData>(`/logs?${params.toString()}`);
  },
};
