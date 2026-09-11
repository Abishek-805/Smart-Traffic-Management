/**
 * Dashboard ViewModel Layer (useDashboardViewModel)
 * Transforms raw WebSocket telemetry & system health into display-ready view models.
 * Completely isolates presentation components from transformation business logic.
 */

import { useMemo } from 'react';
import { useTelemetry } from '../../contexts/TelemetryContext';
import { useSystemHealth, useMobileNodes } from '../../shared/hooks/useSystemQueries';
import { DIRECTIONS, DIRECTION_LABELS, DirectionType } from '../../constants/directions';
import { cameraApi } from '../../services/api/camera';
import { HardwareConnectionState } from '../../types';

export interface LaneViewModel {
  direction: DirectionType;
  label: string;
  isGreen: boolean;
  statusColor: string;
  statusLabel: string;
  vehicleCount: number;
  queueLengthMeters: string;
  pceScore: string;
  priorityScore: string;
  waitTimeSeconds: number;
  latencyMs: number;
  frameAgeMs: number;
  streamUrl: string;
  streamStatus: 'CONNECTING' | 'LIVE' | 'STALE' | 'OFFLINE' | 'RECONNECTING' | 'DISCONNECTED';
  isConfigured: boolean;
  density: number;
  priority: number;
  fps: number;
  inferenceTimeMs: number;
  serverProcessingMs: number;
  queueWaitMs: number;
}

export interface PhaseViewModel {
  activeDirection: string;
  remainingSeconds: number;
  progressPercentage: number;
  phaseReason: string;
}

export interface StatusBarViewModel {
  operatingMode: 'AUTOMATIC' | 'MANUAL_OVERRIDE' | 'EMERGENCY_OVERRIDE';
  aiHealthy: boolean;
  backendHealthy: boolean;
  esp32Healthy: boolean;
  esp32State: HardwareConnectionState;
  activeCameraCount: number;
  totalCameraSlots: number;
  fps: number;
  latencyMs: number;
  schedulerStatus: string;
}

export interface MetricStripViewModel {
  totalVehicles: number;
  avgFps: number;
  inferenceTimeMs: number;
  processingQueueLength: number;
  pipelineLatencyMs: number;
  frameAgeMs: number;
  connectionHealth: 'HEALTHY' | 'DEGRADED' | 'DISCONNECTED';
}

export interface DashboardViewModel {
  lanes: Record<DirectionType, LaneViewModel>;
  activePhase: PhaseViewModel;
  statusBar: StatusBarViewModel;
  metrics: MetricStripViewModel;
}

