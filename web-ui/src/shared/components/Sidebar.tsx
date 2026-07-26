import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Cpu,
  BarChart3,
  Settings,
  FileText,
  Activity,
} from 'lucide-react';

const navItems = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/devices', label: 'Devices', icon: Cpu },
  { path: '/analytics', label: 'Analytics', icon: BarChart3 },
  { path: '/logs', label: 'Logs', icon: FileText },
  { path: '/settings', label: 'Settings', icon: Settings },
];

export const Sidebar: React.FC = () => {
  return (
    <aside style={{
      width: '240px',
      backgroundColor: 'var(--bg-sidebar)',
      borderRight: '1px solid var(--border-color)',
      display: 'flex',
      flexDirection: 'column',
      height: '100vh',
      position: 'fixed',
      left: 0,
      top: 0,
      zIndex: 100,
    }}>
      {/* Brand Header */}
      <div style={{
        padding: '20px 24px',
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
        borderBottom: '1px solid var(--border-color)',
      }}>
        <div style={{
          width: '36px',
          height: '36px',
          borderRadius: '8px',
          backgroundColor: 'var(--color-primary)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 0 12px var(--color-primary-glow)',
        }}>
          <Activity size={22} color="#ffffff" />
        </div>
        <div>
          <h1 style={{ fontSize: '0.95rem', fontWeight: 800, letterSpacing: '-0.02em', lineHeight: 1.1 }}>
            SMART TRAFFIC
          </h1>
          <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: 600 }}>
            CONTROL CENTER v1.0
          </span>
        </div>
      </div>

      {/* Navigation Links */}
      <nav style={{ padding: '16px 12px', display: 'flex', flexDirection: 'column', gap: '4px', flex: 1 }}>
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === '/'}
              style={({ isActive }) => ({
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                padding: '10px 16px',
                borderRadius: '8px',
                textDecoration: 'none',
                fontSize: '0.88rem',
                fontWeight: isActive ? 600 : 500,
                color: isActive ? '#ffffff' : 'var(--text-muted)',
                backgroundColor: isActive ? 'rgba(59, 130, 246, 0.15)' : 'transparent',
                borderLeft: isActive ? '3px solid var(--color-primary)' : '3px solid transparent',
                transition: 'all 0.15s ease',
              })}
            >
              <Icon size={18} />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>

      {/* Footer Meta */}
      <div style={{
        padding: '16px 20px',
        borderTop: '1px solid var(--border-color)',
        fontSize: '0.75rem',
        color: 'var(--text-muted)',
      }}>
        <p style={{ fontWeight: 600 }}>YOLO11 + ByteTrack</p>
        <p style={{ fontSize: '0.7rem', opacity: 0.7 }}>FastAPI + React 3-Tier</p>
      </div>
    </aside>
  );
};
