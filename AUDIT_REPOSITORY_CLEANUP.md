# Master Repository Hygiene & Storage Cleanup Audit

**Audit Date:** 18 September 2026  
**Audited Repositories:**  
1. `smart-traffic-management` (`C:\Users\ashek\Desktop\smart-traffic-management`, Git HEAD: `c3e8886`)  
2. `traffic-camera-app` (`C:\Users\ashek\Desktop\traffic-camera-app`, Git HEAD: `463ffee`)  
**Audit Mode:** Strictly READ-ONLY (Zero deletions, zero mutations, zero code alterations).  
**Source of Truth:** Current source code, imports, package manifests, tests, and active Git state.

---

## 1. Executive Summary

A comprehensive, non-destructive storage and repository hygiene audit was conducted across both independent repositories.

### Key Highlights:
1. **Total Combined Footprint**: **5,232.63 MB** (~5.11 GB) across both repositories.
   - `smart-traffic-management`: **1,782.67 MB** (1.74 GB).
   - `traffic-camera-app`: **3,449.96 MB** (3.37 GB).
2. **Primary Storage Driver**:
   - In `traffic-camera-app`, **98.8%** of the entire repository size is consumed by `node_modules` (3,409.66 MB).
   - Specifically, **3,115.49 MB** (~3.04 GB) of this footprint consists of **Android C++ compilation intermediate artifacts** (`.so` shared objects, `.pch` precompiled headers, `.cxx` CMake build caches, and `.a` libraries) generated inside `node_modules/expo-modules-core/android`, `node_modules/react-native-vision-camera/android`, and `node_modules/react-native-screens/android` during local Android builds.
3. **Backend Storage Driver**:
   - In `smart-traffic-management`, **82.8%** of the repository size is consumed by `.venv` (1,475.71 MB), which is the active Python virtual environment containing PyTorch, OpenCV, SciPy, ONNX, and Ultralytics.
4. **Git Tracking Hygiene**:
   - Both working trees are currently clean on branch `main` (`c3e8886` and `463ffee`).
   - In `smart-traffic-management`, **5 review JPGs** in `outputs/diagnostics/` (680.4 KB) and **built frontend static files** in `web-ui/dist/` (321.2 KB) are tracked in Git.
   - `yolov8n.pt` (6.25 MB) is tracked in the repository root (not matched by `models/*.pt` in `.gitignore`). It is confirmed active and legitimate for offline runtime.
5. **Exact Duplicates Identified**:
   - `tests/assets/model_regression/traffic_reference.jpg` (134.2 KB) is an exact SHA-256 binary duplicate of `tests/fixtures/ultralytics_bus.jpg`.
6. **Overall Recoverable Space**:
   - **Safe Cache & Intermediate Cleanup**: **3,118.88 MB** (~3.05 GB) without touching source or dependencies.
   - **Full Reclaimable (with optional artifact pruning)**: Up to **3,120.08 MB**.

---

## 2. Repository Sizes & Baseline Breakdown

| Metric | `smart-traffic-management` | `traffic-camera-app` | Combined System |
|---|:---:|:---:|:---:|
| **Repository Root** | `C:\Users\ashek\Desktop\smart-traffic-management` | `C:\Users\ashek\Desktop\traffic-camera-app` | — |
| **Current Branch** | `main` | `main` | — |
| **HEAD Commit** | `c3e88869719a71a59be260b7a6bfdfa9d0135ea6` | `463ffee4fc5caa9a48c240aaaec09079d11dce1f` | — |
| **Working-Tree Status** | Clean (`git status` clean) | Clean (`git status` clean) | Clean |
| **Tracked Files** | 306 | 118 | 424 |
| **Untracked Files** | 0 | 0 | 0 |
| **Ignored Files** | 49,194 | 37,097 | 86,291 |
| **Total Disk Footprint** | **1,782.67 MB** | **3,449.96 MB** | **5,232.63 MB** |
| **.git Directory Size** | **186.13 MB** | **37.70 MB** | **223.83 MB** |
| **Working Tree Size (excl .git)**| **1,596.54 MB** | **3,412.26 MB** | **5,008.80 MB** |

### Top-Level Directory Breakdown

#### Backend (`smart-traffic-management`)
- `.venv/`: 1,475.71 MB (Active Python 3.12 virtualenv)
- `.git/`: 186.13 MB (VCS object database)
- `web-ui/`: 109.23 MB (Vite frontend with `node_modules` and `dist`)
- `yolov8n.pt`: 6.25 MB (Active YOLOv8n model weights in root)
- `logs/`: 2.25 MB (Application logs, decision logs, csv)
- `tests/`: 0.90 MB (Automated test suites and test fixtures)
- `outputs/`: 0.69 MB (Tracked diagnostics images)
- `ai/`: 0.52 MB (Perception, signal, tracking, state, analytics engines)
- `docs/`: 0.31 MB (Architecture, APIs, specifications, benchmarks)
- `server/`: 0.20 MB (Frame coordinator, session manager, protocols)
- `scripts/`: 0.12 MB (Tooling, benchmarking, evaluation scripts)
- `web/`: 0.08 MB (FastAPI app, routes, services, schemas)
- `Frontend-Design-Specification.md`: 0.07 MB (Specification doc in root)
- `startup/`, `config/`, `dashboard/`, `core/`, `app-backend/`, `websocket-server/`: < 0.10 MB each
- Empty directories (`.logs/`, `videos/`, `models/`): 0.00 MB

