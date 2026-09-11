"""Regression tests for authoritative laptop and Raspberry Pi runtime profiles."""

import importlib.util

import pytest


def test_deployment_profile_module_exists():
    """Removing the single profile source would split runtime configuration again."""
    assert importlib.util.find_spec("config.deployment") is not None


def test_laptop_profile_has_current_measured_software_defaults():
    from config.deployment import load_deployment_profile

    profile = load_deployment_profile({"TRAFFIC_PROFILE": "laptop"})

    assert profile.name == "LAPTOP"
    assert profile.validation_status == "MEASURED_LOCAL_SOFTWARE"
    assert profile.capture_fps == 4.0
    assert profile.webrtc_sample_fps == 4.0
    assert profile.detector_fps == 2.0
    assert profile.input_size == 576
    assert profile.batch_size == 4
    assert profile.cpu_threads == 4
    assert profile.preview_fps == 4.0


def test_raspberry_pi_profile_is_proposed_and_batch_one():
    from config.deployment import load_deployment_profile

    profile = load_deployment_profile({"TRAFFIC_PROFILE": "raspberry_pi"})

    assert profile.name == "RASPBERRY_PI"
    assert profile.validation_status == "PROPOSED_UNVALIDATED"
    assert profile.capture_fps == 2.0
    assert profile.webrtc_sample_fps == 2.0
    assert profile.detector_fps == 1.0
    assert profile.input_size == 512
    assert profile.batch_size == 1
    assert profile.cpu_threads == 4
    assert profile.preview_fps == 2.0


def test_ncnn_profile_forces_batch_one_despite_conflicting_override():
    from config.deployment import load_deployment_profile

    profile = load_deployment_profile({
        "TRAFFIC_PROFILE": "laptop",
        "YOLO_MODEL_NAME": "models/best_ncnn_model",
        "YOLO_BATCH_SIZE": "4",
    })

    assert profile.batch_size == 1


def test_unknown_deployment_profile_is_rejected():
    from config.deployment import load_deployment_profile

    with pytest.raises(ValueError, match="TRAFFIC_PROFILE"):
        load_deployment_profile({"TRAFFIC_PROFILE": "cloud_magic"})


def test_effective_profile_controls_all_frame_cadences():
    from config.deployment import load_deployment_profile
    from server.local_sources import LocalCameraSources
    from server.message_handler import MessageHandler
    from server.webrtc_ingest import WebRTCIngest
    from web.services.camera_service import CameraService

    profile = load_deployment_profile({
        "TRAFFIC_PROFILE": "raspberry_pi",
        "CAMERA_CAPTURE_FPS": "2.5",
        "WEBRTC_SAMPLE_FPS": "1.25",
        "PREVIEW_FPS": "5",
    })
    handler = MessageHandler()
    try:
        assert LocalCameraSources(handler, profile=profile).sample_interval == pytest.approx(0.4)
        assert WebRTCIngest(handler, profile=profile).sample_interval == pytest.approx(0.8)
        assert CameraService(profile=profile).preview_interval == pytest.approx(0.2)
    finally:
        handler.frame_executor.shutdown()


def test_model_warmup_and_inference_share_configured_batch(monkeypatch):
    from ai.models import model_manager as model_module

    class FakeModel:
        names = {2: "car"}

        def __init__(self):
            self.predict_calls = []

        def predict(self, **kwargs):
            self.predict_calls.append(kwargs)
            source = kwargs["source"]
            return [object() for _ in source] if isinstance(source, list) else [object()]

    fake_model = FakeModel()
    monkeypatch.setattr(model_module, "YOLO", lambda _target: fake_model)

    manager = model_module.ModelManager(
        model_name="models/best_ncnn_model",
        device="cpu",
        input_size=320,
        max_detections=10,
        batch_size=1,
    )

    assert len(fake_model.predict_calls[0]["source"]) == 1
    with pytest.raises(ValueError, match="configured batch size of 1"):
        manager.predict_batch([object(), object()])
