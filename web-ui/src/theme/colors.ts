/**
 * SCADA 5-State Color System & Palette Tokens
 */

export const colors = {
  // Backgrounds & Surface Elevation
  bgMain: '#070b14',
  bgSurface: '#0f172a',
  bgSurfaceHover: '#1e293b',
  bgSidebar: '#04070d',
  bgHeader: 'rgba(7, 11, 20, 0.95)',
  bgOverlay: 'rgba(7, 11, 20, 0.85)',

  // Text Hierarchy
  textMain: '#f8fafc',
  textMuted: '#94a3b8',
  textSubtle: '#64748b',

  // Borders & Glows
  borderColor: 'rgba(255, 255, 255, 0.08)',
  borderHighlight: 'rgba(255, 255, 255, 0.16)',

  // SCADA 5-State Operational Palette
  statusGreen: '#10b981',       // Active green phase
  statusGreenGlow: 'rgba(16, 185, 129, 0.25)',
  
  statusAmber: '#f59e0b',       // Waiting / Transition phase
  statusAmberGlow: 'rgba(245, 158, 11, 0.25)',

  statusBlue: '#3b82f6',        // Camera online (inactive phase)
  statusBlueGlow: 'rgba(59, 130, 246, 0.25)',

  statusGrey: '#64748b',        // Camera offline / unassigned
  statusGreyGlow: 'rgba(100, 116, 139, 0.15)',

  statusRed: '#ef4444',         // Hardware fault / disconnected
  statusRedGlow: 'rgba(239, 68, 68, 0.25)',

  // Operational Category Accent
  primary: '#3b82f6',
  info: '#06b6d4',
  warning: '#f59e0b',
  danger: '#ef4444',
  success: '#10b981',
};

export type ColorTokens = typeof colors;
