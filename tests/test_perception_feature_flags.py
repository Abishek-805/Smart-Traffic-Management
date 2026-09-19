from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from ai.experiments.perception_registry import (
    PerceptionRegistry,
    UnqualifiedFeatureError,
)
from config.perception_features import load_perception_features
from web.app import app


FEATURES = (
    "speed_estimation",
    "stopped_vehicle_detection",
    "lane_segmentation",
    "additional_vehicle_classes",
)


def test_all_unvalidated_perception_features_are_disabled_by_default():
    flags = load_perception_features({})

    assert all(not getattr(flags, name) for name in FEATURES)


def test_feature_flag_parser_is_strict():
    with pytest.raises(ValueError, match="boolean"):
        load_perception_features({"PERCEPTION_LANE_SEGMENTATION": "sometimes"})


def test_enabling_feature_without_evidence_is_rejected():
    registry = PerceptionRegistry(FEATURES)

    with pytest.raises(UnqualifiedFeatureError):
        registry.enable("lane_segmentation", evidence_path=None, resource_evidence_path=None)


def test_feature_with_both_evidence_files_is_experimental_until_qualified(tmp_path):
    accuracy = tmp_path / "accuracy.json"
    resources = tmp_path / "resources.json"
    accuracy.write_text("{}", encoding="utf-8")
    resources.write_text("{}", encoding="utf-8")
    registry = PerceptionRegistry(FEATURES)

    feature = registry.enable("additional_vehicle_classes", accuracy, resources)

    assert feature.enabled
    assert feature.status == "experimental"


def test_unknown_feature_is_rejected():
    registry = PerceptionRegistry(FEATURES)

    with pytest.raises(KeyError):
        registry.enable("emergency_vehicle_detection", "accuracy.json", "resources.json")


def test_status_endpoint_redacts_evidence_paths():
    response = TestClient(app).get("/api/v1/perception/features")

    assert response.status_code == 200
    features = response.json()["data"]["features"]
    assert {item["name"] for item in features} == set(FEATURES)
    assert all(item["status"] == "disabled" for item in features)
    assert all("evidence_path" not in item for item in features)
    assert "emergency_vehicle_detection" not in {item["name"] for item in features}


def test_status_endpoint_reports_evidence_backed_experiment(monkeypatch, tmp_path):
    accuracy = tmp_path / "accuracy.json"
    resources = tmp_path / "resources.json"
    accuracy.write_text("{}", encoding="utf-8")
    resources.write_text("{}", encoding="utf-8")
    monkeypatch.setenv("PERCEPTION_LANE_SEGMENTATION", "true")
    monkeypatch.setenv("PERCEPTION_LANE_SEGMENTATION_EVIDENCE", str(accuracy))
    monkeypatch.setenv("PERCEPTION_LANE_SEGMENTATION_RESOURCE_EVIDENCE", str(resources))

    response = TestClient(app).get("/api/v1/perception/features")

    lane = next(item for item in response.json()["data"]["features"] if item["name"] == "lane_segmentation")
    assert lane == {
        "name": "lane_segmentation",
        "enabled": True,
        "status": "experimental",
        "accuracyEvidenceAvailable": True,
        "resourceEvidenceAvailable": True,
    }
