"""Fine-tune the Raspberry Pi candidate on labelled real traffic images."""

import argparse
from pathlib import Path

from ultralytics import YOLO


def main() -> None:
    parser = argparse.ArgumentParser(description="Train and validate the 14-class traffic detector")
    parser.add_argument("--data", default="datasets/uvh26/traffic.yaml")
    parser.add_argument("--model", default="yolo26n.pt")
    parser.add_argument("--epochs", type=int, default=80)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", type=float, default=-1, help="-1 lets Ultralytics size the batch")
    parser.add_argument("--device", default="0", help="GPU index, cpu, or mps")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--name", default="yolo26n-uvh26")
    args = parser.parse_args()
    data = Path(args.data)
    if not data.is_file():
        parser.error(f"Prepared dataset YAML not found: {data}")
    model = YOLO(args.model)
    result = model.train(
        data=str(data.resolve()), epochs=args.epochs, imgsz=args.imgsz,
        batch=args.batch, device=args.device, workers=args.workers,
        project="outputs/training", name=args.name, patience=20,
        cache="disk", cos_lr=True, close_mosaic=10, plots=True,
    )
    best = Path(result.save_dir) / "weights" / "best.pt"
    print(f"Best weights: {best.resolve()}")
    print("Run scripts/evaluate_detector.py on the untouched validation split before deployment.")


if __name__ == "__main__":
    main()
