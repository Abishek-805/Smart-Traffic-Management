import React from 'react';

export const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  // Pass-through wrapper ready for future auth token check if required
  return <>{children}</>;
};
