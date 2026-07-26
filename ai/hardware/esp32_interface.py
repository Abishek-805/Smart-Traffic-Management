"""
ESP32Interface manages physical or simulated serial communications with ESP32 signal hardware controllers.
"""

from dataclasses import dataclass, field
import time
from typing import Optional, Dict, Any

from ai.hardware.command_encoder import CommandEncoder
from ai.signal.signal_types import HardwareCommand
from ai.utils.logger import get_logger

logger = get_logger("ESP32Interface")

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
    port: str = "COM3 (SIMULATED)"
    baudrate: int = 115200
    last_ack_time: float = 0.0
    last_error: Optional[str] = None
    total_commands_sent: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "connected": self.connected,
            "simulation_mode": self.simulation_mode,
            "port": self.port,
            "baudrate": self.baudrate,
            "last_ack_time": round(self.last_ack_time, 3),
            "last_error": self.last_error,
            "total_commands_sent": self.total_commands_sent,
        }


class ESP32Interface:
    """
    Non-blocking serial hardware communication interface for ESP32 microcontrollers.
    Falls back gracefully to SIMULATION MODE if no physical COM port is connected.
    """

    def __init__(
        self,
        port: Optional[str] = None,
        baudrate: int = 115200,
        simulation_mode: bool = True,
    ):
        self.port = port
        self.baudrate = baudrate
        self.simulation_mode = simulation_mode or (port is None) or (serial is None)
        self.serial_conn: Optional[Any] = None

        self.status = HardwareStatus(
            connected=False,
            simulation_mode=self.simulation_mode,
            port=self.port if self.port else "COM3 (SIMULATED)",
            baudrate=self.baudrate,
        )

        # Attempt connection
        if not self.simulation_mode and self.port:
            self.connect()
        else:
            logger.info("ESP32Interface running in SIMULATION MODE (hardware commands logged safely).")

    def connect(self) -> bool:
        """Attempt non-blocking connection to PySerial COM port."""
        if serial is None or not self.port:
            self.status.simulation_mode = True
            self.status.connected = False
            return False

        try:
            logger.info(f"Connecting to ESP32 hardware on port '{self.port}' @ {self.baudrate} baud...")
            self.serial_conn = serial.Serial(self.port, self.baudrate, timeout=0.1)
            time.sleep(1.0)  # Reset delay for microcontrollers
            if self.serial_conn.is_open:
                self.status.connected = True
                self.status.simulation_mode = False
                self.status.last_error = None
                logger.info(f"✅ ESP32 serial interface connected successfully on '{self.port}'.")
                return True
        except Exception as e:
            self.status.connected = False
            self.status.simulation_mode = True
            self.status.last_error = str(e)
            logger.warning(
                f"⚠️ Could not open serial port '{self.port}' ({e}). "
                f"Falling back to SIMULATION MODE."
            )
        return False

    def send_command(self, cmd: HardwareCommand) -> bool:
        """
        Send a HardwareCommand to the ESP32 hardware or simulation layer.
        Non-blocking execution ensures AI loop never stalls.
        """
        packet_str = CommandEncoder.encode_serial(cmd)
        json_pkt = CommandEncoder.encode_json(cmd)

        self.status.total_commands_sent += 1

        if not self.status.simulation_mode and self.serial_conn and self.serial_conn.is_open:
            try:
                # Write command string over serial
                tx_data = (packet_str + "\n").encode("utf-8")
                self.serial_conn.write(tx_data)
                self.serial_conn.flush()

                # Non-blocking ACK read
                ack = self.serial_conn.readline().decode("utf-8", errors="ignore").strip()
                if ack:
                    self.status.last_ack_time = time.time()
                    logger.info(f"🔌 [ESP32 Hardware ACK] Received: '{ack}' for command: {packet_str}")
                else:
                    logger.info(f"🔌 [ESP32 Hardware Sent] Packet transmitted: '{packet_str}' (No immediate ACK)")

                return True
            except Exception as e:
                self.status.last_error = str(e)
                self.status.connected = False
                logger.error(f"❌ Serial write error on port '{self.port}': {e}. Switching to Simulation Mode.")
                self.status.simulation_mode = True
                return False
        else:
            # Simulation Mode logging
            self.status.last_ack_time = time.time()
            logger.info(f"💻 [ESP32 SIMULATED TRANSMISSION] {packet_str}")
            return True

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
        logger.info("ESP32Interface shut down cleanly.")
