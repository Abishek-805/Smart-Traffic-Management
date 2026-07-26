"""
Unit test suite for startup/ package: StartupManager, StartupConfig, RuntimeConfig, DebugConfig, ConfigValidator, ProfileManager, and Port Discovery.
"""

import unittest
from pathlib import Path
import tempfile
import json

from startup import (
    StartupManager,
    StartupConfig,
    CameraConfig,
    HardwareConfig,
    RuntimeConfig,
    DebugConfig,
    ConfigValidator,
    load_profile,
    save_profile,
    run_startup_wizard,
    discover_com_ports,
)


class TestStartupPackage(unittest.TestCase):
    """Test suite for startup configuration dataclasses, validation, and profile persistence."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_file = Path(self.temp_dir.name) / "runtime_config.json"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_01_startup_config_dataclasses(self):
        """Test StartupConfig, CameraConfig, HardwareConfig, RuntimeConfig serialization."""
        cam_cfg = CameraConfig(
            mode="mobile",
            sources={
                "north": "http://192.168.1.50:8080/video",
                "south": "http://192.168.1.51:8080/video",
                "east": "http://192.168.1.52:8080/video",
                "west": "http://192.168.1.53:8080/video",
            },
        )
        hw_cfg = HardwareConfig(port="COM5", simulation=False, baudrate=115200)
        rt_cfg = RuntimeConfig(show_dashboard=True, save_output_video=True)
        dbg_cfg = DebugConfig(debug_mode=False)

        startup_cfg = StartupConfig(
            version=1,
            camera=cam_cfg,
            hardware=hw_cfg,
            runtime=rt_cfg,
            debug=dbg_cfg,
        )

        d = startup_cfg.to_dict()
        self.assertEqual(d["version"], 1)
        self.assertEqual(d["camera"]["mode"], "mobile")
        self.assertEqual(d["hardware"]["port"], "COM5")
        self.assertTrue(d["runtime"]["show_dashboard"])

        reconstructed = StartupConfig.from_dict(d)
        self.assertEqual(reconstructed.version, 1)
        self.assertEqual(reconstructed.camera.mode, "mobile")
        self.assertEqual(reconstructed.hardware.port, "COM5")
        self.assertTrue(reconstructed.runtime.show_dashboard)

    def test_02_config_validator(self):
        """Test ConfigValidator validating camera and hardware configurations."""
        cam_cfg = CameraConfig(mode="usb", sources={"north": 0, "south": 1, "east": 2, "west": 3})
        startup_cfg = StartupConfig(camera=cam_cfg)

        is_valid, issues = ConfigValidator.validate(startup_cfg)
        self.assertTrue(is_valid)
        self.assertEqual(len(issues), 0)

        # Invalid camera configuration
        bad_cfg = StartupConfig(camera=CameraConfig(sources={"north": 0}))
        is_valid, issues = ConfigValidator.validate(bad_cfg)
        self.assertFalse(is_valid)

    def test_03_profile_manager_versioning(self):
        """Test profile saving, version check, and loading."""
        cam_cfg = CameraConfig(mode="usb", sources={"north": 0, "south": 1, "east": 2, "west": 3})
        hw_cfg = HardwareConfig(port="COM3", simulation=False)
        original = StartupConfig(version=1, camera=cam_cfg, hardware=hw_cfg)

        success = save_profile(original, config_path=self.config_file)
        self.assertTrue(success)
        self.assertTrue(self.config_file.exists())

        loaded = load_profile(config_path=self.config_file)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.version, 1)
        self.assertEqual(loaded.camera.mode, "usb")
        self.assertEqual(loaded.hardware.port, "COM3")

    def test_04_startup_manager_non_interactive(self):
        """Test StartupManager.run in non-interactive mode."""
        config = StartupManager.run(interactive=False)
        self.assertIsNotNone(config)
        self.assertIsInstance(config, StartupConfig)
        self.assertIn("north", config.camera.sources)

    def test_05_com_port_discovery(self):
        """Test discover_com_ports returns a list."""
        ports = discover_com_ports()
        self.assertIsInstance(ports, list)


if __name__ == "__main__":
    unittest.main()
