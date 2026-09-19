"""Small deterministic tracking/count metrics for labelled frame sequences."""

from __future__ import annotations

from dataclasses import dataclass
from collections import defaultdict


@dataclass(frozen=True)
class TrackingMetrics:
    id_switches: int
    mostly_tracked: int
    track_fragmentations: int
    count_mae: float


def tracking_metrics(gt, pred) -> TrackingMetrics:
    """Score ordered `(identity, frame_number)` observations.

    Within each frame, sorted ground-truth and prediction identities are paired.
    A later different predicted identity for the same ground-truth identity counts
    as one switch even when observations disappeared in between.
    """
    gt_by_frame = _by_frame(gt)
    pred_by_frame = _by_frame(pred)
    frames = sorted(set(gt_by_frame) | set(pred_by_frame))
    assignments = defaultdict(dict)
    total_error = 0
    for frame in frames:
        gt_ids = sorted(gt_by_frame.get(frame, ()))
        pred_ids = sorted(pred_by_frame.get(frame, ()))
        total_error += abs(len(gt_ids) - len(pred_ids))
        for index, gt_id in enumerate(gt_ids):
            assignments[gt_id][frame] = pred_ids[index] if index < len(pred_ids) else None

    switches = 0
    mostly_tracked = 0
    fragmentations = 0
    for gt_id, frame_assignments in assignments.items():
        ordered = [frame_assignments[frame] for frame in sorted(frame_assignments)]
        matched = [value for value in ordered if value is not None]
        switches += sum(left != right for left, right in zip(matched, matched[1:]))
        if ordered and len(matched) / len(ordered) >= 0.8:
            mostly_tracked += 1
        seen_match = False
        in_gap = False
        for value in ordered:
            if value is None and seen_match:
                in_gap = True
            elif value is not None:
                if in_gap:
                    fragmentations += 1
                    in_gap = False
                seen_match = True

    return TrackingMetrics(
        id_switches=switches,
        mostly_tracked=mostly_tracked,
        track_fragmentations=fragmentations,
        count_mae=total_error / len(frames) if frames else 0.0,
    )


def _by_frame(values):
    output = defaultdict(list)
    for identity, frame in values:
        output[int(frame)].append(str(identity))
    return output