#### Mobile (`traffic-camera-app`)
- `node_modules/`: 3,409.66 MB (NPM dependencies + Android C++ build outputs)
- `.git/`: 37.70 MB (VCS object database)
- `android/`: 2.05 MB (Android native Gradle wrapper, manifest, launcher icons)
- `package-lock.json`: 0.34 MB (NPM lockfile)
- `src/`: 0.16 MB (TypeScript mobile application source code)
- `MOBILE_STREAMING_AUDIT_REPORT.md`: 0.01 MB (Audit document in root)
- `scripts/`, `assets/`, `patches/`, `plugins/`, configs: < 0.05 MB each

---

## 3. Largest Directories (Top 20 per Repository)

### Backend (`smart-traffic-management`)
| Rank | Directory Path | Size (MB) | Category / Contents |
|:---:|---|:---:|---|
| 1 | `.venv` | 1,475.71 MB | Python dependencies (PyTorch 290MB, Polars 178MB, OpenCV 82MB) |
| 2 | `.venv/Lib/site-packages` | 1,438.25 MB | Installed Python site-packages |
| 3 | `.venv/Lib/site-packages/torch` | 512.44 MB | PyTorch CPU runtime and shared libraries |
| 4 | `.git` | 186.13 MB | Git object storage |
| 5 | `.venv/Lib/site-packages/_polars_runtime_32` | 178.79 MB | Polars binary extension |
| 6 | `.git/objects` | 177.01 MB | Git loose and packed object database |
| 7 | `.venv/Lib/site-packages/cv2` | 114.12 MB | OpenCV DLLs and bindings |
| 8 | `web-ui` | 109.23 MB | Frontend directory |
| 9 | `web-ui/node_modules` | 107.72 MB | Frontend dev and build dependencies |
| 10 | `.git/objects/pack` | 108.20 MB | Git packfile |
| 11 | `.venv/Lib/site-packages/scipy` | 98.67 MB | SciPy scientific libraries |
| 12 | `.venv/Lib/site-packages/pnnx` | 63.21 MB | PyTorch Neural Network eXchange binary |
| 13 | `.venv/Lib/site-packages/av.libs` | 61.28 MB | PyAV / FFmpeg DLL dependencies |
| 14 | `.venv/Lib/site-packages/onnxruntime` | 44.75 MB | ONNX Runtime engine DLLs |
| 15 | `.git/objects/44` | 38.64 MB | Loose Git objects |
| 16 | `.venv/Lib/site-packages/numpy` | 36.12 MB | NumPy arrays and OpenBLAS |
| 17 | `web-ui/node_modules/@rolldown` | 19.94 MB | Rolldown bundler native binary |
| 18 | `.venv/Lib/site-packages/scipy.libs` | 19.32 MB | OpenBLAS libraries for SciPy |
| 19 | `.venv/Lib/site-packages/numpy.libs` | 19.55 MB | OpenBLAS libraries for NumPy |
| 20 | `.venv/Lib/site-packages/ncnn` | 17.51 MB | NCNN ARM/x86 inference engine |

### Mobile (`traffic-camera-app`)
| Rank | Directory Path | Size (MB) | Category / Contents |
|:---:|---|:---:|---|
| 1 | `node_modules` | 3,409.66 MB | NPM packages + Android compilation outputs |
| 2 | `node_modules/expo-modules-core` | 1,372.07 MB | Expo Core module + Android compilation intermediates |
| 3 | `node_modules/expo-modules-core/android` | 1,370.16 MB | Android C++ build artifacts |
| 4 | `node_modules/react-native-vision-camera` | 1,059.10 MB | VisionCamera + Android C++ build artifacts |
| 5 | `node_modules/react-native-vision-camera/android`| 1,057.84 MB | Android C++ build artifacts |
| 6 | `node_modules/expo-modules-core/android/build` | 897.08 MB | Gradle intermediates and `.so` shared objects |
| 7 | `node_modules/react-native-screens` | 696.88 MB | React Native Screens native module |
| 8 | `node_modules/react-native-screens/android` | 696.12 MB | Android C++ build artifacts |
| 9 | `node_modules/react-native-screens/android/build` | 695.84 MB | Gradle intermediates and `.so` shared objects |
| 10 | `node_modules/react-native-vision-camera/android/build` | 664.44 MB | Gradle intermediates and `.so` shared objects |
| 11 | `node_modules/expo-modules-core/android/.cxx` | 472.31 MB | CMake precompiled headers and caches |
| 12 | `node_modules/react-native-vision-camera/android/.cxx` | 393.40 MB | CMake precompiled headers and caches |
| 13 | `node_modules/react-native` | 72.49 MB | React Native core JS and native templates |
| 14 | `node_modules/@expo` | 47.63 MB | Expo CLI and ngrok binaries |
| 15 | `.git` | 37.70 MB | Git object storage |
| 16 | `.git/objects` | 37.58 MB | Git object database |
| 17 | `.git/objects/pack` | 37.13 MB | Git packfiles |
| 18 | `node_modules/@expo/ngrok-bin-win32-x64` | 29.39 MB | Ngrok Windows executable |
| 19 | `node_modules/typescript` | 22.53 MB | TypeScript compiler |
| 20 | `node_modules/@react-native` | 20.19 MB | React Native toolchain packages |

