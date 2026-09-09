# Four-camera connectivity and adaptive timing validation

Date: 2026-09-09

## Scope

This validation used the combined local FastAPI runtime and four concurrent WebSocket camera clients, one each for North, East, South, and West. Each client registered through its own generated QR session, sent authenticated heartbeats, and replayed a different real local road image. This validates backend session isolation, frame routing, detection execution, telemetry, and signal scheduling. It does not replace a four-physical-phone Wi-Fi test or a labelled video accuracy evaluation.

## Connectivity and detection

All four clients connected simultaneously and remained isolated by node, token, and direction. Under a 4 FPS offered load per camera, all four lanes continued producing processed acknowledgements and independent detections:

| Lane | Last observed count | Processed ACKs | Mean processed ACK latency |
|---|---:|---:|---:|
| North | 56 | 6 | 2140.1 ms |
| East | 1 | 5 | 2143.0 ms |
| South | 39 | 6 | 1931.2 ms |
| West | 34 | 6 | 1984.7 ms |

The 16 FPS aggregate offered load exceeds this laptop runtime's dense-scene throughput. Latest-frame replacement bounded the queues, so stale work did not grow without limit, but most offered frames were intentionally superseded.

A reproducible 2 FPS per-camera run is stored in `four-camera-yolov8n-2fps-2026-09-09.json`. Dense-scene inference took roughly 395-509 ms per processed frame and the single shared worker produced only 0.4-0.5 processed FPS per lane. Direction p95 processed-ACK latency was 2.24-2.30 seconds.

A 0.5 FPS per-camera capacity-boundary run is stored in `four-camera-yolov8n-0.5fps-2026-09-09.json`. Every lane achieved 0.5 processed FPS and counts remained independent at North 42, East 1, South 26, and West 31. Because the four simulated senders transmit at nearly the same instant, the serialized worker still gives later lanes about 1.4 seconds of queue wait and direction p95 ACK latency of 1.67-1.92 seconds.

## Adaptive timing and fairness

The scheduler was exercised with the four detected demand levels. It selected the normal clockwise service order and bounded each green duration:

| Phase | Detected demand used by test | Green duration |
|---|---:|---:|
| North | 56 | 60 s |
| East | 1 | 12 s |
| South | 39 | 54 s |
| West | 34 | 51 s |

The low-demand East lane was still served after North, so the high North count did not starve it. In a second scenario with East at zero vehicles, the scheduler skipped East and continued North to South to West. Existing emergency override and scheduler regression tests also passed.

## Assessment

- **Multiple connectivity:** passes in local simulation for four concurrent authenticated clients, distinct directions, heartbeats, frame routing, and reconnect/session rules.
- **Detection isolation:** passes; each direction reports results from its own input. The counts above demonstrate execution, not accuracy, because the images do not have ground-truth annotations.
- **Smart timing:** passes the current fairness, empty-lane skip, ordering, minimum, and maximum duration rules.
- **Four-camera latency target:** fails for dense scenes on this laptop. The documented target is p95 below 750 ms at 2 FPS per camera; the measured p95 is about 2.3 seconds.

The limiting component is the single serialized inference worker shared by all four directions, not QR registration or WebSocket routing. Lowering phone FPS prevents backlog but cannot make simultaneous four-lane inference meet 750 ms. Reaching that target requires a batched multi-lane inference path, a faster exported runtime or accelerator, and validation on labelled moving traffic video. A Raspberry Pi CPU should not be expected to outperform this laptop; Pi deployment needs an optimized NCNN/OpenVINO/TFLite profile or an accelerator and must be benchmarked on the actual board.

