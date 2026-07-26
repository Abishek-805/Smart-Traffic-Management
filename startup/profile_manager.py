"""
ProfileManager handles reading and writing versioned runtime configuration profiles (config/runtime_config.json)
to eliminate repetitive setup during live demonstrations and testing.
"""

import json
from pathlib import Path
from typing import Optional

from config.paths import RUNTIME_CONFIG_PATH
from startup.startup_config import StartupConfig
from ai.utils.logger import get_logger

logger = get_logger("ProfileManager")

CURRENT_PROFILE_VERSION = 1


def load_profile(config_path: Path = RUNTIME_CONFIG_PATH) -> Optional[StartupConfig]:
    """
    Attempt to load a previously saved StartupConfig profile from disk.
    Verifies profile version compatibility (current version: 1).
    """
    path = Path(config_path)
    if not path.exists() or path.stat().st_size == 0:
        return None

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        ver = data.get("version", 1)
        if ver != CURRENT_PROFILE_VERSION:
            logger.warning(
                f"Configuration profile version mismatch (Found v{ver}, expected v{CURRENT_PROFILE_VERSION}). "
                f"Re-running startup wizard..."
            )
            return None

        cfg = StartupConfig.from_dict(data)
        logger.info(f"Loaded existing runtime configuration profile (v{cfg.version}) from '{path}'.")
        return cfg
    except Exception as e:
        logger.warning(f"Could not parse configuration profile '{path}': {e}")
        return None


def save_profile(config: StartupConfig, config_path: Path = RUNTIME_CONFIG_PATH) -> bool:
    """
    Save active StartupConfig profile to disk.
    """
    path = Path(config_path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        config.version = CURRENT_PROFILE_VERSION
        with open(path, "w", encoding="utf-8") as f:
            json.dump(config.to_dict(), f, indent=4)
        logger.info(f"Saved runtime configuration profile (v{config.version}) to '{path}'.")
        return True
    except Exception as e:
        logger.error(f"Failed to save profile to '{path}': {e}")
        return False


def prompt_use_existing_profile(profile: StartupConfig) -> bool:
    """
    Display previously saved configuration summary and prompt user whether to reuse it.
    """
    print("\n--------------------------------------------------")
    print(f" 📋 Existing Configuration Profile Found (v{profile.version})")
    print("--------------------------------------------------")
    print(f" Camera Mode : {profile.camera.mode.upper()}")
    for lane, src in profile.camera.sources.items():
        print(f"   • {lane.capitalize():<6} : {src}")
    
    hw_port = profile.hardware.port if profile.hardware.port else "None"
    hw_mode = "SIMULATED" if profile.hardware.simulation else "HARDWARE"
    print(f" ESP32 Port  : {hw_port} ({hw_mode})")
    print(f" Dashboard   : {'ENABLED' if profile.runtime.show_dashboard else 'DISABLED'}")
    print("--------------------------------------------------")

    try:
        ans = input("\nUse previous configuration profile? [Y/n]: ").strip().lower()
        if ans in ("", "y", "yes"):
            print("✅ Using saved configuration profile.\n")
            return True
    except (EOFError, KeyboardInterrupt):
        pass

    print("⚙️  Starting interactive configuration wizard...\n")
    return False
