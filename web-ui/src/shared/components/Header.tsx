/**
 * Header Component (SCADA Minimal Operator Header)
 * Contract Section: Header
 * Left: Current phase | Countdown | Operating mode
 * Center: WebSocket | YOLO | ESP32 | Health
 * Right: Start | Stop | Restart | Emergency | Diagnostics
 */

import React, { useState } from 'react';
import { useTelemetry } from '../../contexts/TelemetryContext';
import { useNotifications } from '../../contexts/NotificationContext';
import { useSystemHealth, useSystemControls } from '../hooks/useSystemQueries';
import { Play, Square, RotateCcw, AlertTriangle, Activity, Radio, Cpu, Video, Shield, RefreshCw } from 'lucide-react';
import { DiagnosticsDrawer } from './DiagnosticsDrawer';

export const Header: React.FC = () => {
  const { telemetry, isConnected } = useTelemetry();
  const { data: health } = useSystemHealth();
  const { addToast } = useNotifications();
  const { startMutation, stopMutation, restartMutation } = useSystemControls();

  const [isDiagnosticsOpen, setIsDiagnosticsOpen] = useState(false);

  const activePhase = telemetry?.activePhase || 'North';
  const remainingSeconds = telemetry?.timeRemaining !== undefined ? telemetry.timeRemaining : 0;
  const operatingMode = telemetry?.operatingMode || health?.operating_mode || 'AUTOMATIC';

  const isAiHealthy = health?.components?.ai?.status === 'HEALTHY' || (isConnected && Boolean(telemetry));
  const aiFps = health?.components?.ai?.fps || (telemetry?.frameAgeMs && telemetry.frameAgeMs > 0 ? Math.min(60, Math.round(1000 / telemetry.frameAgeMs)) : 0);

  const esp32Comp = health?.components?.esp32;
  const isEsp32Connected = Boolean(esp32Comp?.connected);
  const isEsp32Sim = Boolean(esp32Comp?.simulation);

  let esp32StatusLabel = 'OFFLINE';
  let esp32StatusColor = '#ef4444';
  if (isEsp32Connected) {
    esp32StatusLabel = 'ACTIVE';
    esp32StatusColor = '#10b981';
  } else if (isEsp32Sim) {
    esp32StatusLabel = 'SIMULATION';
    esp32StatusColor = '#06b6d4';
  }

  const handleStart = () => {
    startMutation.mutate(undefined, {
      onSuccess: (data: any) => {
        addToast('success', 'System Started', data?.message || 'AI Perception Engine loop started.');
      },
      onError: (err: any) => {
        addToast('error', 'Start Failed', err?.message || 'Failed to start AI Perception Engine.');
      }
    });
  };

  const handleStop = () => {
    if (confirm('Are you sure you want to stop the AI Perception Engine loop? This will pause real-time traffic signal optimization.')) {
      stopMutation.mutate(undefined, {
        onSuccess: (data: any) => {
          addToast('success', 'System Stopped', data?.message || 'AI Perception Engine loop stopped.');
        },
        onError: (err: any) => {
          addToast('error', 'Stop Failed', err?.message || 'Failed to stop AI Perception Engine.');
        }
      });
    }
  };

  const handleRestart = () => {
    if (confirm('Are you sure you want to restart the AI Perception Engine? This will temporarily interrupt traffic monitoring.')) {
      restartMutation.mutate(undefined, {
        onSuccess: (data: any) => {
          addToast('success', 'System Restarted', data?.message || 'AI System restart initiated.');
        },
        onError: (err: any) => {
          addToast('error', 'Restart Failed', err?.message || 'Failed to restart AI System.');
        }
      });
    }
  };

  return (
    <>
      <header
        style={{
          height: '42px',
          maxHeight: '42px',
          backgroundColor: '#161b22',
          borderBottom: '1px solid #30363d',
          padding: '0 12px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          fontSize: '11px',
          userSelect: 'none',
          zIndex: 90,
        }}
      >
        {/* Left Section: Current Phase | Countdown | Operating Mode */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', backgroundColor: '#0d1117', padding: '3px 8px', borderRadius: '3px', border: '1px solid #30363d' }}>
            <Shield size={13} color="#10b981" />
            <span style={{ fontWeight: 800, color: '#ffffff', letterSpacing: '0.04em' }}>SCADA TCC</span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', backgroundColor: 'rgba(16, 185, 129, 0.15)', border: '1px solid #10b981', padding: '3px 8px', borderRadius: '3px' }}>
            <span style={{ color: '#10b981', fontWeight: 800 }}>GREEN:</span>
            <span style={{ color: '#ffffff', fontWeight: 800, textTransform: 'uppercase' }}>{activePhase}</span>
          </div>

          <div className="font-mono-num" style={{ backgroundColor: '#21262d', color: '#58a6ff', border: '1px solid #30363d', padding: '3px 8px', borderRadius: '3px', fontWeight: 800, fontSize: '11px' }}>
            ⏱ {remainingSeconds}s
          </div>

          <span
            style={{
              backgroundColor: operatingMode === 'EMERGENCY_OVERRIDE' ? 'rgba(239,68,68,0.2)' : '#21262d',
              color: operatingMode === 'EMERGENCY_OVERRIDE' ? '#ef4444' : '#c9d1d9',
              border: `1px solid ${operatingMode === 'EMERGENCY_OVERRIDE' ? '#ef4444' : '#30363d'}`,
              padding: '3px 6px',
              borderRadius: '3px',
              fontWeight: 800,
              fontSize: '10px',
            }}
          >
            {operatingMode}
          </span>
        </div>

        {/* Center Section: WebSocket | YOLO | ESP32 | System Health */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', backgroundColor: '#0d1117', padding: '3px 10px', borderRadius: '3px', border: '1px solid #30363d' }} className="font-mono-num">
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <Radio size={11} color={isConnected ? '#10b981' : '#ef4444'} />
            <span style={{ color: '#8b949e' }}>WS:</span>
            <span style={{ color: isConnected ? '#10b981' : '#ef4444', fontWeight: 800 }}>{isConnected ? 'ONLINE' : 'OFFLINE'}</span>
          </div>

          <span style={{ color: '#30363d' }}>|</span>

          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <Cpu size={11} color="#bc8cff" />
            <span style={{ color: '#8b949e' }}>YOLO11:</span>
            <span style={{ color: isAiHealthy ? '#10b981' : '#f59e0b', fontWeight: 800 }}>{isAiHealthy ? `${aiFps > 0 ? aiFps.toFixed(0) : 'ACTIVE'} FPS` : 'FAULT'}</span>
          </div>

          <span style={{ color: '#30363d' }}>|</span>

          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <Video size={11} color="#58a6ff" />
            <span style={{ color: '#8b949e' }}>ESP32:</span>
            <span style={{ color: esp32StatusColor, fontWeight: 800 }}>{esp32StatusLabel}</span>
          </div>
        </div>

        {/* Right Section: Start | Stop | Restart | Emergency | Diagnostics Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <button
            onClick={handleStart}
            disabled={startMutation.isPending || stopMutation.isPending || restartMutation.isPending}
            style={{
              backgroundColor: '#161b22',
              color: '#10b981',
              border: '1px solid #30363d',
              borderRadius: '3px',
              padding: '3px 6px',
              fontSize: '10px',
              fontWeight: 800,
              cursor: startMutation.isPending ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '3px',
              opacity: startMutation.isPending ? 0.6 : 1,
            }}
            title="Start System Scheduler"
          >
            {startMutation.isPending ? (
              <>
                <RefreshCw size={10} className="spin" /> Starting...
              </>
            ) : (
              <>
                <Play size={10} /> Start
              </>
            )}
          </button>

          <button
            onClick={handleStop}
            disabled={startMutation.isPending || stopMutation.isPending || restartMutation.isPending}
            style={{
              backgroundColor: '#161b22',
              color: '#ef4444',
              border: '1px solid #30363d',
              borderRadius: '3px',
              padding: '3px 6px',
              fontSize: '10px',
              fontWeight: 800,
              cursor: stopMutation.isPending ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '3px',
              opacity: stopMutation.isPending ? 0.6 : 1,
            }}
            title="Stop System Scheduler"
          >
            {stopMutation.isPending ? (
              <>
                <RefreshCw size={10} className="spin" /> Stopping...
              </>
            ) : (
              <>
                <Square size={10} /> Stop
              </>
            )}
          </button>

          <button
            onClick={handleRestart}
            disabled={startMutation.isPending || stopMutation.isPending || restartMutation.isPending}
            style={{
              backgroundColor: '#161b22',
              color: '#58a6ff',
              border: '1px solid #30363d',
              borderRadius: '3px',
              padding: '3px 6px',
              fontSize: '10px',
              fontWeight: 800,
              cursor: restartMutation.isPending ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '3px',
              opacity: restartMutation.isPending ? 0.6 : 1,
            }}
            title="Restart Service Engine"
          >
            {restartMutation.isPending ? (
              <>
                <RefreshCw size={10} className="spin" /> Restarting...
              </>
            ) : (
              <>
                <RotateCcw size={10} /> Restart
              </>
            )}
          </button>

          <button
            disabled={true}
            style={{
              backgroundColor: 'rgba(239, 68, 68, 0.05)',
              color: '#f87171',
              border: '1px solid rgba(239, 68, 68, 0.2)',
              borderRadius: '3px',
              padding: '3px 8px',
              fontSize: '10px',
              fontWeight: 800,
              cursor: 'not-allowed',
              opacity: 0.6,
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
            }}
            title="Emergency control is unavailable on the backend. Feature is simulation-only."
          >
            <AlertTriangle size={11} /> EMERGENCY (SIM ONLY)
          </button>

          <button
            onClick={() => setIsDiagnosticsOpen(true)}
            style={{
              backgroundColor: '#21262d',
              color: '#c9d1d9',
              border: '1px solid #30363d',
              borderRadius: '3px',
              padding: '3px 8px',
              fontSize: '10px',
              fontWeight: 800,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
            }}
            title="Open System Diagnostics Drawer"
          >
            <Activity size={11} color="#58a6ff" /> Diagnostics
          </button>
        </div>
      </header>

      <DiagnosticsDrawer isOpen={isDiagnosticsOpen} onClose={() => setIsDiagnosticsOpen(false)} />
    </>
  );
};
