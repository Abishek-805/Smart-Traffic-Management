"""
StartupManager orchestrates the complete system startup sequence: ASCII banner display,
profile version validation, camera & hardware wizards, configuration validation, and Startup Summary rendering.
"""

import sys
from typing import Optional
from startup.banner import display_banner
from startup.startup_config import StartupConfig, CameraConfig, HardwareConfig
from startup.camera_setup import setup_camera_config
from startup.hardware_setup import setup_hardware_config
from startup.profile_manager import load_profile, save_profile, prompt_use_existing_profile
from startup.validator import ConfigValidator
from ai.utils.logger import get_logger

logger = get_logger("StartupManager")


class StartupManager:
    """
    Centralized startup orchestrator isolating user interaction and setup wizards
    from lower-level video acquisition and hardware communication modules.
    """

    @classmethod
    def run(cls, interactive: bool = True) -> StartupConfig:
        """
        Execute startup sequence and return validated StartupConfig object.

        Args:
            interactive: If True, prompt user interactively; if False, load or return default demo config.

        Returns:
            StartupConfig: Validated system configuration object.
        """
        display_banner()

        if not interactive:
            existing = load_profile()
            cfg = existing if existing is not None else StartupConfig()
            ConfigValidator.validate(cfg)
            return cfg

        # 1. Profile Reuse Check
        existing_profile = load_profile()
        if existing_profile is not None:
            if prompt_use_existing_profile(existing_profile):
                is_valid, issues = ConfigValidator.validate(existing_profile)
                if is_valid:
                    cls._display_startup_summary(existing_profile)
                    cls._wait_for_user_acknowledgement()
                    return existing_profile
                else:
                    logger.warning("Existing profile contained validation issues. Launching setup wizard...")

        # 2. Interactive Setup Wizards
        cam_cfg = setup_camera_config()
        hw_cfg = setup_hardware_config()

        config = StartupConfig(version=1, camera=cam_cfg, hardware=hw_cfg)

        # 3. Save Runtime Profile
        save_profile(config)

        # 4. Configuration Validation
        is_valid, issues = ConfigValidator.validate(config)
        if not is_valid:
            print("\n❌ Configuration errors detected:")
            for issue in issues:
                print(f"   • {issue}")
            sys.exit(1)

        # 5. Display Startup Summary
        cls._display_startup_summary(config)
        cls._wait_for_user_acknowledgement()

        return config

    @staticmethod
    def _display_startup_summary(config: StartupConfig) -> None:
        """Display clear operational summary box prior to launching AI pipeline."""
        cam_mode = config.camera.mode.upper()
        hw_port = config.hardware.port if config.hardware.port else "None"
        hw_mode = "SIMULATED" if config.hardware.simulation else "HARDWARE"

        print("==================================================")
        print("     SMART TRAFFIC SYSTEM — CONFIGURATION SUMMARY")
        print("==================================================")
        print(f" Camera Mode : {cam_mode}")
        for lane, src in config.camera.sources.items():
            print(f"   • {lane.capitalize():<6} : {src}")
        print("--------------------------------------------------")
        print(f" ESP32 Port  : {hw_port} ({hw_mode})")
        print(f" Dashboard   : {'ENABLED' if config.runtime.show_dashboard else 'DISABLED'}")
        print(f" Save Video  : {'YES' if config.runtime.save_output_video else 'NO'}")
        print("==================================================")

    @staticmethod
    def _wait_for_user_acknowledgement() -> None:
        """Prompt user to press ENTER to start system."""
        try:
            input("\n🚀 Press ENTER to launch Traffic Pipeline...")
            print()
        except (EOFError, KeyboardInterrupt):
            pass
