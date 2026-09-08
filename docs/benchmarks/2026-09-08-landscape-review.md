# Landscape and runtime correction, 2026-09-08

## Changes

- Android VisionCamera takeSnapshot reads PreviewView.bitmap, which already includes the display transform. Mobile now explicitly uses interface orientation and sends only the remaining device/display rotation. Frames captured across orientation changes are discarded; unknown orientation is not guessed. Physical device verification remains required.
- Processing acknowledgements no longer gate capture: overwritten backend frames do not receive processed ACKs. Socket buffered bytes still apply backpressure and acknowledgement history stays bounded to 64 entries.
- ByteTrack intermediate predictions use elapsed time relative to the detector observation interval, rather than advancing one full step per preview frame. Predictions expire after at most two seconds without observations. This is short extrapolation, not a new measurement or guaranteed identity recovery through long gaps.
- Empty/all-red scheduler results preserve perception output and timing. Last detection frame IDs are reported per camera.
- Provisional CPU default is YOLOv8n, configurable via YOLO_MODEL_NAME. Existing YOLO26 weights are retained for comparison.

## Measurements

See landscape-model-comparison.json. Fifteen repeated inferences on the same existing real traffic-photo crop, 640 input, CPU four threads, confidence 0.15, IoU 0.60. These are warm detector timings, NOT stream latency, accuracy, moving-video performance or electrical power measurements.

| Model | Mean ms | p95 ms | CPU seconds/frame |
|---|---:|---:|---:|
| YOLO26s | 286.47 | 323.44 | 0.7135 |
| YOLO26n | 131.68 | 143.19 | 0.2562 |
| YOLOv8n | 102.69 | 106.08 | 0.2427 |

YOLOv8n mean inference was 64% lower than YOLO26s in this run. Visual inspection showed improved vehicle coverage in this scene, but truck/bus class errors remain. No ground-truth annotations were available, so more boxes are not presented as an accuracy score. The runtime still accepts low-confidence boxes for ByteTrack recovery; this benchmark's threshold differs from that low threshold. Process RSS is affected by sequential model loading and must not be interpreted as isolated model memory cost.

## Verification

- 68 backend tests passed, including elapsed-time prediction and per-camera buffering.
- Mobile regression suite and TypeScript check passed; new tests failed before the corresponding fixes.
- Four simulated clients passed registration, processing, independent staleness and stop/start checks using a real street photo. This does not validate four physical phones or traffic movement.
- Web production build passed.
- APK 1.0.6/versionCode 7 submitted as EAS build 359acb9f-2cb6-43a9-9512-3e34c55476b7. Build completion and phone installation must be verified separately.

## Remaining acceptance work

Install 1.0.6, restart the backend, then test portrait and both landscape orientations (including rotation lock), checking that vehicles are upright in the backend feed. Use original moving traffic videos or a fixed road camera rather than filming a small monitor image. Record ground-truth counts, per-class precision/recall, track ID switches, and p50/p95 frame age for one then four cameras. The serial inference worker limits aggregate capacity; four times two detector FPS is a target, not a guarantee. Do not interpret stale or predicted counts as fresh detections. Pi runtime/export selection requires the actual board and labelled validation set. No H.264/WebRTC migration was made: measured inference and orientation/capture bugs should be addressed before adding another transport stack.

Sources: installed VisionCamera HybridPreviewView.kt and orientation managers; [Android PreviewView](https://developer.android.com/reference/androidx/camera/view/PreviewView); [Ultralytics tracking](https://docs.ultralytics.com/modes/track).
