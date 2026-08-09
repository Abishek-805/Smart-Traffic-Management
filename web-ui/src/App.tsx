import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { TelemetryProvider } from './contexts/TelemetryContext';
import { ThemeProvider } from './contexts/ThemeContext';
import { NotificationProvider } from './contexts/NotificationContext';
import { SettingsProvider } from './contexts/SettingsContext';

import { DashboardLayout } from './shared/layouts/DashboardLayout';
import { ErrorBoundary } from './shared/components/ErrorBoundary';

import { OverviewPage } from './features/dashboard/OverviewPage';
import { DevicesManagerPage } from './features/cameras/DevicesManagerPage';
import { AnalyticsPage } from './features/analytics/AnalyticsPage';
import { SettingsPage } from './features/settings/SettingsPage';
import { LogViewerPage } from './features/logs/LogViewerPage';
import { NotFoundPage } from './shared/components/NotFoundPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      staleTime: 5000,
    },
  },
});

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <SettingsProvider>
          <NotificationProvider>
            <TelemetryProvider>
              <BrowserRouter>
                <ErrorBoundary>
                  <Routes>
                    <Route path="/" element={<DashboardLayout />}>
                      <Route index element={<OverviewPage />} />
                      <Route path="devices" element={<DevicesManagerPage />} />
                      <Route path="analytics" element={<AnalyticsPage />} />
                      <Route path="settings" element={<SettingsPage />} />
                      <Route path="logs" element={<LogViewerPage />} />
                      <Route path="*" element={<NotFoundPage />} />
                    </Route>
                  </Routes>
                </ErrorBoundary>
              </BrowserRouter>
            </TelemetryProvider>
          </NotificationProvider>
        </SettingsProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
};

export default App;
