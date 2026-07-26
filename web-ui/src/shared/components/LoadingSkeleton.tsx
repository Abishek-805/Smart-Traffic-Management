import React from 'react';

export const LoadingSkeleton: React.FC<{ height?: string; width?: string }> = ({
  height = '120px',
  width = '100%',
}) => {
  return (
    <div
      className="glass-card"
      style={{
        height,
        width,
        opacity: 0.6,
        animation: 'pulse-dot 1.5s infinite ease-in-out',
      }}
    />
  );
};
