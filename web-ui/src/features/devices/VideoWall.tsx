/**
 * VideoWall (Devices Feature Sub-Component)
 * 2×2 camera stream grid extracted from DevicesManagerPage.
 * Always-live feeds — no popup modals, no click-to-view.
 */

import React from 'react';
import { CameraGrid } from '../../shared/components/scada/CameraGrid';

interface VideoWallProps {
  connectedDirections: string[];
  selectedDirection: string;
  onSelectDirection: (dir: string) => void;
}

export const VideoWall: React.FC<VideoWallProps> = ({
  connectedDirections,
  selectedDirection,
  onSelectDirection,
}) => {
  return (
    <CameraGrid
      connectedDirections={connectedDirections}
      selectedDirection={selectedDirection}
      onSelectDirection={onSelectDirection}
    />
  );
};
