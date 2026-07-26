/**
 * Analytics Domain API Client
 */

import { apiFetch } from './client';
import { AnalyticsSummaryData } from '../../types';

export const analyticsApi = {
  getAnalyticsSummary: () => apiFetch<AnalyticsSummaryData>('/analytics'),
};
