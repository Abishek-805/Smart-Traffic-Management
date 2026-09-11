"""
ESP32Interface manages physical or simulated serial communications with ESP32 signal hardware controllers.
"""

from dataclasses import dataclass
from enum import Enum
import time
from typing import Optional, Dict, Any

from ai.hardware.command_encoder import CommandEncoder
from ai.signal.signal_types import HardwareCommand
from ai.utils.logger import get_logger

logger = get_logger("ESP32Interface")


class HardwareConnectionState(str, Enum):
    """Truthful lifecycle states for simulated and serial control output."""

    SIMULATION = "SIMULATION"
    CONNECTING = "CONNECTING"
    CONNECTED = "CONNECTED"
    DISCONNECTED = "DISCONNECTED"
    ERROR = "ERROR"

# Safe PySerial import fallback
try:
    import serial  # type: ignore
except ImportError:
    serial = None


@dataclass
class HardwareStatus:
    """
    Strongly-typed status telemetry container for ESP32 hardware interface.
    """
    connected: bool = False
    simulation_mode: bool = True
    port: str = "SIMULATION"
    baudrate: int = 115200
    connection_state: HardwareConnectionState = HardwareConnectionState.SIMULATION
    last_ack_time: Optional[float] = None
    last_ack: Optional[str] = None
    last_error: Optional[str] = None
    total_commands_sent: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "connected": self.connected,
            "simulation_mode": self.simulation_mode,
            "port": self.port,
            "baudrate": self.baudrate,
            "connection_state": self.connection_state.value,
            "last_ack_time": round(self.last_ack_time, 3) if self.last_ack_time is not None else None,
            "last_ack": self.last_ack,
            "last_error": self.last_error,
            "total_commands_sent": self.total_commands_sent,
        }


class ESP32Interface:
    """
    Non-blocking serial hardware communication interface for ESP32 microcontrollers.
    Simulation is explicit; requested hardware failures remain visible and fail closed.
    """

    def __init__(
        self,
        port: Optional[str] = None,
        baudrate: int = 115200,
        simulation_mode: bool = True,
    ):
        self.port = port
        self.baudrate = baudrate
        self.simulation_mode = simulation_mode
        self.serial_conn: Optional[Any] = None

        self.status = HardwareStatus(
            connected=False,
            simulation_mode=self.simulation_mode,
            port=self.port if self.port else "SIMULATION",
            baudrate=self.baudrate,
            connection_state=(HardwareConnectionState.SIMULATION if self.simulation_mode
                              else HardwareConnectionState.DISCONNECTED),
        )

        # Attempt connection
        if not self.simulation_mode:
            self.connect()
        else:
            logger.info("ESP32Interface running in SIMULATION MODE (hardware commands logged safely).")

    def connect(self) -> bool:
        """Attempt non-blocking connection to PySerial COM port."""
        if self.simulation_mode:
            self.status.connection_state = HardwareConnectionState.SIMULATION
            return False
        self.status.connection_state = HardwareConnectionState.CONNECTING
        self.status.last_error = None
        if serial is None or not self.port:
            self.status.connected = False
            self.status.connection_state = HardwareConnectionState.ERROR
            self.status.last_error = (
                "PySerial is unavailable" if serial is None else "ESP32 serial port is not configured"
            )
            return False

        try:
            logger.info(f"Connecting to ESP32 hardware on port '{self.port}' @ {self.baudrate} baud...")
            self.serial_conn = serial.Serial(self.port, self.baudrate, timeout=0.1)
            time.sleep(1.0)  # Reset delay for microcontrollers
            if self.serial_conn.is_open:
                self.status.connected = True
                self.status.simulation_mode = False
                self.status.connection_state = HardwareConnectionState.CONNECTED
                self.status.last_error = None
                logger.info(f"✅ ESP32 serial interface connected successfully on '{self.port}'.")
                return True
        except Exception as e:
            self.status.connected = False
            self.status.simulation_mode = False
            self.status.connection_state = HardwareConnectionState.ERROR
            self.status.last_error = str(e)
            logger.warning(
                f"⚠️ Could not open serial port '{self.port}' ({e}). "
                "Requested hardware remains unavailable; traffic output must stay safe."
            )
        return False

    def reconnect(self) -> bool:
        """Close stale serial state and retry the explicitly configured device."""
        if self.serial_conn is not None:
            try:
                self.serial_conn.close()
            except Exception as exc:
                logger.debug("Error closing stale ESP32 connection before reconnect: %s", exc)
            finally:
                self.serial_conn = None
        self.status.connected = False
        return self.connect()

    def send_command(self, cmd: HardwareCommand) -> bool:
        """
        Send a HardwareCommand to the ESP32 hardware or simulation layer.
        Non-blocking execution ensures AI loop never stalls.
        """
        packet_str = CommandEncoder.encode_serial(cmd)
        json_pkt = CommandEncoder.encode_json(cmd)

        self.status.total_commands_sent += 1

        if self.status.simulation_mode:
            logger.info(f"💻 [ESP32 SIMULATED TRANSMISSION] {packet_str}")
            return True

        if self.serial_conn and self.serial_conn.is_open:
            try:
                # Write command string over serial
                tx_data = (packet_str + "\n").encode("utf-8")
                self.serial_conn.write(tx_data)
                self.serial_conn.flush()

                # Non-blocking ACK read
                ack = self.serial_conn.readline().decode("utf-8", errors="ignore").strip()
                if ack:
                    self.status.last_ack_time = time.time()
                    self.status.last_ack = ack
                    self.status.connected = True
                    self.status.connection_state = HardwareConnectionState.CONNECTED
                    logger.info(f"🔌 [ESP32 Hardware ACK] Received: '{ack}' for command: {packet_str}")
                else:
                    logger.info(f"🔌 [ESP32 Hardware Sent] Packet transmitted: '{packet_str}' (No immediate ACK)")

                return True
            except Exception as e:
                self.status.last_error = str(e)
                self.status.connected = False
                self.status.connection_state = HardwareConnectionState.ERROR
                logger.error(f"❌ Serial write error on port '{self.port}': {e}. Hardware output disabled.")
                return False
        self.status.connected = False
        if self.status.connection_state != HardwareConnectionState.ERROR:
            self.status.connection_state = HardwareConnectionState.DISCONNECTED
        self.status.last_error = self.status.last_error or "ESP32 serial connection is unavailable"
        logger.error("ESP32 command rejected: %s", self.status.last_error)
        return False

    def get_status(self) -> HardwareStatus:
        """Return strongly-typed HardwareStatus container."""
        return self.status

    def close(self) -> None:
        """Close serial connection cleanly."""
        if self.serial_conn is not None:
            try:
                self.serial_conn.close()
            except Exception as e:
                logger.error(f"Error closing serial port: {e}")
            finally:
                self.serial_conn = None
        self.status.connected = False
        self.status.connection_state = HardwareConnectionState.DISCONNECTED
        logger.info("ESP32Interface shut down cleanly.")


def hardware_is_safe_to_run(status: HardwareStatus) -> bool:
    """Return whether the configured output is deliberately usable."""
    return status.connection_state in {
        HardwareConnectionState.SIMULATION,
        HardwareConnectionState.CONNECTED,
    }
