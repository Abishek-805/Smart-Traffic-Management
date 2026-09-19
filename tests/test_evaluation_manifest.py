import copy
import json
from pathlib import Path
import shutil

import pytest

from ai.evaluation.manifest import (
    ChecksumMismatch,
    EvaluationManifest,
    ManifestValidationError,
)


FIXTURES = Path(__file__).parent / "fixtures" / "evaluation"
FIXTURE_MANIFEST = FIXTURES / "sample-manifest.json"


def copy_fixture(target: Path) -> Path:
    shutil.copytree(FIXTURES, target, dirs_exist_ok=True)
    return target / "sample-manifest.json"


def test_manifest_keeps_external_and_project_results_separate():
    manifest = EvaluationManifest.load(FIXTURE_MANIFEST)

    groups = manifest.datasets_by_provenance()

    assert set(groups) == {"external", "project_owned"}
    assert [item.dataset_id for item in groups["external"]] == ["bdd-sample"]
    assert [item.dataset_id for item in groups["project_owned"]] == ["project-intersection"]


def test_manifest_loads_typed_tracking_queue_and_ignore_annotations():
    manifest = EvaluationManifest.load(FIXTURE_MANIFEST)

    frame = next(item for item in manifest.frames if item.frame_id == "project-night-001")

    assert frame.annotations[0].track_id == "project-1"
    assert frame.annotations[0].bbox == (600.0, 400.0, 760.0, 650.0)
    assert frame.queue_region is not None
    assert len(frame.ignore_regions) == 1


def test_changed_annotation_asset_fails_checksum(tmp_path):
    manifest_path = copy_fixture(tmp_path / "fixture")
    manifest = EvaluationManifest.load(manifest_path)
    (manifest_path.parent / "annotations.json").write_bytes(b"changed")

    with pytest.raises(ChecksumMismatch):
        manifest.validate_files(manifest_path.parent)


def test_manifest_rejects_path_traversal(tmp_path):
    data = json.loads(FIXTURE_MANIFEST.read_text(encoding="utf-8"))
    data["annotation_file"] = "../annotations.json"
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(ManifestValidationError, match="traversal"):
        EvaluationManifest.load(path)


@pytest.mark.parametrize(
    "mutation, expected",
    [
        (lambda data: data["frames"].append(copy.deepcopy(data["frames"][0])), "Duplicate frame_id"),
        (lambda data: data["frames"][0]["annotations"][0].update(bbox=[10, 10, 5, 20]), "bbox"),
        (lambda data: data["frames"][0]["annotations"][0].update(bbox=[0, 0, float("nan"), 20]), "finite"),
    ],
)
def test_annotation_contract_rejects_ambiguous_ground_truth(tmp_path, mutation, expected):
    fixture_dir = tmp_path / "fixture"
    manifest_path = copy_fixture(fixture_dir)
    annotations_path = fixture_dir / "annotations.json"
    annotations = json.loads(annotations_path.read_text(encoding="utf-8"))
    mutation(annotations)
    annotations_path.write_text(json.dumps(annotations, allow_nan=True), encoding="utf-8")
    manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
    import hashlib
    checksum = hashlib.sha256(annotations_path.read_bytes()).hexdigest()
    for dataset in manifest_data["datasets"]:
        dataset["sha256"] = checksum
    manifest_path.write_text(json.dumps(manifest_data), encoding="utf-8")

    with pytest.raises(ManifestValidationError, match=expected):
        EvaluationManifest.load(manifest_path)


def test_unknown_provenance_is_rejected(tmp_path):
    data = json.loads(FIXTURE_MANIFEST.read_text(encoding="utf-8"))
    data["datasets"][0]["provenance"] = "mixed"
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(ManifestValidationError, match="provenance"):
        EvaluationManifest.load(path)