export const useDashboardViewModel = (): DashboardViewModel => {
  const { telemetry, isConnected, streamStatus, frameAgeMs, pipelineHealthy, lastUpdated } = useTelemetry();
  const { data: health } = useSystemHealth();
  const { data: mobileNodesData } = useMobileNodes();
  const mobileNodes = mobileNodesData?.nodes || [];

  const activePhaseName = (telemetry?.activePhase || 'none').toLowerCase();
  const remainingTime = telemetry?.timeRemaining || 0;
  const greenDuration = telemetry?.greenDuration || 25;
  const progressPct = Math.min(100, Math.max(0, ((greenDuration - remainingTime) / greenDuration) * 100));

  return useMemo(() => {
    // Build 4 Lane ViewModels (North, East, South, West)
    const lanesList: Record<DirectionType, LaneViewModel> = DIRECTIONS.reduce((acc, dir) => {
      const isGreen = pipelineHealthy && activePhaseName === dir && telemetry?.signalState !== 'YELLOW';
      const laneNode = mobileNodes.find((n) => n.assigned_lane.toLowerCase().includes(dir));
      const isConfigured = laneNode?.status === 'CONNECTED';

      const laneData = telemetry?.lanes?.[dir];
      // Determine SCADA 5-color status
      let statusColor = '#64748b'; // Grey (Offline)
      let statusLabel = 'OFFLINE';
      let currentStreamStatus: LaneViewModel['streamStatus'] = 'OFFLINE';

      if (!isConnected) {
        statusColor = '#ef4444'; // Red (Fault/Disconnected)
        statusLabel = 'DISCONNECTED';
        currentStreamStatus = 'OFFLINE';
      } else if (isConfigured) {
        currentStreamStatus = streamStatus === 'DISCONNECTED' || streamStatus === 'STALE' ? streamStatus : laneData?.streamStatus ?? 'CONNECTING';
        if (isGreen) {
          statusColor = '#10b981'; // Green (Active)
          statusLabel = 'CURRENT GREEN';
        } else {
          statusColor = '#3b82f6'; // Blue (Online - Waiting)
          statusLabel = 'WAITING';
        }
      }

      const vehicles = laneData?.vehicles ?? 0;
      const queueVal = laneData?.queue ?? 0;
      const pceVal = laneData?.pce ?? 0;
      const prioVal = laneData?.priority ?? 0;
      const densityVal = laneData?.density ?? 0;
      const waitSec = laneData?.wait ?? (isGreen ? 0 : remainingTime);

      acc[dir] = {
        direction: dir,
        label: DIRECTION_LABELS[dir],
        isGreen,
        statusColor,
        statusLabel,
        vehicleCount: vehicles,
        queueLengthMeters: `${queueVal} veh`,
        pceScore: pceVal.toFixed(1),
        priorityScore: prioVal.toFixed(1),
        waitTimeSeconds: Math.round(waitSec),
        latencyMs: laneData?.serverProcessingMs ?? 0,
        frameAgeMs: laneData?.frameAgeMs == null ? 0 : laneData.frameAgeMs + (lastUpdated ? Math.max(0, Date.now() - lastUpdated.getTime()) : 0),
        streamUrl: cameraApi.getPreviewUrl(dir),
        streamStatus: currentStreamStatus,
        isConfigured,
        density: typeof densityVal === 'number' ? densityVal : parseFloat(densityVal) || 0,
        priority: prioVal,
        fps: currentStreamStatus === 'LIVE' ? laneData?.fps ?? 0 : 0,
        inferenceTimeMs: laneData?.inferenceTimeMs ?? 0,
        serverProcessingMs: laneData?.serverProcessingMs ?? 0,
        queueWaitMs: laneData?.queueWaitMs ?? 0,
      };

      return acc;
    }, {} as Record<DirectionType, LaneViewModel>);

    // StatusBar ViewModel
    const isAiHealthy = pipelineHealthy;
    const isEspHealthy = health?.components?.esp32?.status === 'HEALTHY';
    const esp32State = health?.components?.esp32?.connection_state ?? 'DISCONNECTED';
    const currentFps = Object.values(lanesList).reduce((sum, lane) => sum + lane.fps, 0);
    const connectedCamsCount = mobileNodes.filter((n) => n.status === 'CONNECTED').length;

    const statusBar: StatusBarViewModel = {
      operatingMode: telemetry?.operatingMode || 'AUTOMATIC',
      aiHealthy: isAiHealthy,
      backendHealthy: isConnected,
      esp32Healthy: isEspHealthy,
      esp32State,
      activeCameraCount: connectedCamsCount,
      totalCameraSlots: 4,
      fps: currentFps,
      latencyMs: telemetry?.latencyMetrics?.total_ms ?? 0,
      schedulerStatus: !isConnected ? 'DISCONNECTED' : telemetry?.systemRunning ? pipelineHealthy ? 'RUNNING' : 'WAITING FOR FRAMES' : 'PAUSED',
    };

    // Phase ViewModel
    const activePhase: PhaseViewModel = {
      activeDirection: pipelineHealthy ? telemetry?.activePhase || 'None' : 'None',
      remainingSeconds: remainingTime,
      progressPercentage: progressPct,
      phaseReason: telemetry?.signalState === 'YELLOW' ? 'Yellow clearance' : telemetry?.phaseReason || 'Waiting for a connected camera',
    };

    // MetricStrip ViewModel
    const metrics: MetricStripViewModel = {
      totalVehicles: telemetry?.totalVehicles ?? 0,
      avgFps: currentFps,
      inferenceTimeMs: telemetry?.latencyMetrics?.yolo_ms ?? 0,
      processingQueueLength: telemetry?.stageCounters?.dropped ?? 0,
      pipelineLatencyMs: telemetry?.latencyMetrics?.total_ms || telemetry?.frameAgeMs || 0,
      frameAgeMs,
      connectionHealth: !isConnected ? 'DISCONNECTED' : pipelineHealthy ? 'HEALTHY' : 'DEGRADED',
    };

    return {
      lanes: lanesList,
      activePhase,
      statusBar,
      metrics,
    };
  }, [telemetry, isConnected, streamStatus, frameAgeMs, pipelineHealthy, lastUpdated, health, mobileNodes, activePhaseName, remainingTime, greenDuration, progressPct]);
};