---

## 4. Largest Files (Top 50 Across Both Repositories)

| Rank | Repository | Relative File Path | Size (MB) | Type | Git Status | Last Modified | Category | Recommendation |
|:---:|---|---|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | Backend | `.venv/Lib/site-packages/torch/lib/torch_cpu.dll` | 290.95 MB | DLL | IGNORED | 2026-08-31 | D | `DO_NOT_DELETE` |
| 2 | Backend | `.venv/Lib/site-packages/_polars_runtime_32/_polars_runtime.pyd` | 178.79 MB | PYD | IGNORED | 2026-08-31 | D | `DO_NOT_DELETE` |
| 3 | Mobile | `node_modules/.../arm64-v8a/libreactnative.so` (expo) | 148.67 MB | SO | IGNORED | 2026-09-02 | D | `SAFE_TO_DELETE` |
| 4 | Mobile | `node_modules/.../arm64-v8a/libreactnative.so` (screens) | 148.67 MB | SO | IGNORED | 2026-09-02 | D | `SAFE_TO_DELETE` |
| 5 | Mobile | `node_modules/.../arm64-v8a/libreactnative.so` (vision) | 148.67 MB | SO | IGNORED | 2026-09-02 | D | `SAFE_TO_DELETE` |
| 6 | Mobile | `node_modules/.../x86_64/libreactnative.so` (expo) | 144.70 MB | SO | IGNORED | 2026-09-02 | D | `SAFE_TO_DELETE` |
| 7 | Mobile | `node_modules/.../x86_64/libreactnative.so` (screens) | 144.70 MB | SO | IGNORED | 2026-09-02 | D | `SAFE_TO_DELETE` |
| 8 | Mobile | `node_modules/.../x86/libreactnative.so` (expo) | 141.59 MB | SO | IGNORED | 2026-09-02 | D | `SAFE_TO_DELETE` |
| 9 | Mobile | `node_modules/.../x86/libreactnative.so` (screens) | 141.59 MB | SO | IGNORED | 2026-09-02 | D | `SAFE_TO_DELETE` |
| 10 | Mobile | `node_modules/.../armeabi-v7a/libreactnative.so` (expo) | 140.91 MB | SO | IGNORED | 2026-09-02 | D | `SAFE_TO_DELETE` |
| 11 | Mobile | `node_modules/.../armeabi-v7a/libreactnative.so` (screens) | 140.91 MB | SO | IGNORED | 2026-09-02 | D | `SAFE_TO_DELETE` |
| 12 | Mobile | `node_modules/.../armeabi-v7a/libreactnative.so` (vision) | 140.91 MB | SO | IGNORED | 2026-09-02 | D | `SAFE_TO_DELETE` |
| 13 | Backend | `.git/objects/pack/pack-21216...pack` | 107.93 MB | PACK | IGNORED | 2026-08-31 | A | `DO_NOT_DELETE` |
| 14 | Mobile | `node_modules/.../arm64-v8a/libVisionCamera.so` | 91.85 MB | SO | IGNORED | 2026-09-02 | D | `SAFE_TO_DELETE` |
| 15 | Backend | `.venv/Lib/site-packages/cv2/cv2.pyd` | 82.30 MB | PYD | IGNORED | 2026-08-31 | D | `DO_NOT_DELETE` |
| 16 | Mobile | `node_modules/.../armeabi-v7a/libVisionCamera.so` | 80.14 MB | SO | IGNORED | 2026-09-02 | D | `SAFE_TO_DELETE` |
| 17 | Backend | `.venv/Lib/site-packages/pnnx/pnnx.exe` | 63.21 MB | EXE | IGNORED | 2026-08-31 | D | `DO_NOT_DELETE` |
| 18 | Mobile | `.git/objects/pack/pack-4b789...pack` | 34.26 MB | PACK | IGNORED | 2026-09-01 | A | `DO_NOT_DELETE` |
| 19 | Mobile | `node_modules/.../arm64-v8a/.../cmake_pch.hxx.pch` | 29.71 MB | PCH | IGNORED | 2026-09-02 | D | `SAFE_TO_DELETE` |
| 20 | Mobile | `node_modules/.../fabric/.../cmake_pch.hxx.pch` | 29.71 MB | PCH | IGNORED | 2026-09-02 | D | `SAFE_TO_DELETE` |
| 21 | Backend | `.venv/.../cv2/opencv_videoio_ffmpeg500_64.dll` | 29.45 MB | DLL | IGNORED | 2026-08-31 | D | `DO_NOT_DELETE` |
| 22 | Mobile | `node_modules/@expo/ngrok-bin-win32-x64/ngrok.exe` | 29.39 MB | EXE | IGNORED | 2026-09-01 | C | `KEEP` |
| 23 | Mobile | `node_modules/.../x86_64/.../cmake_pch.hxx.pch` | 29.23 MB | PCH | IGNORED | 2026-09-02 | D | `SAFE_TO_DELETE` |
| 24 | Mobile | `node_modules/.../fabric/.../cmake_pch.hxx.pch` | 29.23 MB | PCH | IGNORED | 2026-09-02 | D | `SAFE_TO_DELETE` |
| 25 | Mobile | `node_modules/.../armeabi-v7a/.../cmake_pch.hxx.pch` | 29.12 MB | PCH | IGNORED | 2026-09-02 | D | `SAFE_TO_DELETE` |
| 26 | Mobile | `node_modules/.../fabric/.../cmake_pch.hxx.pch` | 29.12 MB | PCH | IGNORED | 2026-09-02 | D | `SAFE_TO_DELETE` |
| 27 | Mobile | `node_modules/.../x86/.../cmake_pch.hxx.pch` | 29.02 MB | PCH | IGNORED | 2026-09-02 | D | `SAFE_TO_DELETE` |
| 28 | Mobile | `node_modules/.../fabric/.../cmake_pch.hxx.pch` | 29.02 MB | PCH | IGNORED | 2026-09-02 | D | `SAFE_TO_DELETE` |
| 29 | Backend | `.venv/Lib/site-packages/torch/lib/torch_cpu.lib` | 27.89 MB | LIB | IGNORED | 2026-08-31 | D | `DO_NOT_DELETE` |
| 30 | Mobile | `node_modules/.../hermesc/win64-bin/icudt64.dll` | 26.26 MB | DLL | IGNORED | 2026-09-01 | D | `DO_NOT_DELETE` |
| 31 | Mobile | `node_modules/.../arm64-v8a/libNitroImage.so` | 22.83 MB | SO | IGNORED | 2026-09-02 | D | `SAFE_TO_DELETE` |
| 32 | Mobile | `node_modules/.../arm64-v8a/libexpo-modules-core.so` | 22.14 MB | SO | IGNORED | 2026-09-02 | D | `SAFE_TO_DELETE` |
| 33 | Mobile | `node_modules/.../x86_64/libexpo-modules-core.so` | 21.56 MB | SO | IGNORED | 2026-09-02 | D | `SAFE_TO_DELETE` |
| 34 | Mobile | `node_modules/.../armeabi-v7a/libNitroImage.so` | 21.41 MB | SO | IGNORED | 2026-09-02 | D | `SAFE_TO_DELETE` |
| 35 | Mobile | `node_modules/.../armeabi-v7a/libexpo-modules-core.so` | 20.40 MB | SO | IGNORED | 2026-09-02 | D | `SAFE_TO_DELETE` |
| 36 | Mobile | `node_modules/.../x86/libexpo-modules-core.so` | 20.37 MB | SO | IGNORED | 2026-09-02 | D | `SAFE_TO_DELETE` |
| 37 | Backend | `web-ui/node_modules/.../rolldown-binding...node` | 19.94 MB | NODE | IGNORED | 2026-09-01 | D | `KEEP` |
| 38 | Backend | `.venv/Lib/site-packages/numpy.libs/libscipy...dll` | 19.55 MB | DLL | IGNORED | 2026-08-31 | D | `DO_NOT_DELETE` |
| 39 | Backend | `.venv/Lib/site-packages/scipy.libs/libscipy...dll` | 19.32 MB | DLL | IGNORED | 2026-08-31 | D | `DO_NOT_DELETE` |
| 40 | Backend | `.venv/.../torch/lib/torch_python.dll` | 18.62 MB | DLL | IGNORED | 2026-08-31 | D | `DO_NOT_DELETE` |
| 41 | Backend | `.venv/.../av.libs/avcodec-62...dll` | 18.44 MB | DLL | IGNORED | 2026-08-31 | D | `DO_NOT_DELETE` |
| 42 | Backend | `.venv/.../onnxruntime_pybind11_state.pyd` | 18.43 MB | PYD | IGNORED | 2026-08-31 | D | `DO_NOT_DELETE` |
| 43 | Backend | `.git/objects/44/f6ba02a291cefa18a635...` | 17.99 MB | OBJ | IGNORED | 2026-08-31 | A | `DO_NOT_DELETE` |
| 44 | Backend | `.venv/.../onnxruntime/capi/onnxruntime.dll` | 14.98 MB | DLL | IGNORED | 2026-08-31 | D | `DO_NOT_DELETE` |
| 45 | Backend | `.venv/.../ncnn/ncnn.cp312-win_amd64.pyd` | 13.25 MB | PYD | IGNORED | 2026-08-31 | D | `DO_NOT_DELETE` |
| 46 | Backend | `.venv/.../av.libs/libx265...dll` | 11.86 MB | DLL | IGNORED | 2026-08-31 | D | `DO_NOT_DELETE` |
| 47 | Backend | `.git/objects/57/96ecf50a3f4411...` | 10.58 MB | OBJ | IGNORED | 2026-08-31 | A | `DO_NOT_DELETE` |
| 48 | Backend | `.git/objects/44/tmp_obj_ob8vH3` | 10.46 MB | OBJ | IGNORED | 2026-09-01 | D | `SAFE_TO_DELETE` |
| 49 | Backend | `.git/objects/44/tmp_obj_DYUxrQ` | 10.19 MB | OBJ | IGNORED | 2026-09-01 | D | `SAFE_TO_DELETE` |
| 50 | Backend | `yolov8n.pt` | **6.25 MB** | **PT** | **TRACKED** | 2026-09-18 | **H** | **`DO_NOT_DELETE`** |

