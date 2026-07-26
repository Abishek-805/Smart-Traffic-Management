/**
 * Mobile Node Domain API Client
 */

import { apiFetch } from './client';
import { MobileNodesData } from '../../types';

export const nodeApi = {
  getMobileNodes: () => apiFetch<MobileNodesData>('/mobile-nodes'),
  generateQRCode: (direction: string = 'north') =>
    apiFetch<{ payload: Record<string, any>; qr_image: string }>(`/qr/generate?direction=${encodeURIComponent(direction)}`),
};
