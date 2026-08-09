import React from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { Sidebar } from '../components/Sidebar';
import { Header } from '../components/Header';
import { ToastContainer } from '../components/ToastContainer';
import { BackendConnected } from '../components/BackendConnected';
import { FooterStatusBar } from '../components/scada/FooterStatusBar';
import { useDashboardViewModel } from '../../features/dashboard/useDashboardViewModel';

export const DashboardLayout: React.FC = () => {
  const location = useLocation();
  const vm = useDashboardViewModel();
  const isDashboard = location.pathname === '/';

  return (
    <BackendConnected>
      <div style={{ display: 'flex', height: '100vh', width: '100vw', overflow: 'hidden', backgroundColor: 'var(--bg-main)' }}>
        <Sidebar />
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0, height: '100vh', overflow: 'hidden' }}>
          <Header />
          <main
            style={{
              flex: 1,
              padding: isDashboard ? '8px' : '24px',
              overflowY: isDashboard ? 'hidden' : 'auto',
              display: 'flex',
              flexDirection: 'column',
              minHeight: 0,
            }}
          >
            <Outlet />
          </main>
          <FooterStatusBar statusBar={vm.statusBar} metrics={vm.metrics} />
        </div>
        <ToastContainer />
      </div>
    </BackendConnected>
  );
};