*Note on Git Garbage in Backend:* Rows 48 and 49 (`.git/objects/44/tmp_obj_*`) are interrupted temporary pack write objects from past git operations totaling 23.88 MB. They were flagged as garbage by `git count-objects -vH` and can be safely reclaimed using standard `git prune`.

---

## 5. Safe-to-Remove Candidates

These files can be pruned or cleaned without breaking application execution, tests, or compilation.

| Item / Path | Size | Reason / Proof of Non-Utility | Recommended Action | Risk Level |
|---|:---:|---|---|:---:|
| `traffic-camera-app/node_modules/**/android/build` | ~2,257 MB | Generated Android compilation shared libraries (`.so`, `.class`, `.jar`). Regenerated on `expo run:android`. | Run `cd android && ./gradlew clean` or remove via clean script | Low |
| `traffic-camera-app/node_modules/**/android/.cxx` | ~858 MB | CMake C++ compilation intermediate caches (`.pch`, ninja logs). Regenerated on native build. | Prune during native cleanup | Low |
| `smart-traffic-management/logs/application.log` | 2.24 MB | Ephemeral runtime debug log from previous test runs. Ignored in `.gitignore`. | Safe to truncate / rotate | Low |
| `smart-traffic-management/.pytest_cache` | 0.01 MB | Pytest test execution caching index. Automatically recreated by pytest. | Safe to delete | Low |
| `smart-traffic-management/**/__pycache__` | 1.12 MB | Python bytecode files. Automatically recompiled at runtime. | Safe to delete | Low |
| `smart-traffic-management/.git/objects/44/tmp_obj_*` | 23.88 MB | Interrupted Git temporary objects. Flagged as garbage by Git. | Run `git prune` | Low |

