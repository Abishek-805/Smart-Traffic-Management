"""Evaluate detector accuracy on a labelled Ultralytics/YOLO dataset.

This deliberately requires labelled data. Runtime replay latency cannot establish
precision, recall, or mAP.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ultralytics import YOLO

from ai.evaluation.manifest import EvaluationManifest
from ai.evaluation.model_evaluator import EvaluationPrediction
from ai.evaluation.report import EvidenceMetadata, EvaluationReport


def main():
    parser = argparse.ArgumentParser(description="Measure detector precision, recall and mAP on labelled traffic data")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--data", help="Dataset YAML containing labelled validation images")
    source.add_argument("--manifest", help="Versioned evaluation manifest")
    parser.add_argument("--predictions", help="Optional JSON list of predictions for manifest reporting")
    parser.add_argument("--model", default="yolov8n.pt")
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--conf", type=float, default=0.001, help="Evaluation confidence floor; keep low for PR/mAP curves")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--output", default="docs/benchmarks/detector-evaluation.json")
    args = parser.parse_args()

    if args.manifest:
        manifest = EvaluationManifest.load(args.manifest)
        manifest.validate_files()
        raw_predictions = []
        if args.predictions:
            raw_predictions = json.loads(Path(args.predictions).read_text(encoding="utf-8"))
        predictions = [EvaluationPrediction(
            image_id=item["frame_id"], class_id=int(item["class_id"]),
            class_name=item["class_name"], bbox=tuple(item["bbox"]),
            confidence=float(item["confidence"]),
        ) for item in raw_predictions]
        model_path = Path(args.model)
        model_sha = hashlib.sha256(model_path.read_bytes()).hexdigest() if model_path.is_file() else "unavailable"
        try:
            commit = subprocess.check_output(["git", "rev-parse", "--short=12", "HEAD"], text=True).strip()
        except Exception:
            commit = "unavailable"
        metadata = EvidenceMetadata(
            git_commit=commit,
            configuration={"confidence": args.conf, "device": args.device},
            model_sha256=model_sha,
            model_identity=args.model,
            input_size=args.imgsz,
            runtime="precomputed-predictions",
            warmup_policy={"iterations": 0},
            trial_count=1,
            environment={"device": args.device},
        )
        target_classes = sorted({item.class_name for frame in manifest.frames for item in frame.annotations})
        report = EvaluationReport.evaluate(manifest, predictions, metadata, target_classes)
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(report.to_json() + "\n", encoding="utf-8")
        print(report.to_json())
        return

    data_path = Path(args.data)
    if not data_path.exists():
        parser.error(f"labelled dataset YAML not found: {data_path}")
    model = YOLO(args.model)
    metrics = model.val(data=str(data_path), imgsz=args.imgsz, conf=args.conf,
                        device=args.device, plots=True, save_json=True,
                        project="outputs/evaluations", name=data_path.stem, exist_ok=True)
    names = getattr(metrics, "names", model.names)
    maps = list(getattr(metrics.box, "maps", []))
    report = {
        "scope": "Labelled dataset accuracy; valid only for the dataset named below.",
        "dataset": str(data_path.resolve()),
        "model": args.model,
        "imgsz": args.imgsz,
        "device": args.device,
        "summary": {key: float(value) for key, value in metrics.results_dict.items()},
        "per_class_map50_95": {str(names[i]): float(maps[i]) for i in range(min(len(maps), len(names)))},
        "speed_ms_per_image": {key: float(value) for key, value in metrics.speed.items()},
        "artifacts": str(Path(metrics.save_dir).resolve()),
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
