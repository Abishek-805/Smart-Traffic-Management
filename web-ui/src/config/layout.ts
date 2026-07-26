/**
 * Dashboard Layout Parameters & Metrics Configuration
 */

export interface DashboardLayoutConfig {
  statusBarHeight: number;
  phaseBarHeight: number;
  metricBarHeight: number;
  laneAspectRatio: number;
  centerNodeSize: number;
  gap: number;
}

export const DASHBOARD_LAYOUT_CONFIG: DashboardLayoutConfig = {
  statusBarHeight: 72,
  phaseBarHeight: 48,
  metricBarHeight: 56,
  laneAspectRatio: 16 / 9,
  centerNodeSize: 220,
  gap: 16,
};
