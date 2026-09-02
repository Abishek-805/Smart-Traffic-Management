"""Convert the official IISc UVH-26 COCO release into an Ultralytics dataset.

Download UVH-26 separately from https://huggingface.co/datasets/iisc-aim/UVH-26
(about 90 GB, CC BY 4.0). This converter hard-links images by default so the
prepared dataset does not duplicate that storage.
"""

import argparse
import json
import os
import shutil
from pathlib import Path

CLASSES = [
    "hatchback", "sedan", "suv", "muv", "bus", "truck", "three-wheeler",
    "two-wheeler", "lcv", "mini-bus", "tempo-traveller", "bicycle", "van", "other",
]


def canonical_name(value: str) -> str:
    normalized = value.strip().lower().replace("_", "-").replace(" ", "-")
    aliases = {
        "3-wheeler": "three-wheeler",
        "2-wheeler": "two-wheeler",
        "minibus": "mini-bus",
        "tempo-traveller": "tempo-traveller",
        "tempo-traveler": "tempo-traveller",
    }
    return aliases.get(normalized, normalized)


def link_image(source: Path, destination: Path, mode: str) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        return
    if mode == "copy":
        shutil.copy2(source, destination)
    elif mode == "symlink":
        destination.symlink_to(source.resolve())
    else:
        os.link(source, destination)


def convert_split(source_root: Path, output_root: Path, split: str, mode: str) -> dict:
    release = source_root / ("UVH-26-Train" if split == "train" else "UVH-26-Val")
    annotation = release / f"UVH-26-MV-{'Train' if split == 'train' else 'Val'}.json"
    if not annotation.is_file():
        raise FileNotFoundError(f"Missing official UVH-26 annotation: {annotation}")
    coco = json.loads(annotation.read_text(encoding="utf-8"))
    category_names = {int(item["id"]): canonical_name(str(item["name"]))
                      for item in coco["categories"]}
    class_index = {name: index for index, name in enumerate(CLASSES)}
    unknown = sorted(set(category_names.values()) - set(class_index))
    if unknown:
        raise ValueError(f"Unexpected UVH-26 categories: {unknown}")

    annotations = {}
    for item in coco["annotations"]:
        annotations.setdefault(int(item["image_id"]), []).append(item)

    boxes = 0
    for image in coco["images"]:
        relative = Path(str(image["file_name"]))
        source_image = release / "images" / relative
        if not source_image.is_file():
            matches = list((release / "images").rglob(relative.name))
            if len(matches) != 1:
                raise FileNotFoundError(f"Cannot resolve image {relative} under {release / 'images'}")
            source_image = matches[0]
            relative = source_image.relative_to(release / "images")
        output_image = output_root / "images" / split / relative
        link_image(source_image, output_image, mode)
        label_path = output_root / "labels" / split / relative.with_suffix(".txt")
        label_path.parent.mkdir(parents=True, exist_ok=True)
        width, height = float(image["width"]), float(image["height"])
        lines = []
        for box in annotations.get(int(image["id"]), []):
            x, y, w, h = map(float, box["bbox"])
            if w <= 0 or h <= 0:
                continue
            name = category_names[int(box["category_id"])]
            cx = (x + w / 2) / width
            cy = (y + h / 2) / height
            lines.append(f"{class_index[name]} {cx:.8f} {cy:.8f} {w / width:.8f} {h / height:.8f}")
        label_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
        boxes += len(lines)
    return {"images": len(coco["images"]), "boxes": boxes}


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare official UVH-26 for YOLO26 training")
    parser.add_argument("--source", required=True, type=Path, help="Downloaded UVH-26 dataset root")
    parser.add_argument("--output", type=Path, default=Path("datasets/uvh26"))
    parser.add_argument("--image-mode", choices=("hardlink", "symlink", "copy"), default="hardlink")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    reports = {split: convert_split(args.source, args.output, split, args.image_mode)
               for split in ("train", "val")}
    yaml = [f"path: {args.output.resolve().as_posix()}", "train: images/train", "val: images/val", "names:"]
    yaml.extend(f"  {index}: {name}" for index, name in enumerate(CLASSES))
    (args.output / "traffic.yaml").write_text("\n".join(yaml) + "\n", encoding="utf-8")
    (args.output / "PREPARATION_REPORT.json").write_text(json.dumps(reports, indent=2), encoding="utf-8")
    print(json.dumps({"dataset": str((args.output / 'traffic.yaml').resolve()), **reports}, indent=2))


if __name__ == "__main__":
    main()
