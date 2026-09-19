"""Compare candidate evidence against an immutable baseline policy."""

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ai.evaluation.regression_gate import QualityGatePolicy, compare_reports


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--policy", default="config/model_quality_gate.json")
    args = parser.parse_args()
    baseline = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
    candidate = json.loads(Path(args.candidate).read_text(encoding="utf-8"))
    policy = QualityGatePolicy.from_dict(
        json.loads(Path(args.policy).read_text(encoding="utf-8"))
    )
    result = compare_reports(baseline, candidate, policy)
    print(json.dumps({"accepted": result.accepted, "failures": result.failures}, indent=2, sort_keys=True))
    return 0 if result.accepted else 1


if __name__ == "__main__":
    raise SystemExit(main())
