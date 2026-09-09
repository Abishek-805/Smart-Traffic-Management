"""Remove known generated artifacts from the backend and sibling mobile workspace.

The allowlist is intentionally fixed. Source, datasets, input videos, weights in use,
dependency environments, and production web assets are never selected.
"""

import argparse
import shutil
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
MOBILE_ROOT = BACKEND_ROOT.parent / "traffic-camera-app"


def size_bytes(path: Path) -> int:
    if path.is_file():
        return path.stat().st_size
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())


def verified(path: Path, root: Path) -> Path:
    resolved = path.resolve()
    resolved.relative_to(root.resolve())
    if resolved == root.resolve():
        raise RuntimeError(f"Refusing to select workspace root: {resolved}")
    return resolved


def collect() -> list[tuple[Path, Path]]:
    selected: dict[Path, Path] = {}

    # Fixed generated directories. Keep virtual environments and node_modules so
    # the repaired project remains immediately runnable.
    for relative in (".pytest_cache", ".venv_test"):
        path = BACKEND_ROOT / relative
        if path.exists():
            selected[verified(path, BACKEND_ROOT)] = BACKEND_ROOT
    # Runtime logs are disposable. Benchmark inputs/results under outputs are
    # retained because they are tracked validation evidence.
    for container in (BACKEND_ROOT / "logs", BACKEND_ROOT / ".logs"):
        if container.exists():
            for child in container.iterdir():
                selected[verified(child, BACKEND_ROOT)] = BACKEND_ROOT
    for path in BACKEND_ROOT.rglob("__pycache__"):
        if not any(part in {".git", ".venv", "venv", "node_modules"} for part in path.parts):
            selected[verified(path, BACKEND_ROOT)] = BACKEND_ROOT
    for weight_name in ("yolo11n.pt", "yolo26n.pt", "yolo26s.pt"):
        old_weight = BACKEND_ROOT / weight_name
        if old_weight.exists():
            selected[verified(old_weight, BACKEND_ROOT)] = BACKEND_ROOT

    if MOBILE_ROOT.exists():
        for relative in (
            ".expo",
            "dist-android",
            "dist-android-crashfix",
            "dist-android-1.0.2",
            "android/.gradle",
            "android/.kotlin",
            "android/build",
            "android/app/build",
        ):
            path = MOBILE_ROOT / relative
            if path.exists():
                selected[verified(path, MOBILE_ROOT)] = MOBILE_ROOT

    # If a parent is selected, omit its children from the deletion plan.
    ordered = sorted(selected, key=lambda item: len(item.parts))
    compact: list[tuple[Path, Path]] = []
    for path in ordered:
        if not any(path.is_relative_to(parent) for parent, _ in compact):
            compact.append((path, selected[path]))
    return compact


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Apply the displayed fixed cleanup plan")
    args = parser.parse_args()
    selected = collect()
    total = sum(size_bytes(path) for path, _ in selected)
    for path, _ in selected:
        print(f"{'DELETE' if args.apply else 'WOULD DELETE'} {path} ({size_bytes(path) / 1024**2:.2f} MB)")
    print(f"TOTAL {total / 1024**2:.2f} MB")
    if not args.apply:
        return
    for path, root in selected:
        verified(path, root)
        if path.is_dir():
            shutil.rmtree(path)
        elif path.exists():
            path.unlink()


if __name__ == "__main__":
    main()
