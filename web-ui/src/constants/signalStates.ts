/**
 * Fixed Signal Phase States & Colors
 */

export type SignalStateType = 'GREEN' | 'AMBER' | 'RED';

export const SIGNAL_STATES: Record<SignalStateType, { label: string; color: string; bg: string }> = {
  GREEN: {
    label: 'CURRENT GREEN',
    color: '#10b981',
    bg: 'rgba(16, 185, 129, 0.15)',
  },
  AMBER: {
    label: 'TRANSITION',
    color: '#f59e0b',
    bg: 'rgba(245, 158, 11, 0.15)',
  },
  RED: {
    label: 'RED SIGNAL',
    color: '#ef4444',
    bg: 'rgba(239, 68, 68, 0.15)',
  },
};