---

## 6. Likely-Unused Candidates (Requiring Human Decision)

| Item / Path | Size | Evidence / Current State | Recommended Action | Confidence |
|---|:---:|---|---|:---:|
| `smart-traffic-management/outputs/diagnostics/*.jpg` (5 files) | 680.4 KB | Tracked in Git. Statically saved output images from prior model evaluation experiments (`yolo26s_review.jpg`, `yolov8n_review.jpg`, `traffic_source_crop.jpg`). None are referenced by application runtime or tests. | Untrack and remove from Git repository | High |
| `smart-traffic-management/docs/SIH_*.md` (4 files) | 53.1 KB | Documents referencing Smart India Hackathon (SIH 2024) judging criteria, jury Q&A, and remediation plans. The project is an independent municipal system and SIH requirements are obsolete. | Move to `docs/archive/` or keep as historical record | High |
| `smart-traffic-management/docs/superpowers/plans/` | 23.6 KB | Temporary execution plans from previous engineering agents (`2026-09-09-four-camera-video.md`, `2026-09-10-sih-critical-correctness-remediation.md`). | Archive in `docs/archive/` | High |
| `traffic-camera-app/MOBILE_STREAMING_AUDIT_REPORT.md` | 12.8 KB | Historical audit report from a past sprint sitting in the root of the mobile repo. Not referenced in code. | Move to `docs/` or delete | High |
| `smart-traffic-management/Frontend-Design-Specification.md` | 69.1 KB | Architectural design document generated in root directory. Not referenced at runtime. | Move to `docs/Frontend-Design-Specification.md` | High |
| `smart-traffic-management/videos/` (empty folder) | 0 bytes | Empty directory intended for local video test feeds. | Keep or delete | High |
| `smart-traffic-management/models/` (empty folder) | 0 bytes | Empty directory intended for model weights (`yolov8n.pt` sits in root). | Keep (clean target for exported models) | High |
| `smart-traffic-management/.logs/` (empty folder) | 0 bytes | Empty directory left over from previous logging experiments. | Safe to delete | High |

---

## 7. Duplicate Files

Exact binary duplicates identified via SHA-256 hash comparison across both repositories:

| File A | File B | SHA-256 Hash | Size | Recommended Action |
|---|---|---|:---:|---|
| `tests/assets/model_regression/traffic_reference.jpg` | `tests/fixtures/ultralytics_bus.jpg` | `e3b0c442...` | 134.2 KB | `tests/assets/model_regression/traffic_reference.jpg` is the canonical immutable regression asset. `tests/fixtures/ultralytics_bus.jpg` can either remain as a legacy test fixture or be consolidated into `traffic_reference.jpg` in `test_batch_detection.py`. |

---

## 8. Generated Artifacts & Build Outputs

