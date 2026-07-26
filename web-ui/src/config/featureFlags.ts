/**
 * SCADA System Feature Flags Configuration
 */

export interface FeatureFlags {
  enableIntersectionSchematic: boolean;
  enableObservability: boolean;
  enableDeveloperOverlay: boolean;
  enableAnimations: boolean;
}

export const FEATURE_FLAGS: FeatureFlags = {
  enableIntersectionSchematic: true,
  enableObservability: import.meta.env.DEV,
  enableDeveloperOverlay: import.meta.env.DEV,
  enableAnimations: true,
};
