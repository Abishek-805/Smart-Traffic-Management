/**
 * Fixed Approach Direction Enumerations & Types
 */

export type DirectionType = 'north' | 'east' | 'south' | 'west';

export const DIRECTIONS: DirectionType[] = ['north', 'east', 'south', 'west'];

export const DIRECTION_LABELS: Record<DirectionType, string> = {
  north: 'North Approach',
  east: 'East Approach',
  south: 'South Approach',
  west: 'West Approach',
};

export const DIRECTION_VECTORS: Record<DirectionType, string> = {
  north: '▲',
  east: '►',
  south: '▼',
  west: '◄',
};