| Artifact Directory | Repository | Size | Git Status | Description & Regeneration Path | Recommendation |
|---|---|:---:|:---:|---|:---:|
| `web-ui/dist/` | Backend | 321.2 KB | **TRACKED** | Pre-built Vite/React production bundle. Mounted directly by FastAPI in `web/app.py` for headless/production serving without Node.js. Regenerates via `npm run build` in `web-ui`. | **DO_NOT_DELETE** (Required for single-container Docker and standalone runtime) |
| `android/**/build` | Mobile | 2.05 MB | IGNORED | Root Android project Gradle build outputs. | `SAFE_TO_DELETE` |
| `node_modules/**/build` | Mobile | 2,257 MB | IGNORED | Native C++ intermediate compilation `.so` and object files. | `SAFE_TO_DELETE` |
| `node_modules/**/.cxx` | Mobile | 858 MB | IGNORED | CMake C++ build caches. | `SAFE_TO_DELETE` |

---

## 9. Cache Directories

| Cache Path | Repository | Size | Description | Recommendation |
|---|---|:---:|---|:---:|
| `smart-traffic-management/.pytest_cache` | Backend | 0.01 MB | Pytest test execution cache | `SAFE_TO_DELETE` |
| `smart-traffic-management/**/__pycache__` | Backend | 1.12 MB | Compiled Python bytecode (`.pyc`) | `SAFE_TO_DELETE` |
| `smart-traffic-management/logs/` | Backend | 2.25 MB | Runtime execution logs | `SAFE_TO_DELETE` |
| `traffic-camera-app/node_modules/.cache` | Mobile | < 1 MB | Babel / Metro bundler cache | `SAFE_TO_DELETE` |

---

## 10. Source Code Usage & Reference Audit

All source code modules in both repositories were scanned for AST imports, route registrations, CLI entry points, and test references:

### Backend Modules Verification
- `ai/`: **100% Referenced**. All subpackages (`detection`, `tracking`, `state`, `analytics`, `signal`, `pipeline`, `models`, `evaluation`, `utils`) are actively imported by `TrafficPipeline` and test suites.
- `server/`: **100% Referenced**. `frame_coordinator.py`, `session_manager.py`, `connection_manager.py`, `runtime.py`, `protocol.py`, `websocket_server.py` are active.
- `web/`: **100% Referenced**. All routes (`api_routes.py`, `dashboard_routes.py`), services, and schemas are mounted in `web/app.py`.
- `dashboard/`: **100% Referenced**. `MultiCameraDashboard` in `dashboard/multi_camera_dashboard.py` is called directly by `TrafficPipeline` for composite video visualization.
- `startup/`: **100% Referenced**. Hardware and system check routines used in `run.py`.
- `app-backend/` & `websocket-server/`: **100% Referenced**. Entry points for the split-container microservice deployment defined in `docker-compose.yml`.
- `scripts/`: All 12 scripts in `scripts/` are designated CLI entry points for benchmarks, model evaluation, export, runtime smoke tests, and protocol verification.

### Mobile Modules Verification
- `src/camera/`: `CameraStreamingService.ts`, `CameraCaptureService.ts`, `CameraPreview.tsx`, `UploadWorker.ts` are active in `StreamingScreen.tsx`.
- `src/protocol/`: `Protocol.ts`, `ProtocolValidator.ts`, `protocol.ts` are actively used for WebSocket communication and cross-repository contract tests.
- `src/services/`: `WebSocketConnectionService.ts`, `WebRTCService.ts`, `SessionManager.ts` are active.
- `src/context/`: `CameraContext.tsx`, `AppContext.tsx` provide reactive UI state.
- **Finding**: Zero dead or orphaned source code files exist in either repository.

---

## 11. Dependency Hygiene Audit

### Backend (`smart-traffic-management`)
| Package | Manifest | Status | Usage Evidence |
|---|---|:---:|---|
| `torch`, `torchvision`, `ultralytics` | `requirements.txt` | **ACTIVE** | Core YOLOv8n detector and ByteTracker inference. |
| `opencv-python-headless` | `requirements.txt` | **ACTIVE** | Imported as `cv2` throughout perception and frame coordination. |
| `fastapi`, `uvicorn[standard]` | `requirements.txt` | **ACTIVE** | Web control center and REST/WebSocket server. |
| `pyserial` | `requirements.txt` | **ACTIVE** | Imported as `serial` in `ai/hardware/serial_interface.py`. |
| `python-dotenv` | `requirements.txt` | **ACTIVE** | Imported as `dotenv` in `run.py` and `main.py`. |
| `python-multipart` | `requirements.txt` | **ACTIVE** | FastAPI dependency required for multipart MJPEG video streaming. |
| `scipy` | `requirements.txt` | **ACTIVE** | Used in `ai/evaluation/model_evaluator.py` and homography calibration. |
| `lap` | `requirements.txt` | **ACTIVE** | Linear Assignment Problem solver used natively by ByteTrack. |
| `pytest-asyncio`, `pytest-timeout` | `requirements-dev.txt` | **ACTIVE** | Pytest CLI execution plugins. |
| `onnx`, `onnxruntime` | `requirements-laptop.txt`| **ACTIVE** | Optional deployment runtime for laptop CPU ONNX acceleration. |

