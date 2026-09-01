/**
 * Sidebar Component (TOC SCADA Navigation)
 * SCADA v2.0.0 Navigation Sidebar
 * Preserves React Router NavLink route paths ('/', '/devices', '/analytics', '/logs', '/settings')
 */

import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Video,
  BarChart3,
  FileText,
  Settings,
  Shield,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';

const navItems = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/devices', label: 'Live Cameras', icon: Video },
  { path: '/analytics', label: 'Analytics', icon: BarChart3 },
  { path: '/logs', label: 'Operations Logs', icon: FileText },
  { path: '/settings', label: 'Settings', icon: Settings },
];

export const Sidebar: React.FC = () => {
  const [collapsed, setCollapsed] = useState(true);

  return (
    <aside
      style={{
        width: collapsed ? '52px' : '180px',
        backgroundColor: 'var(--bg-secondary)',
        borderRight: '1px solid #30363d',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        height: '100vh',
        flexShrink: 0,
        zIndex: 100,
        userSelect: 'none',
        transition: 'width 150ms ease',
      }}
    >
      {/* Brand Header */}
      <div>
        <div
          style={{
            padding: collapsed ? '10px' : '10px 14px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            borderBottom: '1px solid #30363d',
            height: '42px',
          }}
        >
          <div
            style={{
              width: '26px',
              height: '26px',
              borderRadius: '3px',
              backgroundColor: 'var(--bg-primary)',
              border: '1px solid #30363d',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#10b981',
              flexShrink: 0,
            }}
          >
            <Shield size={14} aria-hidden="true" />
          </div>
          {!collapsed && (
            <div>
              <h1 style={{ fontSize: '0.8rem', fontWeight: 800, letterSpacing: '0.04em', color: 'var(--text-main)', lineHeight: 1.1 }}>
                TOC CONTROL
              </h1>
              <span className="font-mono-num" style={{ fontSize: '8px', color: 'var(--text-muted)' }}>
                SCADA v2.0.0
              </span>
            </div>
          )}
        </div>

        {/* Navigation Links */}
        <nav style={{ padding: '6px 4px', display: 'flex', flexDirection: 'column', gap: '2px' }}>
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                end={item.path === '/'}
                title={collapsed ? item.label : undefined}
                style={({ isActive }) => ({
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: collapsed ? '8px 12px' : '8px 10px',
                  borderRadius: '3px',
                  textDecoration: 'none',
                  fontSize: '0.75rem',
                  fontWeight: isActive ? 700 : 500,
                  color: isActive ? 'var(--text-main)' : 'var(--text-muted)',
                  backgroundColor: isActive ? 'var(--bg-surface)' : 'transparent',
                  borderLeft: isActive ? '3px solid #58a6ff' : '3px solid transparent',
                  transition: 'all 120ms ease',
                })}
              >
                <Icon size={15} style={{ flexShrink: 0 }} aria-hidden="true" />
                {!collapsed && <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{item.label}</span>}
              </NavLink>
            );
          })}
        </nav>
      </div>

      {/* Collapse Toggle Footer */}
      <div
        style={{
          padding: '6px 10px',
          borderTop: '1px solid #30363d',
          display: 'flex',
          alignItems: 'center',
          justifyContent: collapsed ? 'center' : 'space-between',
          color: 'var(--text-muted)',
        }}
      >
        {!collapsed && <span className="font-mono-num" style={{ fontSize: '9px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Collapse</span>}
        <button
          onClick={() => setCollapsed(!collapsed)}
          style={{
            background: 'var(--bg-surface)',
            border: '1px solid #30363d',
            borderRadius: '3px',
            color: 'var(--text-main)',
            padding: '3px',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
          title={collapsed ? 'Expand menu' : 'Collapse menu'}
        >
          {collapsed ? <ChevronRight size={13} aria-hidden="true" /> : <ChevronLeft size={13} aria-hidden="true" />}
        </button>
      </div>
    </aside>
  );
};
