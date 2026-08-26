import time
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class RedisEventEnvelope(BaseModel):
    """Standardized message envelope for Redis Pub/Sub events."""
    event: str
    timestamp: float = Field(default_factory=time.time)
    data: Dict[str, Any]
    correlation_id: Optional[str] = None
