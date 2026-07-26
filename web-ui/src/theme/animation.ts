/**
 * Animation Tokens (Max 250ms hardware-accelerated cubic-bezier)
 */

export const animation = {
  durationFast: '150ms',
  durationNormal: '250ms',
  durationSlow: '400ms',
  
  easingFast: 'cubic-bezier(0.4, 0, 0.2, 1)',
  easingNormal: 'cubic-bezier(0.16, 1, 0.3, 1)',

  transitionFast: 'all 150ms cubic-bezier(0.4, 0, 0.2, 1)',
  transitionNormal: 'all 250ms cubic-bezier(0.16, 1, 0.3, 1)',
};

export type AnimationTokens = typeof animation;
