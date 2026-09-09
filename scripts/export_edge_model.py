"""Export a trained Ultralytics detector to an edge runtime directory."""

import argparse
import shutil
from pathlib import Path

from ultralytics import YOLO


def main() -> None:
    parser = argparse.ArgumentParser(description="Export an Ultralytics detector for Raspberry Pi")
    parser.add_argument("--model", default="yolov8n.pt", help="PyTorch weights or trained traffic model")
    parser.add_argument("--format", choices=("ncnn", "onnx"), default="ncnn")
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--output-dir", default="models")
    parser.add_argument("--replace", action="store_true", help="Replace an existing export with the same name")
    args = parser.parse_args()

    source = Path(args.model).resolve()
    if not source.exists():
        # Ultralytics can download a known official weight name. Keep the plain
        # name here so the download follows its normal verified asset path.
        source_arg = args.model
    else:
        source_arg = str(source)

    exported = Path(YOLO(source_arg).export(
        format=args.format,
        imgsz=args.imgsz,
        batch=1,
        device="cpu",
    )).resolve()
    output_root = Path(args.output_dir).resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    target = output_root / exported.name

    if exported == target:
        print(target)
        return
    if target.exists():
        if not args.replace:
            raise FileExistsError(f"Export already exists: {target}. Pass --replace to replace it.")
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()
    shutil.move(str(exported), str(target))
    print(target)


if __name__ == "__main__":
    main()
