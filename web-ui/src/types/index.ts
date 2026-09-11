/**
 * Master TypeScript Interfaces for Smart Traffic Control Center.
 * Mirrors backend Pydantic contracts and WS event definitions.
 */

// Standard API Response Envelope
export interface ApiResponse<T> {
  success: boolean;
  timestamp: string;
  data?: T;
  error?: {
    code: string;
    message: string;
  };
}

// Operational & System
export interface SystemVersionInfo {
  version: string;
  backend: string;
  frontend: string;
  protocol: string;
  build_date: string;
}

export interface ComponentHealth {
  status: 'HEALTHY' | 'DEGRADED' | 'UNHEALTHY';
  message: string;
  connected?: boolean;
  simulation?: boolean;
  running?: boolean;
  fps?: number;
  active?: number;
  model?: string;
  runtime?: string;
  input_size?: number;
  connection_state?: HardwareConnectionState;
  port?: string | null;
  baudrate?: number | null;
  last_ack_time?: number | null;
  last_ack?: string | null;
  last_error?: string | null;
}

export type HardwareConnectionState = 'SIMULATION' | 'CONNECTING' | 'CONNECTED' | 'DISCONNECTED' | 'ERROR';

export interface SystemHealthData {
  system_status: 'RUNNING' | 'STOPPED' | 'ERROR';
  operating_mode: 'AUTOMATIC' | 'MANUAL_OVERRIDE' | 'EMERGENCY_OVERRIDE';
  uptime_seconds: number;
  liveness: boolean;
  readiness: boolean;
  cpu_percent?: number | null;
  memory_used_gb?: number | null;
  memory_total_gb?: number | null;
  frame_processing_errors?: number;
  inference_latency_ms?: number | null;
  stage_counters?: Record<string, number>;
  components: Record<string, ComponentHealth>;
}

// Telemetry WebSocket Contract
export type TelemetryEventType =
  | 'SystemStatusUpdated'
  | 'SignalPhaseChanged'
  | 'AnalyticsUpdated'
  | 'NodeConnected'
  | 'NodeDisconnected'
  | 'LogEntry';

export interface LaneTelemetryItem {
  frameAgeMs?: number | null;
  streamStatus?: 'CONNECTING' | 'LIVE' | 'STALE' | 'OFFLINE' | 'DISCONNECTED';
  fps?: number;
  inferenceTimeMs?: number;
  serverProcessingMs?: number;
  queueWaitMs?: number;
  frameId?: string | null;
  latestFrameId?: string | null;
  lastDetectionFrameId?: string | null;
  lastPredictionFrameId?: string | null;
  lastTrackedFrameId?: string | null;
  detectorRan?: boolean;
  detectorFps?: number;
  trackerFps?: number;
  trackingTimeMs?: number;
  vehicles: number;
  queue: number;
  wait: number;
  pce: number;
  density: number | string;
  priority: number;
}

export interface TelemetryPayload {
  systemRunning?: boolean;
  signalState?: 'GREEN' | 'YELLOW' | 'ALL_RED';
  phaseReason?: string;
  activePhase: string;
  greenDuration: number;
  timeRemaining: number;
  totalVehicles: number;
  detectedVehicles?: number;
  assignedVehicles?: number;
  queueLength: number;
  pceScore: number;
  operatingMode: 'AUTOMATIC' | 'MANUAL_OVERRIDE' | 'EMERGENCY_OVERRIDE';
  snapshotTimestamp?: number;
  captureTimestamp?: number;
  uploadTimestamp?: number;
  backendReceiveTimestamp?: number;
  decodeTimestamp?: number;
  inferenceTimestamp?: number;
  schedulerTimestamp?: number;
  broadcastTimestamp?: number;
  dashboardReceiveTimestamp?: number;
  dashboardRenderTimestamp?: number;
  lastFrameTimestamp?: number;
  frameAgeMs?: number;
  pipelineHealthy?: boolean;
  pipelineStalled?: boolean;
  streamStatus?: 'CONNECTING' | 'LIVE' | 'STALE' | 'DISCONNECTED';
  processingErrors?: number;
  stageCounters?: {
    received?: number;
    decoded?: number;
    decode_failed?: number;
    processed?: number;
    dropped?: number;
  };
  lanes?: Record<string, LaneTelemetryItem>;
  latencyMetrics?: {
    frame_id?: number;
    timestamp?: number;
    yolo_ms?: number;
    total_ms?: number;
  };
}

export interface TelemetryMessage {
  protocol: string;
  type: TelemetryEventType;
  timestamp: number;
  payload: TelemetryPayload;
}

// Cameras
export interface CameraConfigItem {
  source: string;
  status: string;
  fps: number;
  latency_ms: number;
}

export interface CameraConfigResponse {
  mode: string;
  streams: Record<string, CameraConfigItem>;
}

// Mobile Nodes
export interface NodeHealthSummary {
  connected_nodes: number;
  offline_nodes: number;
  average_fps: number;
  average_latency_ms: number;
  average_battery_pct: number;
  average_signal_dbm: number;
}

export interface MobileNodeItem {
  node_id: string;
  name: string;
  status: 'CONNECTED' | 'DISCONNECTED' | 'PAIRING' | 'PAIRED' | 'OFFLINE';
  fps: number;
  latency_ms: number;
  battery_pct: number;
  signal_dbm: number;
  last_seen: string;
  assigned_lane: string;
  expires_at?: number;
}

export interface MobileNodesData {
  summary: NodeHealthSummary;
  nodes: MobileNodeItem[];
}

// Analytics
export interface HourlyFlowPoint {
  hour: string;
  north: number;
  south: number;
  east: number;
  west: number;
}

export interface QueueTrendPoint {
  time: string;
  avgQueueLength: number;
  maxQueueLength: number;
}

export interface VehicleSplitItem {
  category: string;
  count: number;
  percentage: number;
}

export interface PhaseEfficiencyItem {
  phase: string;
  score: number;
  fairness: number;
}

export interface AnalyticsSummaryData {
  total_vehicles_today: number;
  avg_wait_time_sec: number;
  peak_pce_score: number;
  efficiency_score: number | null;
  hourly_flow: HourlyFlowPoint[];
  queue_trends: QueueTrendPoint[];
  vehicle_split: VehicleSplitItem[];
  phase_efficiency: PhaseEfficiencyItem[];
}

// Logs
export type LogCategory = 'ALL' | 'INFO' | 'WARNING' | 'ERROR' | 'AI' | 'NODE' | 'ESP32' | 'SYSTEM';

export interface LogEntryItem {
  id: string;
  timestamp: string;
  level: 'INFO' | 'WARNING' | 'ERROR';
  category: LogCategory;
  component: string;
  message: string;
  metadata: Record<string, any>;
}

export interface LogsResponseData {
  total: number;
  logs: LogEntryItem[];
}

// User Settings
export interface UserSettings {
  theme: 'dark' | 'light' | 'system';
  confidenceThreshold: number;
  minGreenTime: number;
  maxGreenTime: number;
  autoRefreshRate: number;
  enableNotifications: boolean;
}