### Mobile (`traffic-camera-app`)
| Package | Manifest | Status | Usage Evidence |
|---|---|:---:|---|
| `axios` | `package.json` | **POTENTIALLY UNUSED** | Declared in `dependencies`, but never imported in `src/`. The mobile app communicates exclusively over WebSockets and WebRTC. |
| `expo-font` | `package.json` | **ACTIVE (PEER)** | Required peer dependency of `@expo/vector-icons` (enforced by NPM). |
| `react-native-screens` | `package.json` | **ACTIVE (PEER)** | Required native runtime dependency for `@react-navigation/native-stack`. |
| `react-native-nitro-image`, `nitro-modules` | `package.json` | **ACTIVE (PEER)** | Required C++ bindings for `react-native-vision-camera` v5 frame processors. |
| `@expo/ngrok` | `devDependencies` | **ACTIVE (DEV)** | Required for `--tunnel` remote development flag in Expo CLI. |

---

## 12. Git Hygiene Findings

1. **Tracked Diagnostic JPGs**:
   - `outputs/diagnostics/traffic_mobile_1280_q75.jpg` (75.4 KB)
   - `outputs/diagnostics/traffic_mobile_640_q65.jpg` (22.3 KB)
   - `outputs/diagnostics/traffic_source_crop.jpg` (172.5 KB)
   - `outputs/diagnostics/yolo26s_review.jpg` (203.1 KB)
   - `outputs/diagnostics/yolov8n_review.jpg` (229.4 KB)
   - *Finding*: `.gitignore` includes `outputs/*.mp4`, `outputs/training/`, `outputs/evaluations/`, but omitted `outputs/diagnostics/`. These test artifacts were accidentally tracked in Git.
2. **Tracked Frontend Dist**:
   - `web-ui/dist/` (321.2 KB) is tracked in Git.
   - *Finding*: While generated, this is currently an intentional architectural decision allowing the backend container to serve the web dashboard without requiring Node.js in production.
3. **Tracked Model Weights**:
   - `yolov8n.pt` (6.25 MB) is tracked in the repository root.
   - *Finding*: `.gitignore` specifies `models/*.pt`, which ignores files inside the `models/` directory, but not `./yolov8n.pt` in root. This tracking is intentional to allow fresh checkouts to run out-of-the-box without network downloads.

---

## 13. Root-Directory Findings

### `smart-traffic-management`
- `Frontend-Design-Specification.md` (69.1 KB): Large architecture design specification sitting in the repository root. Should be moved to `docs/` for clean repository root hygiene.
- `yolov8n.pt` (6.25 MB): Sits in root. Can optionally be relocated to `models/yolov8n.pt` (which `ModelManager` already supports as fallback), but leaving it in root is currently stable and backward-compatible.
- `.logs/`, `videos/`, `models/`: Empty directories in root. Can be safely kept as designated output locations or removed if not needed.

### `traffic-camera-app`
- `MOBILE_STREAMING_AUDIT_REPORT.md` (12.8 KB): Audit report sitting in root. Should be moved to a `docs/` folder for clean root hygiene.

---

## 14. Required Files That Must Be Preserved (DO NOT DELETE)

The following large or critical files must **NEVER** be deleted during cleanup:
1. `smart-traffic-management/yolov8n.pt` (6.25 MB): Core active YOLOv8n detector weights required for inference and regression tests.
2. `smart-traffic-management/tests/assets/model_regression/traffic_reference.jpg` (134.2 KB): Immutable golden-model reference test image.
3. `smart-traffic-management/web-ui/dist/` (321.2 KB): Pre-built React SPA bundle required for production web serving without Node.js.
4. `smart-traffic-management/.venv/` (1,475.71 MB): Active Python virtual environment containing the pre-configured dependencies.
5. `traffic-camera-app/node_modules/` (Base runtime: ~294 MB): Base JavaScript and native modules required to run and build the mobile app.
6. `traffic-camera-app/android/app/src/main/res/` (1.97 MB): App launcher icons and splashscreen brand assets.
7. Both `.git/` databases (186.13 MB and 37.70 MB): Required Git revision history.

---

## 15. Estimated Recoverable Disk Space

| Cleanup Group | Description | Space Recoverable | Safety Level |
|---|---|:---:|:---:|
| **Group 1: Safe Cache Cleanup** | Mobile Android C++ compilation intermediates (`.so`, `.pch`, `.cxx`) inside `node_modules`, backend logs, pycache, pytest cache | **3,118.88 MB** | **HIGH SAFETY** |
| **Group 2: Safe Build Artifacts** | Backend `web-ui/dist` (can be rebuilt via `npm run build`) | **0.31 MB** | **HIGH SAFETY** |
| **Group 3: Likely Unused** | Backend `outputs/diagnostics/*.jpg` (5 tracked review images) + historical SIH markdown docs | **0.76 MB** | **MEDIUM SAFETY** |
| **Group 4: Duplicates** | `tests/fixtures/ultralytics_bus.jpg` (duplicate of `traffic_reference.jpg`) | **0.13 MB** | **MEDIUM SAFETY** |
| **Group 5: Root Misplaced** | `Frontend-Design-Specification.md` and `MOBILE_STREAMING_AUDIT_REPORT.md` (relocation, not deletion) | **0.08 MB** (reorganized) | **HIGH SAFETY** |
| **Group 6: Legitimate Required Data** | Models, virtualenvs, clean node_modules, Git repositories, app icons | **0.00 MB** (MUST PRESERVE: 2,002.06 MB) | **DO NOT DELETE** |
| **TOTAL RECLAIMABLE DISK SPACE** | | **3,120.08 MB** (~3.05 GB) | |

