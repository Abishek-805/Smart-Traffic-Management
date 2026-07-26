/**
 * TerminalConsole (Logs Feature Sub-Component)
 * Monospace live terminal output area with search, pause/resume, and per-line copy.
 */

import React, { useRef, useEffect } from 'react';
import { LogEntryItem } from '../../types';
import { Search, Copy, Check, Play, Pause } from 'lucide-react';

interface TerminalConsoleProps {
  logs: LogEntryItem[];
  searchQuery: string;
  onSearchChange: (q: string) => void;
  isPaused: boolean;
  isFollowActive: boolean;
  copiedId: string | null;
  onTogglePause: () => void;
  onCopyLog: (log: LogEntryItem) => void;
}

export const TerminalConsole: React.FC<TerminalConsoleProps> = ({
  logs,
  searchQuery,
  onSearchChange,
  isPaused,
  isFollowActive,
  copiedId,
  onTogglePause,
  onCopyLog,
}) => {
  const logsEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isFollowActive && !isPaused && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, isFollowActive, isPaused]);

  return (
    <div className="scada-card" style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
      {/* Controls Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        {/* Search */}
        <div style={{ position: 'relative', flex: 1, maxWidth: '400px' }}>
          <Search
            size={14}
            color="var(--text-muted)"
            aria-hidden="true"
            style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)' }}
          />
          <input
            id="log-search"
            type="text"
            placeholder="Search terminal logs..."
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            aria-label="Search terminal logs"
            style={{
              width: '100%',
              padding: '6px 12px 6px 32px',
              borderRadius: '6px',
              backgroundColor: 'rgba(0,0,0,0.2)',
              border: '1px solid var(--border-color)',
              color: 'var(--text-main)',
              fontSize: '0.8rem',
            }}
          />
        </div>

        {/* Stream Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div
            style={{ fontSize: '0.78rem', fontWeight: 700, color: isPaused ? '#f59e0b' : '#10b981' }}
            aria-live="polite"
            aria-label={isPaused ? 'Log stream paused' : 'Following live stream'}
          >
            {isPaused ? '⏸ PAUSED' : '● FOLLOWING LIVE'}
          </div>
          <button
            onClick={onTogglePause}
            aria-label={isPaused ? 'Resume log stream' : 'Pause log stream'}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '4px',
              backgroundColor: 'rgba(255,255,255,0.05)',
              border: '1px solid var(--border-color)',
              borderRadius: '6px',
              padding: '6px 10px',
              color: 'var(--text-main)',
              cursor: 'pointer',
              fontSize: '0.75rem',
              fontWeight: 600,
            }}
          >
            {isPaused ? <Play size={12} aria-hidden="true" /> : <Pause size={12} aria-hidden="true" />}
            <span>{isPaused ? 'Resume' : 'Pause'}</span>
          </button>
        </div>
      </div>

      {/* Terminal Output */}
      <div
        role="log"
        aria-label="System event log terminal"
        aria-live="polite"
        style={{
          backgroundColor: '#04070d',
          borderRadius: '6px',
          border: '1px solid var(--border-color)',
          padding: '12px',
          height: '520px',
          overflowY: 'auto',
          fontFamily: 'var(--font-mono)',
          fontSize: '0.8rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '6px',
        }}
      >
        {logs.map((log) => {
          const isError   = log.level === 'ERROR';
          const isWarning = log.level === 'WARNING';
          const levelColor = isError ? '#ef4444' : isWarning ? '#f59e0b' : '#10b981';

          return (
            <div
              key={log.id}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                gap: '12px',
                padding: '3px 6px',
                borderRadius: '4px',
                backgroundColor: isError
                  ? 'rgba(239,68,68,0.08)'
                  : isWarning
                  ? 'rgba(245,158,11,0.08)'
                  : 'transparent',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flex: 1, wordBreak: 'break-all' }}>
                <span style={{ color: 'var(--text-muted)' }}>
                  {new Date(log.timestamp).toLocaleTimeString()}
                </span>
                <span style={{ color: levelColor, fontWeight: 700, width: '60px' }}>
                  [{log.level}]
                </span>
                <span style={{ color: '#06b6d4', fontWeight: 600 }}>[{log.category}]</span>
                <span style={{ color: 'var(--text-main)', fontWeight: 600 }}>{log.component}:</span>
                <span style={{ color: 'var(--text-main)' }}>{log.message}</span>
              </div>

              <button
                onClick={() => onCopyLog(log)}
                aria-label="Copy log line"
                style={{
                  background: 'none',
                  border: 'none',
                  color: copiedId === log.id ? '#10b981' : 'var(--text-muted)',
                  cursor: 'pointer',
                  padding: '2px',
                }}
              >
                {copiedId === log.id
                  ? <Check size={12} aria-hidden="true" />
                  : <Copy size={12} aria-hidden="true" />}
              </button>
            </div>
          );
        })}

        <div ref={logsEndRef} />

        {logs.length === 0 && (
          <div style={{ padding: '32px', textAlign: 'center', color: 'var(--text-muted)' }}>
            Console ready. Waiting for backend event streams...
          </div>
        )}
      </div>
    </div>
  );
};
