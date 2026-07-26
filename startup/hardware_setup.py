"""
HardwareSetup wizard for auto-discovering serial COM ports and selecting physical ESP32 hardware or Simulation Mode.
"""

from typing import List, Tuple, Optional
from startup.startup_config import HardwareConfig
from ai.utils.logger import get_logger

logger = get_logger("HardwareSetup")

try:
    import serial.tools.list_ports  # type: ignore
except ImportError:
    serial = None


def discover_com_ports() -> List[Tuple[str, str]]:
    """
    Discover active serial COM ports on the host system.

    Returns:
        List of tuples: [(port_name, description), ...]
    """
    if serial is None or not hasattr(serial.tools, "list_ports"):
        return []

    try:
        ports = serial.tools.list_ports.comports()
        return [(p.device, p.description) for p in ports]
    except Exception as e:
        logger.warning(f"Error discovering serial ports: {e}")
        return []


def setup_hardware_config() -> HardwareConfig:
    """
    Interactively prompt user to select detected ESP32 COM port or run in Simulation Mode.

    Returns:
        HardwareConfig object.
    """
    print("\n==================================================")
    print(" 🔌 SEARCHING FOR ESP32 HARDWARE CONTROLLER...")
    print("==================================================")

    ports = discover_com_ports()

    if not ports:
        print(" ⚠️  No physical COM ports detected on host system.")
        print(" 💡 Defaulting to SIMULATION MODE (hardware commands logged safely).\n")
        return HardwareConfig(port="COM3 (SIMULATED)", simulation=True)

    print(" Active COM Ports Discovered:")
    for idx, (port_name, desc) in enumerate(ports, start=1):
        print(f"  {idx}) {port_name:<10} - {desc}")
    print(f"  {len(ports) + 1}) Simulation Mode (Virtual Hardware)")
    print("==================================================")

    try:
        choice = input(f"Select option [1-{len(ports) + 1}] (default: 1): ").strip()
    except (EOFError, KeyboardInterrupt):
        choice = "1"

    if choice.isdigit():
        sel_idx = int(choice)
        if 1 <= sel_idx <= len(ports):
            selected_port, desc = ports[sel_idx - 1]
            print(f"✅ Selected physical ESP32 port: '{selected_port}' ({desc})\n")
            return HardwareConfig(port=selected_port, simulation=False)

    print("💻 Selected SIMULATION MODE (Virtual Hardware).\n")
    return HardwareConfig(port="COM3 (SIMULATED)", simulation=True)
