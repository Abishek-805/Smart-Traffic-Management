/**
 * LogViewerPage (Logs Feature Module) — v3.1 thin composition
 * Owns state, data fetching, and export actions.
 * Delegates rendering to LogFilters + TerminalConsole sub-components.
 */

import React, { useState, useEffect } from 'react';
import { useLogs } from '../../shared/hooks/useSystemQueries';
import { LogCategory, LogEntryItem } from '../../types';
import { Download, RefreshCw } from 'lucide-react';
import { useNotifications } from '../../contexts/NotificationContext';
import { LogFilters } from './LogFilters';
import { TerminalConsole } from './TerminalConsole';

export const LogViewerPage: React.FC = () => {
  const { addToast } = useNotifications();
  const [selectedCategory, setSelectedCategory] = useState<LogCategory>('ALL');
  const [selectedLevel] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [isPaused, setIsPaused] = useState<boolean>(false);
  const [displayedLogs, setDisplayedLogs] = useState<LogEntryItem[]>([]);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const queryCategory = ['AI', 'NODE', 'ESP32', 'SYSTEM'].includes(selectedCategory)
    ? (selectedCategory as LogCategory)
    : 'ALL';
  const queryLevel = ['INFO', 'WARNING', 'ERROR'].includes(selectedCategory)
    ? selectedCategory
    : 'ALL';

  const { data, refetch, isFetching } = useLogs(queryCategory, queryLevel, searchQuery);
  const rawLogs = data?.logs || [];

  useEffect(() => {
    if (!isPaused) setDisplayedLogs(rawLogs);
  }, [rawLogs, isPaused]);

  const handleTogglePause = () => {
    if (isPaused) {
      setIsPaused(false);
      setDisplayedLogs(rawLogs);
      addToast('info', 'Log Stream Resumed', 'Synchronized terminal with live backend events.');
    } else {
      setIsPaused(true);
      addToast('info', 'Log Stream Paused', 'Freezing current log view for inspection.');
    }
  };

  const handleCopyLog = async (log: LogEntryItem) => {
    const text = `${new Date(log.timestamp).toLocaleTimeString()} [${log.level}] [${log.category}] ${log.component}: ${log.message}`;
    try {
      await navigator.clipboard.writeText(text);
      setCopiedId(log.id);
      setTimeout(() => setCopiedId(null), 1500);
    } catch (err) {
      console.error('Failed to copy log:', err);
    }
  };

  const exportJSON = () => {
    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(rawLogs, null, 2));
    const a = document.createElement('a');
    a.setAttribute('href', dataStr);
    a.setAttribute('download', `traffic_logs_${new Date().toISOString()}.json`);
    document.body.appendChild(a);
    a.click();
    a.remove();
  };

  const exportCSV = () => {
    if (!rawLogs.length) return;
    const headers = ['Timestamp', 'Level', 'Category', 'Component', 'Message'];
    const rows = rawLogs.map((l) => [l.timestamp, l.level, l.category, l.component, `"${l.message}"`]);
    const csv = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
    const a = document.createElement('a');
    a.setAttribute('href', encodeURI(csv));
    a.setAttribute('download', `traffic_logs_${new Date().toISOString()}.csv`);
    document.body.appendChild(a);
    a.click();
    a.remove();
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Header */}
      <div className="scada-card" style={{ padding: '16px 20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 style={{ fontSize: '1.2rem', fontWeight: 800 }}>SCADA Real-Time Log Terminal</h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>
            High-density event stream console. Filter by component category or inspect pinned hardware alerts.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          <button
            onClick={() => refetch()}
            aria-label="Refresh log stream"
            style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', backgroundColor: 'rgba(255,255,255,0.05)', color: 'var(--text-main)', border: '1px solid var(--border-color)', borderRadius: '6px', padding: '8px 14px', fontWeight: 600, fontSize: '0.8rem', cursor: 'pointer' }}
          >
            <RefreshCw size={14} aria-hidden="true" className={isFetching ? 'spin' : ''} /> Refresh
          </button>
          <button
            onClick={exportJSON}
            aria-label="Export logs as JSON"
            style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', backgroundColor: 'rgba(59,130,246,0.12)', color: '#3b82f6', border: '1px solid rgba(59,130,246,0.3)', borderRadius: '6px', padding: '8px 14px', fontWeight: 600, fontSize: '0.8rem', cursor: 'pointer' }}
          >
            <Download size={14} aria-hidden="true" /> Export JSON
          </button>
          <button
            onClick={exportCSV}
            aria-label="Export logs as CSV"
            style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', backgroundColor: 'rgba(16,185,129,0.12)', color: '#10b981', border: '1px solid rgba(16,185,129,0.3)', borderRadius: '6px', padding: '8px 14px', fontWeight: 600, fontSize: '0.8rem', cursor: 'pointer' }}
          >
            <Download size={14} aria-hidden="true" /> Export CSV
          </button>
        </div>
      </div>

      {/* Two-Column Layout */}
      <div style={{ display: 'grid', gridTemplateColumns: '260px 1fr', gap: '20px' }}>
        <LogFilters
          selectedCategory={selectedCategory}
          onSelectCategory={setSelectedCategory}
        />
        <TerminalConsole
          logs={displayedLogs}
          searchQuery={searchQuery}
          onSearchChange={setSearchQuery}
          isPaused={isPaused}
          isFollowActive={true}
          copiedId={copiedId}
          onTogglePause={handleTogglePause}
          onCopyLog={handleCopyLog}
          selectedCategory={selectedCategory}
        />
      </div>
    </div>
  );
};

export default LogViewerPage;
