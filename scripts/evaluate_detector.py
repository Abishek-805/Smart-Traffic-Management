"""Evaluate detector accuracy on a labelled Ultralytics/YOLO dataset.

This deliberately requires labelled data. Runtime replay latency cannot establish
precision, recall, or mAP.
"""
import argparse
import json
from pathlib import Path

from ultralytics import YOLO


def main():
    parser = argparse.ArgumentParser(description="Measure detector precision, recall and mAP on labelled traffic data")
    parser.add_argument("--data", required=True, help="Dataset YAML containing labelled validation images")
    parser.add_argument("--model", default="yolo26n.pt")
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--conf", type=float, default=0.001, help="Evaluation confidence floor; keep low for PR/mAP curves")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--output", default="docs/benchmarks/detector-evaluation.json")
    args = parser.parse_args()

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
