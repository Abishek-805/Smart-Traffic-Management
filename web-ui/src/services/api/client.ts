/**
 * Base HTTP API Client Module
 * Standardizes fetch requests, response envelope extraction, and error handling.
 */

import { API_BASE_URL } from '../../config/app';
import { ApiResponse } from '../../types';

export class ApiError extends Error {
  code: string;
  constructor(message: string, code: string = 'UNKNOWN_ERROR') {
    super(message);
    this.code = code;
    this.name = 'ApiError';
  }
}

export async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;

  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  try {
    const res = await fetch(url, { ...options, headers, signal: options.signal ?? AbortSignal.timeout(10000) });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new ApiError(body.detail || `HTTP ${res.status}: ${res.statusText}`, `HTTP_${res.status}`);
    }

    const payload: ApiResponse<T> = await res.json();
    if (!payload.success) {
      const err = payload.error || { code: 'API_ERROR', message: 'API returned failure status' };
      throw new ApiError(err.message, err.code);
    }

    return payload.data as T;
  } catch (error: any) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw new ApiError(error.message || 'Network request failed', 'NETWORK_ERROR');
  }
}
