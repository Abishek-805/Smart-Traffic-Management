import React, { useState } from 'react';
import { useTelemetry } from '../../contexts/TelemetryContext';
import { useTheme } from '../../contexts/ThemeContext';
import { useSystemHealth } from '../hooks/useSystemQueries';
import { Sun, Moon, Radio, ShieldAlert, Cpu, Bell, X, Activity } from 'lucide-react';
import { DiagnosticsDrawer } from './DiagnosticsDrawer';

export const Header: React.FC = () => {
  const { telemetry, isConnected, reconnectCount, isConnectionFailed, retryConnection } = useTelemetry();
  const { theme, toggleTheme } = useTheme();
  const { data: health } = useSystemHealth();

  const [isDiagnosticsOpen, setIsDiagnosticsOpen] = useState(false);
  const [isNotificationsOpen, setIsNotificationsOpen] = useState(false);
  
  const [notifications, setNotifications] = useState([
    { id: '1', time: '10:25', message: 'South Queue High (Vehicle Count: 14)', level: 'warning' },
    { id: '2', time: '10:24', message: 'Emergency Hold Released (North Corridor)', level: 'success' },
    { id: '3', time: '10:22', message: 'Signal Phase Changed: East Approach Green', level: 'info' },
    { id: '4', time: '10:21', message: 'Mobile Camera Node Connected: Galaxy A52', level: 'info' },
  ]);

  const operatingMode = telemetry?.operatingMode || health?.operating_mode || 'AUTOMATIC';

  // Component Health Checks
  const isAiHealthy = health?.components?.ai?.status === 'HEALTHY' || health?.system_status === 'RUNNING';
  const isEsp32Healthy = health?.components?.esp32?.status === 'HEALTHY';
  
  // Read active cameras from localStorage
  const activeCamsString = localStorage.getItem('scc_connected_cameras') || '[]';
  const activeCamsCount = JSON.parse(activeCamsString).length;
  const isCamerasHealthy = activeCamsCount > 0;

  return (
    <>
      <header style={{
        height: '64px',
        backgroundColor: 'var(--bg-header)',
        backdropFilter: 'var(--glass-backdrop)',
        borderBottom: '1px solid var(--border-color)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 28px',
        position: 'sticky',
        top: 0,
        zIndex: 90,
      }}>
        {/* Left Section: Operating Mode & Health Pills */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '6px 12px',
            borderRadius: '20px',
            backgroundColor: operatingMode === 'AUTOMATIC' ? 'rgba(16, 185, 129, 0.12)' : 'rgba(245, 158, 11, 0.15)',
            border: `1px solid ${operatingMode === 'AUTOMATIC' ? '#10b981' : '#f59e0b'}`,
            fontSize: '0.78rem',
            fontWeight: 700,
            color: operatingMode === 'AUTOMATIC' ? '#10b981' : '#f59e0b',
          }}>
            {operatingMode === 'AUTOMATIC' ? <Cpu size={14} /> : <ShieldAlert size={14} />}
            <span>{operatingMode === 'AUTOMATIC' ? 'AI AUTO MODE' : 'MANUAL OVERRIDE'}</span>
          </div>

          {/* Quick Health Summary Pills */}
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            <span
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '4px',
                fontSize: '0.72rem',
                fontWeight: 700,
                padding: '3px 8px',
                borderRadius: '6px',
                backgroundColor: 'rgba(255,255,255,0.03)',
                border: '1px solid var(--border-color)',
              }}
              title="AI Perception Engine status"
            >
              <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: isAiHealthy ? '#10b981' : '#ef4444' }} />
              AI
            </span>
            <span
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '4px',
                fontSize: '0.72rem',
                fontWeight: 700,
                padding: '3px 8px',
                borderRadius: '6px',
                backgroundColor: 'rgba(255,255,255,0.03)',
                border: '1px solid var(--border-color)',
              }}
              title="Connected Slots status"
            >
              <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: isCamerasHealthy ? '#10b981' : '#f59e0b' }} />
              CAMERAS
            </span>
            <span
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '4px',
                fontSize: '0.72rem',
                fontWeight: 700,
                padding: '3px 8px',
                borderRadius: '6px',
                backgroundColor: 'rgba(255,255,255,0.03)',
                border: '1px solid var(--border-color)',
              }}
              title="ESP32 Controller hardware status"
            >
              <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: isEsp32Healthy ? '#10b981' : '#ef4444' }} />
              ESP32
            </span>
            <span
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '4px',
                fontSize: '0.72rem',
                fontWeight: 700,
                padding: '3px 8px',
                borderRadius: '6px',
                backgroundColor: 'rgba(255,255,255,0.03)',
                border: '1px solid var(--border-color)',
              }}
              title="API Gateway / WebSocket status"
            >
              <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: isConnected ? '#10b981' : '#ef4444' }} />
              BACKEND
            </span>
          </div>
        </div>

        {/* WebSocket Retry Warnings Panel */}
        {!isConnected && (
          <div style={{
            flex: 1,
            margin: '0 24px',
            backgroundColor: isConnectionFailed ? 'rgba(239, 68, 68, 0.15)' : 'rgba(245, 158, 11, 0.15)',
            border: `1px solid ${isConnectionFailed ? '#ef4444' : '#f59e0b'}`,
            color: isConnectionFailed ? '#ef4444' : '#f59e0b',
            padding: '4px 12px',
            borderRadius: '6px',
            fontSize: '0.78rem',
            fontWeight: 600,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            maxWidth: '450px'
          }}>
            <span>
              ⚠️ {isConnectionFailed 
                ? 'Unable to reconnect to Telemetry Server.' 
                : `Telemetry connection lost. Reconnecting... (Attempt ${reconnectCount}/5)`}
            </span>
            <button
              onClick={retryConnection}
              style={{
                backgroundColor: 'transparent',
                border: 'none',
                color: 'inherit',
                textDecoration: 'underline',
                cursor: 'pointer',
                fontWeight: 700,
                fontSize: '0.75rem',
              }}
            >
              {isConnectionFailed ? 'Retry Now' : 'Force Reconnect'}
            </button>
          </div>
        )}

        {/* Right Section: Signal Status HUD & Drawer Buttons */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          {/* Active Phase Pill */}
          {telemetry && isConnected && (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              backgroundColor: 'rgba(255, 255, 255, 0.05)',
              padding: '6px 14px',
              borderRadius: '8px',
              border: '1px solid var(--border-color)',
            }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600 }}>
                ACTIVE PHASE:
              </span>
              <span style={{ fontSize: '0.85rem', fontWeight: 800, color: 'var(--color-primary)' }}>
                {telemetry.activePhase.toUpperCase()}
              </span>
              <span style={{
                fontSize: '0.85rem',
                fontWeight: 800,
                backgroundColor: '#10b981',
                color: '#000000',
                padding: '2px 8px',
                borderRadius: '4px',
              }}>
                {telemetry.timeRemaining}s
              </span>
            </div>
          )}

          {/* Diagnostics Button */}
          <button
            onClick={() => setIsDiagnosticsOpen(true)}
            style={{
              background: 'none',
              border: '1px solid var(--border-color)',
              borderRadius: '8px',
              padding: '8px 12px',
              color: 'var(--text-main)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              fontSize: '0.78rem',
              fontWeight: 600,
            }}
          >
            <Activity size={15} color="var(--color-primary)" />
            <span>Diagnostics</span>
          </button>

          {/* Notification Bell */}
          <button
            onClick={() => setIsNotificationsOpen(true)}
            style={{
              background: 'none',
              border: '1px solid var(--border-color)',
              borderRadius: '8px',
              padding: '8px',
              color: 'var(--text-main)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              position: 'relative',
            }}
            title="Notification Centre"
          >
            <Bell size={18} />
            {notifications.length > 0 && (
              <span style={{
                position: 'absolute',
                top: '-4px',
                right: '-4px',
                backgroundColor: '#ef4444',
                color: '#ffffff',
                fontSize: '0.62rem',
                fontWeight: 800,
                width: '15px',
                height: '15px',
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}>
                {notifications.length}
              </span>
            )}
          </button>

          {/* Theme Toggle Button */}
          <button
            onClick={toggleTheme}
            style={{
              background: 'none',
              border: '1px solid var(--border-color)',
              borderRadius: '8px',
              padding: '8px',
              color: 'var(--text-main)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
            title="Toggle Dark / Light Theme"
          >
            {theme === 'dark' ? <Sun size={18} color="#f59e0b" /> : <Moon size={18} color="#3b82f6" />}
          </button>
        </div>
      </header>

      {/* Slide-out Diagnostics Drawer */}
      <DiagnosticsDrawer isOpen={isDiagnosticsOpen} onClose={() => setIsDiagnosticsOpen(false)} />

      {/* Notification Centre Drawer */}
      {isNotificationsOpen && (
        <div style={{
          position: 'fixed',
          top: 0,
          right: 0,
          width: '380px',
          height: '100vh',
          backgroundColor: 'var(--bg-sidebar)',
          borderLeft: '1px solid var(--border-color)',
          boxShadow: '-10px 0 30px rgba(0, 0, 0, 0.5)',
          zIndex: 1000,
          display: 'flex',
          flexDirection: 'column',
          animation: 'slideIn 0.3s ease-out',
        }}>
          <div style={{
            padding: '20px 24px',
            borderBottom: '1px solid var(--border-color)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Bell size={18} color="var(--color-primary)" />
              <h3 style={{ fontSize: '1.05rem', fontWeight: 800 }}>Notification Centre</h3>
            </div>
            <button
              onClick={() => setIsNotificationsOpen(false)}
              style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
            >
              <X size={18} />
            </button>
          </div>

          <div style={{ padding: '16px', flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {notifications.map((notif) => (
              <div
                key={notif.id}
                style={{
                  padding: '12px 14px',
                  borderRadius: '8px',
                  backgroundColor: 'rgba(255, 255, 255, 0.02)',
                  border: `1px solid var(--border-color)`,
                  borderLeft: `3px solid ${
                    notif.level === 'warning' ? '#f59e0b' : notif.level === 'success' ? '#10b981' : '#3b82f6'
                  }`,
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                  <span style={{
                    fontSize: '0.72rem',
                    fontWeight: 700,
                    color: notif.level === 'warning' ? '#f59e0b' : notif.level === 'success' ? '#10b981' : '#3b82f6'
                  }}>
                    {notif.level.toUpperCase()}
                  </span>
                  <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{notif.time}</span>
                </div>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-main)', margin: 0 }}>{notif.message}</p>
              </div>
            ))}
            
            {notifications.length === 0 && (
              <div style={{ padding: '32px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.82rem' }}>
                No recent event alerts.
              </div>
            )}
          </div>

          <div style={{ padding: '16px', borderTop: '1px solid var(--border-color)' }}>
            <button
              onClick={() => setNotifications([])}
              style={{
                width: '100%',
                backgroundColor: 'rgba(255,255,255,0.05)',
                color: 'var(--text-main)',
                border: '1px solid var(--border-color)',
                borderRadius: '8px',
                padding: '10px',
                cursor: 'pointer',
                fontSize: '0.8rem',
                fontWeight: 600,
              }}
            >
              Clear All Notifications
            </button>
          </div>
        </div>
      )}
    </>
  );
};
