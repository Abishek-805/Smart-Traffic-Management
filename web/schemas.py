"""
Pydantic API contracts and schemas for Smart Traffic Management System REST API v1.
Separates API payload representations from internal domain models.
"""

from datetime import datetime
from typing import Generic, TypeVar, Optional, List, Dict, Any
from pydantic import BaseModel, Field

T = TypeVar("T")


# --- Standardized API Response Envelope ---

class ApiErrorDetail(BaseModel):
    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error explanation")


class ApiResponse(BaseModel, Generic[T]):
    success: bool = Field(True, description="Indicates if the request was successful")
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat() + "Z",
        description="ISO 8601 UTC timestamp",
    )
    data: Optional[T] = Field(None, description="Response payload data when successful")
    error: Optional[ApiErrorDetail] = Field(None, description="Error payload details when unsuccessful")


# --- Operational & System Schemas ---

class SystemVersionInfo(BaseModel):
    version: str = "1.0.0"
    backend: str = "FastAPI"
    frontend: str = "React"
    protocol: str = "1.0"
    build_date: str = "2026-07-25"


class ComponentHealth(BaseModel):
    status: str = "HEALTHY"  # HEALTHY, DEGRADED, UNHEALTHY
    message: str = "Operational"


class SystemHealthData(BaseModel):
    system_status: str = "RUNNING"  # RUNNING, STOPPED, ERROR
    operating_mode: str = "AUTOMATIC"  # AUTOMATIC, MANUAL_OVERRIDE, EMERGENCY_OVERRIDE
    uptime_seconds: float = 0.0
    liveness: bool = True
    readiness: bool = True
    components: Dict[str, ComponentHealth] = Field(default_factory=dict)


# --- Camera Schemas ---

class CameraConfigItem(BaseModel):
    direction: str
    camera_id: int
    fps: float
    resolution: str
    status: str  # ACTIVE, INACTIVE, ERROR
    url: Optional[str] = None


class CameraConfigResponse(BaseModel):
    cameras: Dict[str, CameraConfigItem]


# --- Mobile Node Schemas ---

class NodeHealthSummary(BaseModel):
    connected_nodes: int = 0
    offline_nodes: int = 0
    average_fps: float = 0.0
    average_latency_ms: float = 0.0
    average_battery_pct: float = 0.0
    average_signal_dbm: float = 0.0


class MobileNodeItem(BaseModel):
    node_id: str
    name: str
    status: str  # CONNECTED, DISCONNECTED, PAIRING
    fps: float
    latency_ms: float
    battery_pct: float
    signal_dbm: float
    last_seen: str


class MobileNodesData(BaseModel):
    summary: NodeHealthSummary
    nodes: List[MobileNodeItem]


# --- Analytics Schemas ---

class HourlyFlowPoint(BaseModel):
    hour: str
    north: int
    south: int
    east: int
    west: int


class QueueTrendPoint(BaseModel):
    time: str
    avgQueueLength: float
    maxQueueLength: float


class VehicleSplitItem(BaseModel):
    category: str
    count: int
    percentage: float


class PhaseEfficiencyItem(BaseModel):
    phase: str
    score: float
    fairness: float


class AnalyticsSummaryData(BaseModel):
    total_vehicles_today: int = 0
    avg_wait_time_sec: float = 0.0
    peak_pce_score: float = 0.0
    efficiency_score: float = 0.0
    hourly_flow: List[HourlyFlowPoint] = Field(default_factory=list)
    queue_trends: List[QueueTrendPoint] = Field(default_factory=list)
    vehicle_split: List[VehicleSplitItem] = Field(default_factory=list)
    phase_efficiency: List[PhaseEfficiencyItem] = Field(default_factory=list)


# --- Structured Logging Schemas ---

class LogEntryItem(BaseModel):
    id: str
    timestamp: str
    level: str  # INFO, WARNING, ERROR
    category: str  # INFO, WARNING, ERROR, AI, NODE, ESP32, SYSTEM
    component: str
    message: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class LogsResponseData(BaseModel):
    total: int
    logs: List[LogEntryItem]
