import React from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { Sidebar } from '../components/Sidebar';
import { Header } from '../components/Header';
import { ToastContainer } from '../components/ToastContainer';
import { BackendConnected } from '../components/BackendConnected';

export const DashboardLayout: React.FC = () => {
  const location = useLocation();
  // Dashboard root (/) is a fixed 0-scroll viewport — overflow must be hidden.
  // Every other route (analytics, logs, settings, devices) scrolls normally.
  const isDashboard = location.pathname === '/';

  return (
    <BackendConnected>
      <div style={{ display: 'flex', minHeight: '100vh', backgroundColor: 'var(--bg-main)' }}>
        <Sidebar />
        <div style={{ flex: 1, marginLeft: '240px', display: 'flex', flexDirection: 'column', minWidth: 0, height: '100vh', overflow: 'hidden' }}>
          <Header />
          <main
            style={{
              flex: 1,
              padding: isDashboard ? '16px 20px' : '28px',
              overflowY: isDashboard ? 'hidden' : 'auto',
              display: 'flex',
              flexDirection: 'column',
              minHeight: 0,
            }}
          >
            <Outlet />
          </main>
        </div>
        <ToastContainer />
      </div>
    </BackendConnected>
  );
};
