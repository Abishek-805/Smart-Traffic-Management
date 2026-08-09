"""
SessionManager tracks active camera node sessions, tokens, heartbeats, and session timeouts.
"""

from dataclasses import dataclass, field
import time
import uuid
from typing import Dict, Optional, List, Any

from server.config import HEARTBEAT_TIMEOUT_SEC
from ai.utils.logger import get_logger

logger = get_logger("SessionManager")


@dataclass
class NodeSession:
    """
    Data model representing an active camera node WebSocket session.
    """
    node_id: str
    session_token: str
    camera_direction: str
    connected_at: float = field(default_factory=time.time)
    last_heartbeat: float = field(default_factory=time.time)
    heartbeat_timeout_sec: float = HEARTBEAT_TIMEOUT_SEC

    def is_expired(self, now: Optional[float] = None) -> bool:
        """Check if the session has exceeded the heartbeat timeout threshold."""
        current_time = now if now is not None else time.time()
        return (current_time - self.last_heartbeat) > self.heartbeat_timeout_sec


class SessionManager:
    """
    Manages active camera node sessions, session tokens, and heartbeat timestamps.
    """

    def __init__(self, timeout_sec: float = HEARTBEAT_TIMEOUT_SEC):
        self.sessions: Dict[str, NodeSession] = {}
        self.pairing_sessions: Dict[str, Dict[str, Any]] = {}
        self.timeout_sec = timeout_sec

    def create_session(self, node_id: str, camera_direction: str) -> NodeSession:
        """
        Create a new camera node session with a secure UUID token.
        If node_id already exists or another node claimed the direction, old session is evicted.
        """
        dir_clean = (camera_direction or "north").lower()
        
        # Evict existing node registered under the same camera direction to prevent frame contention
        existing = self.get_session_by_direction(dir_clean)
        if existing and existing.node_id != node_id:
            logger.warning(f"Direction slot '{dir_clean}' claimed by new node '{node_id}'. Evicting previous node '{existing.node_id}'.")
            self.remove_session(existing.node_id)

        if node_id in self.sessions:
            logger.warning(f"Node '{node_id}' re-registered. Overwriting existing session.")

        session_token = str(uuid.uuid4())
        now = time.time()
        session = NodeSession(
            node_id=node_id,
            session_token=session_token,
            camera_direction=dir_clean,
            connected_at=now,
            last_heartbeat=now,
            heartbeat_timeout_sec=self.timeout_sec,
        )
        self.sessions[node_id] = session
        logger.info(f"Created session for node '{node_id}' ({dir_clean.upper()}). Token: {session_token}")
        return session

    def get_session_by_direction(self, camera_direction: str) -> Optional[NodeSession]:
        """Find active unexpired session for a given camera direction."""
        dir_clean = (camera_direction or "north").lower()
        now = time.time()
        for sess in self.sessions.values():
            if sess.camera_direction.lower() == dir_clean and not sess.is_expired(now=now):
                return sess
        return None

    def validate_session(self, node_id: str, session_token: str) -> bool:
        """Verify node_id exists and session_token matches."""
        session = self.sessions.get(node_id)
        if not session:
            return False
        return session.session_token == session_token

    def update_heartbeat(self, node_id: str, session_token: str) -> bool:
        """Update last_heartbeat timestamp for valid session."""
        if not self.validate_session(node_id, session_token):
            return False
        self.sessions[node_id].last_heartbeat = time.time()
        return True

    def remove_session(self, node_id: str) -> Optional[NodeSession]:
        """Remove and return session for node_id."""
        session = self.sessions.pop(node_id, None)
        if session:
            logger.info(f"Removed session for node '{node_id}'.")
        return session

    def get_session(self, node_id: str) -> Optional[NodeSession]:
        """Retrieve active NodeSession."""
        return self.sessions.get(node_id)

    def get_expired_sessions(self) -> List[str]:
        """Return list of node_ids that have timed out."""
        now = time.time()
        return [nid for nid, sess in self.sessions.items() if sess.is_expired(now=now)]

    def cleanup_expired_sessions(self) -> List[str]:
        """Remove all expired sessions and return their node_ids."""
        expired = self.get_expired_sessions()
        for nid in expired:
            self.remove_session(nid)
        return expired

    def register_pairing_session(self, direction: str, session_id: str, expires_at: float):
        """Register a pairing session for a camera direction."""
        dir_clean = (direction or "north").lower()
        self.pairing_sessions[dir_clean] = {
            "session_id": session_id,
            "expires_at": expires_at,
        }
        logger.info(f"Registered pairing session for {dir_clean.upper()}. ID: {session_id}, Expires at: {expires_at}")

    def get_pairing_session(self, direction: str) -> Optional[Dict[str, Any]]:
        """Retrieve pairing session details if valid and not expired."""
        dir_clean = (direction or "north").lower()
        sess = self.pairing_sessions.get(dir_clean)
        if not sess:
            return None
        if time.time() > sess["expires_at"]:
            logger.info(f"Pairing session for {dir_clean.upper()} has expired.")
            self.clear_pairing_session(dir_clean)
            return None
        return sess

    def clear_pairing_session(self, direction: str):
        """Clear pairing session for a camera direction."""
        dir_clean = (direction or "north").lower()
        self.pairing_sessions.pop(dir_clean, None)
        logger.info(f"Cleared pairing session for {dir_clean.upper()}.")

    def validate_pairing_session(self, direction: str, token: str) -> bool:
        """Validate if a token matches the active pairing session for a camera direction."""
        sess = self.get_pairing_session(direction)
        if not sess:
            return False
        return sess["session_id"] == token
