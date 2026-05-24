# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

VIGIA is a home fall-detection system. It runs on a Raspberry Pi 5 and consists of four components in a monorepo:

| Directory | Language | Purpose |
|---|---|---|
| `fall-detection/` | Python 3.10+ | Embedded agent — camera capture, YOLO pose estimation, SVM fall classification, FIWARE integration |
| `vigia-services/` | Go (workspace) | Cloud backend — `vigia-api` (REST API), `vigia-bootstrap` (Raspberry Pi CLI installer) |
| `vigia_ui/` | Flutter | Mobile app — receives Firebase push notifications on fall events |
| `docker-compose/` | Docker Compose | Local dev and production infra (Postgres, Redis, Keycloak, FIWARE stack, MediaMTX, Traefik) |

---

## fall-detection (Python)

### Environment setup
```bash
cd fall-detection
python -m venv .venv && source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate  # Windows

pip install -r requirements.txt          # dev (OpenCV GUI)
pip install -r requirements-debug.txt    # adds pytest, pytest-asyncio, pytest-cov
pip install -e .                         # install package in editable mode
```

Copy `.env.example` to `.env` and adjust `VIDEO_CAPTURE_SOURCE`, `YOLO_POSE_MODEL`, FIWARE variables, etc.

### Run
```bash
cd fall-detection
python main.py
```

### Lint & SAST
```bash
cd fall-detection
python -m pylint src/app
python -m bandit -r src/app -ll
```

### Tests
```bash
cd fall-detection
python -m pytest -q                                   # all tests
python -m pytest tests/unit/                          # unit tests only
python -m pytest tests/integration/ -m integration    # integration tests only (needs running FIWARE-like server)
python -m pytest tests/unit/command_bus_tests.py      # single file
python -m pytest --cov=src/app --cov-report=term-missing  # with coverage
```

Test files follow `*_tests.py` naming and `asyncio_mode = "auto"` is enabled globally.

### Build for Raspberry Pi (Linux ARM64)
```bash
cd fall-detection
make build-linux-arm64   # Requires Docker with buildx
```
Produces `dist/vigia-fall-detection-linux-arm64.tar.gz` for `scp` to the board.

---

## vigia-services (Go workspace)

### Structure
```
vigia-services/
  go.work                     # workspace linking all modules
  apps/vigia-api/             # REST API (Gin + fx + GORM + Redis)
  apps/vigia-bootstrap/       # Raspberry Pi CLI (Cobra) — installs/manages fall-detection
  pkg/shared/                 # shared logger and utils
```

### Run
```bash
cd vigia-services
make run-api                  # starts vigia-api on :8000
make run-bootstrap install    # runs the bootstrap install command
```

### Tests
```bash
cd vigia-services
make test-all                 # test-api + test-internal + test-bootstrap
make test-api                 # go test ./apps/vigia-api/cmd/...
make test-internal            # go test ./apps/vigia-bootstrap/internal/...
go test -run TestFoo ./apps/vigia-api/...   # single test
```

### Build
```bash
cd vigia-services
make build-all                          # builds both binaries to bin/
make build-linux-arm64-bootstrap        # ARM64 binary for the Pi
```

### Tidy
```bash
cd vigia-services
make tidy   # runs go mod tidy across all modules and syncs go.work
```

---

## vigia_ui (Flutter)

### Run & test
```bash
cd vigia_ui
flutter pub get
flutter analyze --fatal-warnings
dart format --output=none --set-exit-if-changed lib test
flutter test
```

Firebase credentials (`google-services.json` / `GoogleService-Info.plist`) are excluded from source control — copy from the `.example` counterparts before building.

---

## Local infrastructure (Docker Compose)

```bash
# Core services (Postgres + Keycloak) — used by vigia-api
cd docker-compose/local
cp .env.example .env   # fill secrets
docker compose up -d

# With FIWARE stack (Orion, IoT Agent, Mosquitto, STH Comet, Mongo)
docker compose --profile fiware up -d

# With RTMP/HLS streaming server for local tests
docker compose --profile stream-test up -d

# With MinIO (binary storage for vigia-api)
docker compose --profile storage up -d

# With Redis
docker compose --profile redis up -d
```

---

## Architecture: how the three fall-detection processes communicate

`runtime.py` launches three OS processes that communicate via ZMQ PUB/SUB and shared files:

```
[integration process]
    └─ registers device on FIWARE, listens MQTT commands, sends heartbeat
    └─ writes DATA_PATH/device/device.json  ──────────────────────────────┐
                                                                           │
[capture process]                                                          │
    └─ reads from camera (cv2.VideoCapture)                                │
    └─ publishes raw frames on ZMQ tcp://127.0.0.1:5557 (PUB)             │
    └─ optionally streams via RTMP → MediaMTX                             │
                                                                           ↓
[core/analysis process]                                            reads device.json
    └─ subscribes to ZMQ frames (SUB)
    └─ YOLO pose model → keypoints
    └─ SVM ONNX classifier → fall / no-fall
    └─ notifies FIWARE via posture_notifier when a fall is detected
```

Module status is written to `DATA_PATH/module_status.json` every 0.5 s. The integration process must start and signal readiness (via `multiprocessing.Event`) before capture and core are launched.

---

## Architecture: vigia-api & vigia-bootstrap deployment flow

1. **vigia-api** (`vigia-services/apps/vigia-api`) stores versioned PyInstaller bundles in S3/MinIO and exposes `/v1/devices/version/find-for-updates` + `/:version/download`.
2. **vigia-bootstrap** (CLI on the Pi) calls `install` to download the latest bundle, extracts it, and registers a systemd unit (`fall-detection.service`). Commands: `install`, `start`, `stop`, `restart`, `update`.
3. The Pi systemd unit runs `vigia-fall-detection` (PyInstaller onedir binary).

---

## CI pipeline (GitHub Actions)

`.github/workflows/continuos-integration.yml` uses path-based change detection (dorny/paths-filter) to run only the affected project's quality gate on each PR:

- **Python**: pylint → bandit (SAST) → pip-audit → pytest + coverage
- **Go**: golangci-lint → gosec (SAST) → govulncheck → go test -race + coverage
- **Flutter**: dart format → flutter analyze → dart pub audit → flutter test
- **All**: Gitleaks secret scan always runs; Hadolint for changed Dockerfiles

The required status check to set in branch protection is `CI gate` (the consolidation job).