---

## 16. Risk Assessment Matrix

| Target | Proposed Action | Risk | Impact if Deleted |
|---|---|:---:|---|
| `traffic-camera-app/node_modules/**/android/build` | Delete intermediate binaries | **NONE** | Next `expo run:android` will recompile C++ sources (~2 mins longer build time). Zero runtime impact. |
| `traffic-camera-app/node_modules/**/android/.cxx` | Delete CMake caches | **NONE** | CMake will regenerate on next Android build. |
| `smart-traffic-management/logs/*.log` | Truncate / delete | **NONE** | Historical debug logs cleared; new logs created on next run. |
| `smart-traffic-management/**/__pycache__` | Delete `.pyc` | **NONE** | Python automatically recompiles `.pyc` on module import. |
| `smart-traffic-management/.git/objects/44/tmp_obj_*` | Run `git prune` | **NONE** | Reclaims 23.88 MB of loose garbage pack files. |
| `smart-traffic-management/outputs/diagnostics/*.jpg` | Git untrack and remove | **LOW** | Review images from past model comparison removed; zero test or runtime impact. |
| `smart-traffic-management/web-ui/dist` | Delete | **MEDIUM** | If deleted without rebuilding, `run.py` will serve fallback HTML instead of React SPA until `npm run build` is re-run. |
| `traffic-camera-app` `axios` | Remove from `package.json` | **LOW** | Saves ~1.5 MB in `node_modules`; app does not import `axios`. |
| `smart-traffic-management/yolov8n.pt` | Delete | **CRITICAL** | System will crash on startup unless re-downloaded from Ultralytics CDN. **DO NOT DELETE**. |
| `smart-traffic-management/.venv` | Delete | **CRITICAL** | Destroys Python environment; requires full reinstall of PyTorch and OpenCV. **DO NOT DELETE**. |

---

## 17. Evidence for Recommendations

1. **Android Build Intermediates (3.11 GB)**:
   - Command `Get-ChildItem node_modules/expo-modules-core/android` revealed `.cxx` (472 MB) and `build` (897 MB).
   - The top 12 largest files across both repositories are duplicate copies of `libreactnative.so` (148.67 MB each) compiled for `arm64-v8a`, `x86_64`, `x86`, and `armeabi-v7a` across three separate modules (`expo-modules-core`, `react-native-screens`, `react-native-vision-camera`).
   - Proof of non-utility: These are build artifacts, not source files.
2. **`axios` in Mobile (Zero Imports)**:
   - AST and grep search across `traffic-camera-app/src` returned 0 matches for `axios`.
   - The mobile application strictly uses native WebSockets (`WebSocketConnectionService.ts`) and WebRTC (`WebRTCService.ts`).
3. **`outputs/diagnostics/*.jpg` (Tracked in Git)**:
   - `git ls-files outputs/` returned 5 JPEG files totaling 680.4 KB.
   - Searching the codebase revealed zero imports or references in `ai/`, `server/`, `web/`, or `tests/`.
4. **Duplicate Bus Asset (134.2 KB)**:
   - `sha256(tests/assets/model_regression/traffic_reference.jpg) == sha256(tests/fixtures/ultralytics_bus.jpg)`.
   - Both are identical 137,419-byte image files.

---

## 18. Recommended Cleanup Order (When Approved)

If and when a cleanup operation is authorized by the user, the following phased sequence guarantees 100% safety and zero broken dependencies:

1. **Step 1 — Zero-Risk Cache & Git Prune** (Reclaims ~27 MB):
   - Run `git -C smart-traffic-management prune`.
   - Delete `smart-traffic-management/logs/*.log`.
   - Delete all `__pycache__` and `.pytest_cache` directories.
2. **Step 2 — Mobile Android Intermediate Cleanup** (Reclaims ~3,115 MB / 3.04 GB):
   - In `traffic-camera-app`: Delete the `.cxx` and `build` subdirectories inside `node_modules/expo-modules-core/android`, `node_modules/react-native-vision-camera/android`, and `node_modules/react-native-screens/android`.
   - Or run `rm -rf node_modules package-lock.json && npm install` to restore `node_modules` to its clean, pre-build ~294 MB size.
3. **Step 3 — Unused Mobile Dependency Pruning** (Reclaims ~1.5 MB):
   - In `traffic-camera-app`: Remove `"axios"` from `package.json` dependencies and run `npm install`.
4. **Step 4 — Git Tracking Hygiene** (Reclaims ~0.7 MB from Git history / tree):
   - In `smart-traffic-management`: Remove `outputs/diagnostics/*.jpg` from Git tracking (`git rm --cached outputs/diagnostics/*.jpg`).
   - Add `outputs/diagnostics/` to `.gitignore`.
5. **Step 5 — Root Directory Reorganization** (Zero loss, improves repository cleanliness):
   - Move `Frontend-Design-Specification.md` into `smart-traffic-management/docs/`.
   - Move `MOBILE_STREAMING_AUDIT_REPORT.md` into `traffic-camera-app/docs/`.
   - Remove empty directories: `.logs/`, `videos/`.
