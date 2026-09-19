"""Versioned, checksum-pinned evaluation dataset and annotation contract."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import re
from typing import Literal, Optional


class ManifestValidationError(ValueError):
    pass


class ChecksumMismatch(ManifestValidationError):
    pass


Point = tuple[float, float]
Polygon = tuple[Point, ...]


@dataclass(frozen=True)
class BoundingBoxAnnotation:
    class_id: int
    class_name: str
    bbox: tuple[float, float, float, float]
    track_id: Optional[str] = None


@dataclass(frozen=True)
class FrameAnnotation:
    frame_id: str
    dataset_id: str
    image_path: str
    width: int
    height: int
    scene_tags: tuple[str, ...]
    annotations: tuple[BoundingBoxAnnotation, ...]
    queue_region: Optional[Polygon] = None
    ignore_regions: tuple[Polygon, ...] = ()


@dataclass(frozen=True)
class DatasetDescriptor:
    dataset_id: str
    split: str
    provenance: Literal["external", "project_owned"]
    source: str
    license: str
    annotation_revision: str
    sha256: str
    scene_tags: tuple[str, ...]


@dataclass(frozen=True)
class EvaluationManifest:
    schema_version: int
    annotation_file: str
    datasets: tuple[DatasetDescriptor, ...]
    frames: tuple[FrameAnnotation, ...]
    manifest_path: Path

    @classmethod
    def load(cls, path: str | Path) -> "EvaluationManifest":
        manifest_path = Path(path).resolve()
        raw = _read_json(manifest_path)
        if raw.get("schema_version") != 1:
            raise ManifestValidationError("schema_version must be 1")

        annotation_file = _safe_relative_path(raw.get("annotation_file"), "annotation_file")
        datasets = _parse_datasets(raw.get("datasets"))
        annotation_path = (manifest_path.parent / annotation_file).resolve()
        _ensure_contained(annotation_path, manifest_path.parent.resolve(), "annotation_file traversal")
        annotation_raw = _read_json(annotation_path)
        frames = _parse_frames(annotation_raw.get("frames"), {item.dataset_id for item in datasets})
        return cls(
            schema_version=1,
            annotation_file=annotation_file,
            datasets=datasets,
            frames=frames,
            manifest_path=manifest_path,
        )

    def datasets_by_provenance(self) -> dict[str, tuple[DatasetDescriptor, ...]]:
        groups: dict[str, list[DatasetDescriptor]] = {"external": [], "project_owned": []}
        for dataset in self.datasets:
            groups[dataset.provenance].append(dataset)
        return {key: tuple(values) for key, values in groups.items() if values}

    def validate_files(self, root: str | Path | None = None) -> None:
        base = Path(root).resolve() if root is not None else self.manifest_path.parent.resolve()
        annotation_path = (base / self.annotation_file).resolve()
        _ensure_contained(annotation_path, base, "annotation_file traversal")
        if not annotation_path.is_file():
            raise ManifestValidationError(f"Missing annotation asset: {annotation_path}")
        actual = hashlib.sha256(annotation_path.read_bytes()).hexdigest()
        for dataset in self.datasets:
            if actual != dataset.sha256:
                raise ChecksumMismatch(
                    f"Checksum mismatch for {dataset.dataset_id}: expected {dataset.sha256}, got {actual}"
                )


def _read_json(path: Path) -> dict:
    try:
        with path.open("r", encoding="utf-8") as handle:
            value = json.load(
                handle,
                parse_constant=lambda constant: (_ for _ in ()).throw(
                    ManifestValidationError(f"JSON number must be finite: {constant}")
                ),
            )
    except FileNotFoundError as exc:
        raise ManifestValidationError(f"Missing manifest asset: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ManifestValidationError(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ManifestValidationError(f"JSON root must be an object: {path}")
    return value


def _safe_relative_path(value, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ManifestValidationError(f"{field_name} must be a non-empty relative path")
    candidate = Path(value)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ManifestValidationError(f"{field_name} path traversal is not allowed")
    return candidate.as_posix()


def _ensure_contained(path: Path, root: Path, message: str) -> None:
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ManifestValidationError(message) from exc


def _required_text(raw: dict, key: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ManifestValidationError(f"{key} must be a non-empty string")
    return value.strip()


def _tags(value) -> tuple[str, ...]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
        raise ManifestValidationError("scene_tags must be a list of non-empty strings")
    return tuple(dict.fromkeys(item.strip().lower() for item in value))


def _parse_datasets(value) -> tuple[DatasetDescriptor, ...]:
    if not isinstance(value, list) or not value:
        raise ManifestValidationError("datasets must be a non-empty list")
    output = []
    seen = set()
    for raw in value:
        if not isinstance(raw, dict):
            raise ManifestValidationError("Each dataset must be an object")
        dataset_id = _required_text(raw, "dataset_id")
        if dataset_id in seen:
            raise ManifestValidationError(f"Duplicate dataset_id: {dataset_id}")
        seen.add(dataset_id)
        provenance = raw.get("provenance")
        if provenance not in {"external", "project_owned"}:
            raise ManifestValidationError("provenance must be external or project_owned")
        sha256 = _required_text(raw, "sha256").lower()
        if re.fullmatch(r"[0-9a-f]{64}", sha256) is None:
            raise ManifestValidationError("sha256 must contain 64 hexadecimal characters")
        output.append(DatasetDescriptor(
            dataset_id=dataset_id,
            split=_required_text(raw, "split"),
            provenance=provenance,
            source=_required_text(raw, "source"),
            license=_required_text(raw, "license"),
            annotation_revision=_required_text(raw, "annotation_revision"),
            sha256=sha256,
            scene_tags=_tags(raw.get("scene_tags", [])),
        ))
    return tuple(output)


def _parse_polygon(value, width: int, height: int, field_name: str) -> Polygon:
    if not isinstance(value, list) or len(value) < 3:
        raise ManifestValidationError(f"{field_name} must contain at least three points")
    points = []
    for raw in value:
        if not isinstance(raw, list) or len(raw) != 2 or not all(_finite(item) for item in raw):
            raise ManifestValidationError(f"{field_name} points must be finite [x, y] pairs")
        x, y = float(raw[0]), float(raw[1])
        if not (0 <= x <= width and 0 <= y <= height):
            raise ManifestValidationError(f"{field_name} point lies outside the frame")
        points.append((x, y))
    return tuple(points)


def _parse_frames(value, dataset_ids: set[str]) -> tuple[FrameAnnotation, ...]:
    if not isinstance(value, list):
        raise ManifestValidationError("frames must be a list")
    output = []
    seen = set()
    for raw in value:
        if not isinstance(raw, dict):
            raise ManifestValidationError("Each frame must be an object")
        frame_id = _required_text(raw, "frame_id")
        if frame_id in seen:
            raise ManifestValidationError(f"Duplicate frame_id: {frame_id}")
        seen.add(frame_id)
        dataset_id = _required_text(raw, "dataset_id")
        if dataset_id not in dataset_ids:
            raise ManifestValidationError(f"Unknown dataset_id on frame {frame_id}: {dataset_id}")
        width, height = raw.get("width"), raw.get("height")
        if not isinstance(width, int) or not isinstance(height, int) or width <= 0 or height <= 0:
            raise ManifestValidationError("Frame width and height must be positive integers")
        annotations = tuple(_parse_box(item, width, height) for item in raw.get("annotations", []))
        queue = raw.get("queue_region")
        ignores = raw.get("ignore_regions", [])
        if not isinstance(ignores, list):
            raise ManifestValidationError("ignore_regions must be a list")
        output.append(FrameAnnotation(
            frame_id=frame_id,
            dataset_id=dataset_id,
            image_path=_safe_relative_path(raw.get("image_path"), "image_path"),
            width=width,
            height=height,
            scene_tags=_tags(raw.get("scene_tags", [])),
            annotations=annotations,
            queue_region=_parse_polygon(queue, width, height, "queue_region") if queue is not None else None,
            ignore_regions=tuple(_parse_polygon(item, width, height, "ignore_region") for item in ignores),
        ))
    return tuple(output)


def _parse_box(raw, width: int, height: int) -> BoundingBoxAnnotation:
    if not isinstance(raw, dict):
        raise ManifestValidationError("annotation must be an object")
    bbox = raw.get("bbox")
    if not isinstance(bbox, list) or len(bbox) != 4 or not all(_finite(item) for item in bbox):
        raise ManifestValidationError("bbox coordinates must be four finite numbers")
    x1, y1, x2, y2 = (float(item) for item in bbox)
    if not (0 <= x1 < x2 <= width and 0 <= y1 < y2 <= height):
        raise ManifestValidationError("bbox must be ordered and inside frame bounds")
    class_id = raw.get("class_id")
    if not isinstance(class_id, int) or class_id < 0:
        raise ManifestValidationError("class_id must be a non-negative integer")
    track_id = raw.get("track_id")
    if track_id is not None and (not isinstance(track_id, str) or not track_id.strip()):
        raise ManifestValidationError("track_id must be a non-empty string when provided")
    return BoundingBoxAnnotation(
        class_id=class_id,
        class_name=_required_text(raw, "class_name"),
        bbox=(x1, y1, x2, y2),
        track_id=track_id,
    )


def _finite(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
