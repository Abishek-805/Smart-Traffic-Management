/**
 * Camera Domain API Client
 */

import { apiFetch } from './client';
import { CameraConfigResponse } from '../../types';
import { API_BASE_URL } from '../../config/app';

export const cameraApi = {
  getCameras: () => apiFetch<CameraConfigResponse>('/cameras'),
  configureCamera: (direction: string, config: Record<string, any>) =>
    apiFetch<Record<string, any>>(`/cameras/${direction}`, {
      method: 'POST',
      body: JSON.stringify(config),
    }),
  getPreviewUrl: (direction: string) => `${API_BASE_URL}/cameras/${direction}/feed`,
};
