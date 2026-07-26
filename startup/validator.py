"""
ConfigValidator validates StartupConfig settings before initializing camera ingestion or AI pipelines.
Fails fast with actionable diagnostic messages if invalid camera sources or hardware parameters are detected.
"""

from typing import Tuple, List
from pathlib import Path
from startup.startup_config import StartupConfig
from ai.utils.logger import get_logger

logger = get_logger("ConfigValidator")


class ConfigValidator:
    """
    Validates StartupConfig settings prior to pipeline instantiation.
    """

    REQUIRED_LANES = ["north", "south", "east", "west"]

    @classmethod
    def validate(cls, config: StartupConfig) -> Tuple[bool, List[str]]:
        """
        Validate StartupConfig parameters.

        Returns:
            Tuple[bool, List[str]]: (is_valid, list_of_validation_messages)
        """
        issues: List[str] = []

        # 1. Validate Camera Configuration
        cam_cfg = config.camera
        sources = cam_cfg.sources

        for lane in cls.REQUIRED_LANES:
            if lane not in sources:
                issues.append(f"Missing camera stream source for direction '{lane}'.")

        if cam_cfg.mode == "demo":
            for lane, path_str in sources.items():
                if isinstance(path_str, str):
                    p = Path(path_str)
                    if not p.exists():
                        issues.append(f"Demo video file for '{lane}' does not exist at path: '{path_str}'.")

        elif cam_cfg.mode == "usb":
            indices = list(sources.values())
            if len(set(indices)) != len(indices) and len(indices) > 1:
                logger.warning(f"Multiple directions assigned identical USB camera indices: {indices}")

        elif cam_cfg.mode in ("mobile", "rtsp"):
            for lane, url_str in sources.items():
                if isinstance(url_str, str) and not (
                    url_str.startswith("http://")
                    or url_str.startswith("https://")
                    or url_str.startswith("rtsp://")
                ):
                    logger.warning(f"Camera stream URL for '{lane}' does not use http/rtsp schema: '{url_str}'")

        is_valid = len(issues) == 0
        if is_valid:
            logger.info("✅ StartupConfig validation successful! (All parameters valid)")
        else:
            for issue in issues:
                logger.error(f"❌ Configuration Validation Error: {issue}")

        return is_valid, issues
