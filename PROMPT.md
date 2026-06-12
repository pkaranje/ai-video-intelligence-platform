# PROMPT.md — Build Sequence

## How to use

Each step = one prompt. Copy the text inside the prompt block and paste
into Claude Code. Nothing else needed — CLAUDE.md is read automatically.

**Rules:**
- One step at a time. Verify before continuing.
- If verification fails, fix it before the next step.
- Use the model shown for each step.

## Model guide

| Phase | Steps | Model |
|---|---|---|
| Phase 0 — Root + libs | 1–3 | `claude-haiku-4-5` |
| Phase 1 — API backend | 4–9 | `claude-sonnet-4-6` |
| Phase 2 — Frontend | 10–14 | `claude-sonnet-4-6` |
| Phase 3 — Extractor | 15–19 | `claude-haiku-4-5` / `claude-sonnet-4-6` |
| Phase 4 — Worker | 20–25 | `claude-sonnet-4-6` |
| Phase 5 — Quality | 26–28 | `claude-sonnet-4-6` / `claude-haiku-4-5` |

---

## Phase 0 — Root scaffold + libs

---

### Step 1 — Repo root files
**Model: `claude-haiku-4-5`**

```
Read CLAUDE.md fully before starting.

Create these repo root files:

── .gitignore
Python:  __pycache__/, *.py[cod], .venv/, .pytest_cache/, .ruff_cache/,
         *.egg-info/, dist/, .coverage, htmlcov/
Env:     .env, .env.docker, .env.docker.db, .env.docker.api,
         .env.docker.extractor, .env.docker.worker
         (NOT *.example files — those are committed)
Node:    node_modules/, .next/, frontend/out/
Data:    data/
IDE:     .vscode/, .idea/, *.swp
Docker:  .dockerignore is NOT gitignored
Note:    uv.lock files are NOT ignored — commit them

── .dockerignore  (repo root — applies to all Docker builds)
.git/
.venv/
**/.venv/
**/__pycache__/
**/*.pyc
**/.pytest_cache/
**/.ruff_cache/
**/node_modules/
**/.next/
.env
.env.docker
.env.docker.*
!.env.docker.*.example
**/tests/
*.md
.github/

── .env.example
All variables from CLAUDE.md environment variables table.
Group by: Database, Redis, AI, Extraction, Workers, Cleanup, Frontend.
Placeholder values. One comment per line.

── .env.docker.db.example
# Shared by: postgres, api, extractor, worker
POSTGRES_DB=videosumm
POSTGRES_USER=postgres
POSTGRES_PASSWORD=change_me
DATABASE_URL=postgresql+asyncpg://postgres:change_me@ai-video-intelligence-postgres:5432/videosumm
REDIS_URL=redis://ai-video-intelligence-redis:6379

── .env.docker.api.example
# Used by: api only
DATA_ROOT=/data
MAX_FILE_SIZE_MB=500
MAX_DURATION_SEC=600
BATCH_SIZE=5
JOB_TTL_DAYS=7
FAILED_JOB_TTL_DAYS=1
# DevTrack dashboard: http://localhost:8000/__devtrack__/dashboard

── .env.docker.extractor.example
# Used by: ffmpeg-extractor only
DATA_ROOT=/data
SCENE_THRESHOLD=0.35
FRAME_INTERVAL=150
BATCH_SIZE=5
MAX_DURATION_SEC=600
FFMPEG_BIN=ffmpeg
FFPROBE_BIN=ffprobe

── .env.docker.worker.example
# Used by: worker-1..4, scheduler
DATA_ROOT=/data

# ── AI Provider ───────────────────────────────────────────
# Option 1: OpenAI (production)
#   AI_MODEL=gpt-4o
#   AI_BASE_URL=
#   OPENAI_API_KEY=sk-...
#
# Option 2: Gemini Flash 2.0 (production, cost-efficient)
#   AI_MODEL=gemini-2.0-flash
#   AI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
#   OPENAI_API_KEY=your_google_ai_studio_key
#
# Option 3: Ollama local — FIXED to qwen2.5vl:3b (fits 8GB RAM)
#   AI_MODEL=qwen2.5vl:3b        ← 3b only — 7b won't fit in 8GB with Docker
#   AI_BASE_URL=http://ai-video-intelligence-ollama:11434/v1
#   OPENAI_API_KEY=ollama
#   Run: make up-ollama (starts 1 worker + ollama, not 4 workers)
#
AI_MODEL=gpt-4o
AI_BASE_URL=
OPENAI_API_KEY=change_me
AGGREGATION_MODEL=gpt-4o

MAX_RETRIES=3
MIN_BACKOFF_SEC=15
MAX_BACKOFF_SEC=120
BATCH_SIZE=5
JOB_TTL_DAYS=7
FAILED_JOB_TTL_DAYS=1
CLEANUP_CRON=0 2 * * *

── scripts/ollama-entrypoint.sh
  #!/bin/sh
  set -e
  ollama serve &
  OLLAMA_PID=$!
  echo "Waiting for Ollama to start..."
  until curl -sf http://localhost:11434/api/tags > /dev/null 2>&1; do
    sleep 1
  done
  echo "Ollama ready."
  if ! ollama list | grep -q "${OLLAMA_MODEL:-qwen2.5vl:3b}"; then
    echo "Pulling ${OLLAMA_MODEL:-qwen2.5vl:3b}..."
    ollama pull "${OLLAMA_MODEL:-qwen2.5vl:3b}"
    echo "Model ready."
  else
    echo "Model already present — skipping pull."
  fi
  wait $OLLAMA_PID
  Make executable: chmod +x scripts/ollama-entrypoint.sh

── pyproject.toml  (root — tooling config only, NOT a package, NOT a workspace)
[tool.ruff] line-length=100, target-version="py312"
[tool.ruff.lint] select=["E","F","I","UP","B","SIM"]
[tool.pytest.ini_options] asyncio_mode="auto"

── docker-compose.yml  (skeleton — services added in later steps)
version: "3.9"

networks:
  ai-video-intelligence:
    driver: bridge
    name: ai-video-intelligence   ← explicit name prevents project prefix

volumes:
  ai-video-intelligence-postgres-data:
    name: ai-video-intelligence-postgres-data
  ai-video-intelligence-redis-data:
    name: ai-video-intelligence-redis-data
  ai-video-intelligence-app-data:
    name: ai-video-intelligence-app-data
  ai-video-intelligence-ollama-data:
    name: ai-video-intelligence-ollama-data   ← model cache — survives restarts

Run: make env-check
```

**Verify:**
- [ ] `.env.docker.*` files are gitignored, `.env.docker.*.example` files are NOT
- [ ] `.dockerignore` exists at repo root
- [ ] `make env-check` creates all four `.env.docker.*` files
- [ ] `docker-compose.yml` has `name:` on all volumes and network

---

### Step 2 — Root Makefile
**Model: `claude-haiku-4-5`**

```
Create the root Makefile exactly as shown in the Makefile deliverable.

Key requirements:
- COMPOSE := docker compose  (v2, never docker-compose v1)
- All up-* targets use --build flag
- env-check copies each .env.docker.*.example → .env.docker.* if missing
  and exits with error if any .example file is missing
- db-migrate delegates via $(MAKE) -C services/api db-migrate
  services/api/Makefile handles the /.dockerenv detection
- test loops: services/api → services/extractor → services/worker

Wildcard delegation:
  shared-%:    $(MAKE) -C libs/shared $*
  api-%:       $(MAKE) -C services/api $*
  extractor-%: $(MAKE) -C services/extractor $*
  worker-%:    $(MAKE) -C services/worker $*
  frontend-%:  $(MAKE) -C frontend $*

All up-* targets print after starting:
  API      → http://localhost:8000/health
  Docs     → http://localhost:8000/docs
  DevTrack → http://localhost:8000/__devtrack__/dashboard
  UI       → http://localhost:3000  (where applicable)

Targets: env-check, install, lint, lint-fix, test,
  build, build-no-cache, up, up-dev, up-api, up-frontend,
  up-extractor, up-workers, up-ollama, down, down-all, restart, logs, ps, health,
  db-migrate, db-rollback, db-reset,
  ollama-pull, ollama-list,
  clean, clean-all, clean-volumes

up-ollama:
  Starts: postgres + redis + api + ffmpeg-extractor + worker-1 + ollama + scheduler
  NOTE: only 1 worker — keeps within 8GB RAM budget alongside Ollama
  Prints after start:
    Ollama → http://localhost:11434
    API    → http://localhost:8000/health
    Note: first run downloads qwen2.5vl:3b (~2GB) — allow 2-5 min

ollama-pull:
  docker compose exec ai-video-intelligence-ollama ollama pull $(MODEL)
  Usage: make ollama-pull MODEL=qwen2.5vl:3b

ollama-list:
  docker compose exec ai-video-intelligence-ollama ollama list
```

**Verify:**
- [ ] `make help` prints all targets
- [ ] `make env-check` works with split env files
- [ ] No `docker-compose` (v1) anywhere — only `docker compose`

---

### Step 3 — libs/shared
**Model: `claude-haiku-4-5`**

```
Read CLAUDE.md — shared package section and import boundary table.

STRUCTURE RULE — two levels only:
  libs/shared/         ← project directory (NOT a Python package)
  libs/shared/shared/  ← Python package named "shared"
Do NOT create libs/shared/shared/shared/.

Create:

libs/shared/pyproject.toml
  [project]
  name = "shared"
  version = "0.1.0"
  requires-python = ">=3.12"
  dependencies = ["loguru>=0.7", "dramatiq>=1.16"]
  [build-system]
  requires = ["hatchling"]
  build-backend = "hatchling.build"
  [tool.hatch.build.targets.wheel]
  packages = ["shared"]
  [tool.uv]
  dev-dependencies = ["ruff>=0.4"]

libs/shared/Makefile
  Targets: install (uv sync), lint, lint-fix, clean, clean-all, help
  help prints the import boundary from CLAUDE.md.

libs/shared/shared/__init__.py  (empty)

libs/shared/shared/middleware.py
  ActorMetricsMiddleware as defined in CLAUDE.md.
  Imports: time, dramatiq, loguru logger.
  before_process_message: message.options["started_at"] = time.monotonic()
  after_process_message: logger.info("actor_completed", actor, queue,
    duration_ms, status, job_id, retries)

libs/shared/shared/messages.py
  from dataclasses import dataclass
  ExtractionMessage(job_id: str)
  AnalysisBatchMessage(job_id: str, frame_ids: list[str])
  AggregationMessage(job_id: str)
  stdlib only — no external imports.

Run: cd libs/shared && make install
```

**Verify:**
- [ ] `libs/shared/shared/` has `__init__.py`, `middleware.py`, `messages.py`
- [ ] No `libs/shared/shared/shared/` directory
- [ ] `cd libs/shared && uv run python -c "from shared.middleware import ActorMetricsMiddleware; print('OK')"`
- [ ] `cd libs/shared && uv run python -c "from shared.messages import ExtractionMessage; print('OK')"`

---

## Phase 1 — API backend

---

### Step 4 — API scaffold and config
**Model: `claude-sonnet-4-6`**

```
Read CLAUDE.md — api service section, environment variables.

STRUCTURE RULE — two levels only:
  services/api/       ← service root
  services/api/api/   ← Python package named "api"
Do NOT create services/api/api/api/.
pyproject.toml, Makefile, Dockerfile, alembic.ini go in services/api/.
All Python source goes inside services/api/api/.

── services/api/pyproject.toml
[project]
name = "api"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
  "fastapi>=0.115", "uvicorn[standard]>=0.30", "pydantic-settings>=2.0",
  "sqlalchemy[asyncio]>=2.0", "asyncpg>=0.29", "alembic>=1.13",
  "redis>=5.0", "dramatiq[redis]>=1.16", "structlog>=24.0", "loguru>=0.7",
  "python-multipart>=0.0.9", "devtrack-sdk",
  "shared @ { path = '../../libs/shared', develop = true }",
]
dev-dependencies: pytest>=8.0, pytest-asyncio>=0.23, httpx>=0.27, ruff>=0.4
[tool.hatch.build.targets.wheel]
packages = ["api"]
[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"

── services/api/.gitignore
__pycache__/, *.py[cod], .venv/, .pytest_cache/, .ruff_cache/

── services/api/Makefile
install    uv sync
lint       uv run ruff check api/ && uv run ruff format --check api/
lint-fix   uv run ruff check --fix api/ && uv run ruff format api/
test-unit  uv run pytest tests/unit/ -v
test-integration  uv run pytest tests/integration/ -v
test       test-unit then test-integration

db-migrate and db-rollback and db-reset must detect environment:
  if [ -f /.dockerenv ]; then
    run alembic directly (already inside container)
  else
    docker compose -f ../../docker-compose.yml exec api alembic upgrade head
  fi

shell        docker compose -f ../../docker-compose.yml exec api-video-intelligence-api /bin/bash
shell-db     docker compose -f ../../docker-compose.yml exec ai-video-intelligence-postgres psql -U postgres -d videosumm
shell-redis  docker compose -f ../../docker-compose.yml exec ai-video-intelligence-redis redis-cli
clean        remove __pycache__, .pytest_cache, .ruff_cache
clean-all    clean + remove .venv
help

── services/api/api/__init__.py  (empty)
── services/api/api/core/__init__.py  (empty)

── services/api/api/core/config.py
Settings(BaseSettings) with @lru_cache.
Fields: DATABASE_URL, REDIS_URL, MAX_FILE_SIZE_MB=500,
MAX_DURATION_SEC=600, DATA_ROOT="/data", BATCH_SIZE=5,
JOB_TTL_DAYS=7, FAILED_JOB_TTL_DAYS=1.

── services/api/api/core/logging.py
configure_logging(): structlog JSON renderer + loguru sink.
LoggerMixin: self.logger for any class.
log_call decorator: logs entry, exit, elapsed_ms.

Run: cd services/api && make install
Confirm no services/api/api/api/ exists.
```

**Verify:**
- [ ] No `services/api/api/api/` directory
- [ ] `cd services/api && make install` succeeds
- [ ] `cd services/api && uv run python -c "from api.core.config import get_settings; print('OK')"`

---

### Step 5 — API domain and database
**Model: `claude-sonnet-4-6`**

```
Read CLAUDE.md — database schema section.
Working in services/api/.

Create domain (zero external imports in any domain file):

── services/api/api/domain/__init__.py  (empty)

── services/api/api/domain/video.py
VideoStatus enum: queued, running, completed, failed
UploadTooLargeError(ValueError), UnsupportedFormatError(ValueError)
validate_upload(filename, content_type, size_bytes) -> None
  UnsupportedFormatError if content_type != "video/mp4"
  UploadTooLargeError if size_bytes > MAX_FILE_SIZE_MB * 1024 * 1024

── services/api/api/domain/frame.py
SelectionReason enum: scene_change, periodic, both
FrameValidationError
validate_frame_metadata(metadata: dict) -> None
  required keys: video_id, frame_id, frame_path, timestamp,
  frame_number, selection_reason

── services/api/api/domain/summary.py
MalformedAggregationError
AggregationResult dataclass: summary (str), timeline (list[dict])
validate_timeline(timeline: list) -> None
  each item needs timestamp (float) and event (str)

Create database models:

── services/api/api/db/__init__.py  (empty)

── services/api/api/db/models.py
Async SQLAlchemy Base. All 4 tables from CLAUDE.md schema.
videos: all columns including expires_at TIMESTAMPTZ, cleaned_at TIMESTAMPTZ.
frames: all columns including created_at TIMESTAMPTZ.
frame_analysis: id, frame_id FK, ai_response JSONB, description TEXT,
  model_used TEXT, created_at TIMESTAMPTZ.
video_summary: id, video_id FK UNIQUE, summary TEXT, timeline JSONB,
  is_partial BOOL DEFAULT FALSE, model_used TEXT, generated_at TIMESTAMPTZ.
UUID primary keys. TIMESTAMPTZ for all timestamps.

Create Alembic:

── services/api/alembic.ini  (script_location = alembic)

── services/api/alembic/env.py
Async-compatible, asyncio + asyncpg.
Import Base from api.db.models.

── services/api/alembic/versions/0001_initial.py
Creates all 4 tables with every column.
expires_at and cleaned_at must be in this migration.

NOTE: Do NOT run make db-migrate here.
Migrations run automatically when the container starts (Step 8).
```

**Verify:**
- [ ] All 4 table models exist with correct columns
- [ ] No imports outside stdlib in any domain file
- [ ] `uv run python -c "from api.db.models import Base; print('OK')"` succeeds

---

### Step 6 — API repositories and services
**Model: `claude-sonnet-4-6`**

```
Read CLAUDE.md — repository and service layer rules.
Working in services/api/. No business logic in repositories.
All repositories inherit LoggerMixin.

Repositories:

── services/api/api/repositories/__init__.py
BaseRepository(LoggerMixin)

── services/api/api/repositories/job_repo.py
JobRepository(BaseRepository) — async SQLAlchemy only.
create(filename, file_size_bytes, duration_seconds, resolution, fps) -> Job
  sets status=queued, stage=upload_validation
get_by_id(job_id) -> Job | None
update_status(job_id, status, stage, error_message=None) atomic UPDATE
update_progress(job_id, progress_pct)
mark_completed(job_id)
  status=completed, stage=completed, progress_pct=100,
  completed_at=NOW(), expires_at=NOW()+JOB_TTL_DAYS
mark_failed(job_id, stage, error_message, ttl_days)
  status=failed, expires_at=NOW()+ttl_days
get_expired_jobs() -> list[Job]
  WHERE expires_at < NOW() AND cleaned_at IS NULL
  AND status IN ('completed','failed')
is_analysis_complete(job_id) -> bool
mark_cleaned(job_id)

── services/api/api/repositories/frame_repo.py
FrameRepository(BaseRepository)
bulk_insert_frames(frames: list[dict]) -> list[str]
get_frames_for_job(job_id) -> list[Frame]
get_descriptions_for_job(job_id) -> list[dict]
  JOIN frames + frame_analysis ORDER BY timestamp ASC
  returns [{timestamp, description}]

── services/api/api/repositories/ffprobe_client.py
FFprobeResult dataclass: duration_seconds, fps, width, height, codec
FFprobeError
FFprobeClient.probe(video_path) -> FFprobeResult
  ffprobe -v quiet -print_format json -show_format -show_streams
  asyncio.create_subprocess_exec. Raise FFprobeError on failure.

Services (orchestrate — no SQL):

── services/api/api/services/__init__.py
BaseService(LoggerMixin)

── services/api/api/services/upload.py
UploadService.upload(file: UploadFile) -> UploadResponse
Exact order:
  validate_upload() → write {DATA_ROOT}/uploads/{job_id}.mp4
  → FFprobeClient.probe() → raise if duration > MAX_DURATION_SEC
  → job_repo.create() → enqueue_extraction(job_id)
  → return UploadResponse

── services/api/api/services/status.py
StatusService.get(job_id) -> StatusResponse
404 if not found. Map all DB fields.

── services/api/api/services/summary.py
SummaryService.get_summary(job_id) -> SummaryResponse
SummaryService.get_timeline(job_id) -> TimelineResponse
Both 404 if job not completed.
```

**Verify:**
- [ ] All files import without error
- [ ] No raw SQL in any service file
- [ ] No business logic in any repository file

---

### Step 7 — API queue, schemas, routes, main
**Model: `claude-sonnet-4-6`**

```
Read CLAUDE.md — API endpoints, observability sections.
Working in services/api/.

── services/api/api/queue/__init__.py  (empty)

── services/api/api/queue/publisher.py
CRITICAL: Broker must be configured with REDIS_URL before any actor is declared.
Do NOT rely on Dramatiq's default (it uses localhost:6379).
Do NOT import from services/extractor — zero cross-service imports.

from dramatiq.brokers.redis import RedisBroker
from api.core.config import get_settings
from shared.messages import ExtractionMessage
import dramatiq
from loguru import logger

def _configure_broker() -> None:
    broker = RedisBroker(url=get_settings().REDIS_URL)
    dramatiq.set_broker(broker)

_configure_broker()

# Stub actor — declared here so API can enqueue without importing extractor.
# Real implementation lives in services/extractor/extractor/queue/consumer.py.
# Both declare queue_name="extraction" — Dramatiq routes by queue name.
@dramatiq.actor(queue_name="extraction")
def extraction_task(job_id: str) -> None:  # pragma: no cover
    raise NotImplementedError("Stub — never executed in the API process.")

def enqueue_extraction(job_id: str) -> None:
    msg = ExtractionMessage(job_id=job_id)
    logger.info("extraction_enqueued", job_id=msg.job_id)
    extraction_task.send(job_id=msg.job_id)

── services/api/api/schemas/__init__.py  (empty)

── services/api/api/schemas/common.py
ErrorDetail(message: str, code: str), HealthResponse(status: str)

── services/api/api/schemas/video.py
ProgressStage Literal:
  upload_validation, frame_extraction, ai_analysis, aggregation, completed
JobStatus Literal: queued, running, completed, failed
UploadResponse(job_id: str, status: str)
StatusResponse(job_id, status, stage, progress_pct,
  error_message, created_at, updated_at)

── services/api/api/schemas/summary.py
TimelineEvent(timestamp: float, event: str)
SummaryResponse(job_id, summary, word_count, generated_at)
TimelineResponse(job_id, timeline: list[TimelineEvent])

── services/api/api/core/dependencies.py
get_db() -> AsyncSession
get_redis() -> Redis
get_job_repo(), get_frame_repo()
get_upload_service(), get_status_service(), get_summary_service()

── services/api/api/core/middleware.py
RequestLoggingMiddleware:
  UUID request_id per request, bind to structlog context.
  Log method, path, status_code, duration_ms on every response.

── services/api/api/routes/__init__.py  (empty)
── services/api/api/routes/health.py
  GET /health → HealthResponse(status="ok")
  NOTE: mounted WITHOUT /api/v1 prefix in main.py

── services/api/api/routes/videos.py    POST /api/v1/videos → 202 UploadResponse
── services/api/api/routes/status.py    GET /api/v1/videos/{job_id}/status
── services/api/api/routes/summary.py   GET /api/v1/videos/{job_id}/summary
── services/api/api/routes/timeline.py  GET /api/v1/videos/{job_id}/timeline
── services/api/api/routes/frames.py    GET /api/v1/videos/{job_id}/frames

── services/api/api/main.py
FastAPI(title="AI Video Intelligence Platform", lifespan=lifespan)

Router mounting — EXACT order and prefixes:
  app.include_router(devtrack_router)            # no prefix — devtrack owns its paths
  app.include_router(health.router)              # no prefix → /health
  app.include_router(videos.router, prefix="/api/v1")
  app.include_router(status.router, prefix="/api/v1")
  app.include_router(summary.router, prefix="/api/v1")
  app.include_router(timeline.router, prefix="/api/v1")
  app.include_router(frames.router, prefix="/api/v1")

Middleware — EXACT order (last added = first executed):
  app.add_middleware(DevTrackMiddleware,
    exclude_path=["/docs", "/redoc", "/openapi.json"])
  app.add_middleware(RequestLoggingMiddleware)

lifespan():
  configure_logging()
  create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
  async_sessionmaker stored on app.state
  Redis.from_url(settings.REDIS_URL) stored on app.state
  Teardown: redis.aclose() + engine.dispose()

Imports:
  from devtrack_sdk.controller import router as devtrack_router
  from devtrack_sdk.middleware import DevTrackMiddleware
```

**Verify:**
- [ ] `cd services/api && uv run python -c "from api.main import app; print('OK')"`
- [ ] `GET /health` not `/api/v1/health` — no prefix on health route
- [ ] ProgressStage + JobStatus values match CLAUDE.md exactly
- [ ] `cd services/api && uv run python -c "from api.queue.publisher import enqueue_extraction; print('OK')"`

---

### Step 8 — API Dockerfile, docker-compose, smoke test
**Model: `claude-haiku-4-5`**

```
Create services/api/Dockerfile.
Build context is repo root. All paths relative to repo root.

FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app/services/api

WORKDIR /app

RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install uv

# Install shared lib (needed by pyproject.toml dependency resolution)
COPY libs/shared ./libs/shared/

# Install Python deps (cache layer — only rebuilds when pyproject.toml changes)
COPY services/api/pyproject.toml ./services/api/
WORKDIR /app/services/api
RUN uv sync --no-dev

# Copy source AFTER deps — preserves cache when only source changes
COPY services/api/api ./api/
COPY services/api/alembic ./alembic/
COPY services/api/alembic.ini ./alembic.ini

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]

Update docker-compose.yml — add postgres, redis, api services:

postgres:
  container_name: ai-video-intelligence-postgres
  image: postgres:16-alpine
  volumes:
    - ai-video-intelligence-postgres-data:/var/lib/postgresql/data
  env_file:
    - .env.docker.db
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-postgres} -d ${POSTGRES_DB:-videosumm}"]
    interval: 5s
    timeout: 5s
    retries: 5
    start_period: 5s
  restart: unless-stopped
  networks:
    - ai-video-intelligence

redis:
  container_name: ai-video-intelligence-redis
  image: redis:7-alpine
  volumes:
    - ai-video-intelligence-redis-data:/data
  healthcheck:
    test: ["CMD", "redis-cli", "ping"]
    interval: 5s
    timeout: 5s
    retries: 5
    start_period: 5s
  restart: unless-stopped
  networks:
    - ai-video-intelligence

api:
  container_name: ai-video-intelligence-api
  build:
    context: .
    dockerfile: services/api/Dockerfile
  ports:
    - "8000:8000"
  env_file:
    - .env.docker.db
    - .env.docker.api
  volumes:
    - ai-video-intelligence-app-data:/data
  depends_on:
    postgres:
      condition: service_healthy
    redis:
      condition: service_healthy
  command: >
    sh -c "
      echo 'Running migrations...' &&
      alembic upgrade head &&
      echo 'Starting server...' &&
      uvicorn api.main:app --host 0.0.0.0 --port 8000
    "
  healthcheck:
    test: ["CMD", "curl", "-fsS", "http://localhost:8000/health"]
    interval: 5s
    timeout: 2s
    retries: 5
    start_period: 10s
  restart: unless-stopped
  networks:
    - ai-video-intelligence

Run:
  make up-api
  curl http://localhost:8000/health
Report the response.
```

**Verify:**
- [ ] `make up-api` — 3 services healthy
- [ ] `GET /health` → `{"status":"ok"}`
- [ ] Logs show "Running migrations..." then "Starting server..."
- [ ] `POST /api/v1/videos` with MP4 → `202` + `job_id`
- [ ] `GET /api/v1/videos/{job_id}/status` → `{"status":"queued"}`

---

### Step 9 — Unit tests for API domain
**Model: `claude-sonnet-4-6`**

```
Each service owns its tests. Unit tests only in this step.

Create:
services/api/tests/__init__.py  (empty)
services/api/tests/unit/__init__.py  (empty)

services/api/tests/unit/test_domain_video.py
  validate_upload happy path: valid MP4, valid size
  validate_upload raises UnsupportedFormatError: content_type != video/mp4
  validate_upload raises UploadTooLargeError: size > MAX_FILE_SIZE_MB * 1024 * 1024
  validate_upload boundary: exactly at size limit passes

services/api/tests/unit/test_domain_frame.py
  validate_frame_metadata happy path: all required keys present
  raises FrameValidationError for each missing required key individually

services/api/tests/unit/test_domain_summary.py
  validate_aggregation_json happy path: valid JSON with summary + timeline
  validate_aggregation_json: markdown fences stripped before parsing
  validate_aggregation_json: missing fields raise MalformedAggregationError
  validate_timeline happy path
  raises MalformedAggregationError: missing timestamp or event

Rules: no mocks, no DB — domain is pure functions.

services/api/Makefile test-unit target:
  uv run pytest tests/unit/ -v

Run: cd services/api && make test-unit
Report pass/fail count.
```

**Verify:**
- [ ] `services/api/tests/unit/` has 3 test files
- [ ] `cd services/api && make test-unit` all green
- [ ] No mocks or DB connections in unit tests

---

## Phase 2 — Frontend

---

### Step 10 — Frontend scaffold and types
**Model: `claude-sonnet-4-6`**

```
Read CLAUDE.md — frontend section, API endpoints.
make up-api must be running first.

1. Run: npx create-next-app@latest frontend
   App Router: yes, TypeScript: yes, Tailwind: yes,
   src/ directory: yes, import alias @/*: yes.

2. frontend/next.config.ts
   output: 'standalone'
   No rewrites — proxy is a Route Handler not a rewrite rule.

3. frontend/tsconfig.json  strict: true
   Path aliases: @/components, @/lib, @/types

4. frontend/.gitignore
   .next/, out/, node_modules/, .env.local, .env.*.local

5. frontend/.env.local.example
   NEXT_PUBLIC_API_URL=/api/proxy
   BACKEND_URL=http://localhost:8000

6. frontend/Makefile
   install (npm ci), dev, build, typecheck (npx tsc --noEmit),
   lint, lint-fix, shell, logs,
   clean (.next/ out/), clean-all (clean + node_modules/), help

7. frontend/src/lib/constants.ts
   POLL_INTERVAL_MS = 3000
   MAX_FILE_SIZE_BYTES = 500 * 1024 * 1024
   ACCEPTED_TYPES = ['video/mp4']

8. frontend/src/lib/api/types.ts
   JobStatus: 'queued' | 'running' | 'completed' | 'failed'
   ProgressStage: 'upload_validation' | 'frame_extraction' | 'ai_analysis' |
     'aggregation' | 'completed'
   UploadResponse, StatusResponse, TimelineEvent,
   SummaryResponse, TimelineResponse
   APIError extends Error with status: number

9. frontend/src/lib/api/client.ts
   fetchAPI(path, init?): prepends NEXT_PUBLIC_API_URL
   Throws APIError on non-2xx.

10. frontend/src/lib/api/videos.ts
    uploadVideo(file), getStatus(jobId), getSummary(jobId), getTimeline(jobId)

11. frontend/src/types/index.ts  (re-export lib/api/types.ts)

Run: cd frontend && make install && make typecheck
```

**Verify:**
- [ ] `make install` succeeds
- [ ] `make typecheck` zero errors
- [ ] ProgressStage + JobStatus match CLAUDE.md exactly

---

### Step 11 — Frontend utilities and hooks
**Model: `claude-sonnet-4-6`**

```
Working in frontend/. Continue from Step 10.

frontend/src/lib/utils/format.ts
  formatTimestamp(seconds: number): string
    83.5 → "1m 23s", 45.0 → "45s", 0 → "0s"
  formatBytes(bytes: number): string  → "1.2 MB"

frontend/src/lib/utils/validation.ts
  validateFileType(file): { valid: boolean; message?: string }
    valid only if file.type === 'video/mp4'
  validateFileSize(file): { valid: boolean; message?: string }
    valid only if file.size <= MAX_FILE_SIZE_BYTES

frontend/src/lib/hooks/useJobPoller.ts
  useJobPoller(jobId: string, initialStatus: StatusResponse)
  setInterval at POLL_INTERVAL_MS while status queued|running.
  Clears interval on completed, failed, or unmount.
  Returns: { status, error, isLoading }

frontend/src/lib/hooks/useUpload.ts
  State machine: idle → uploading → polling → done | error
  Must use XMLHttpRequest not fetch (needed for progress events).
  upload(file): validate type + size first, XHR POST to /api/proxy/api/v1/videos
  NOTE: proxy forwards to BACKEND_URL + path, so full URL becomes:
    /api/proxy/api/v1/videos → http://ai-video-intelligence-api:8000/api/v1/videos
  Tracks upload progress percentage.
  On 202: extract job_id, transition to polling.
  Returns: { state, jobId, uploadProgress, upload, error }

Run: cd frontend && make typecheck
```

**Verify:**
- [ ] `make typecheck` zero errors
- [ ] `useUpload` uses XHR not fetch
- [ ] Upload path is `/api/proxy/api/v1/videos` not `/api/proxy/videos`

---

### Step 12 — Frontend components
**Model: `claude-sonnet-4-6`**

```
Working in frontend/. Continue from Step 11.
Follow Server/Client split from CLAUDE.md exactly.

UI primitives (all Server Components):
  components/ui/Badge.tsx    variant prop → Tailwind colour classes
  components/ui/Button.tsx   polymorphic, as prop defaults to "button"
  components/ui/Card.tsx     shadow card wrapper
  components/ui/Spinner.tsx  animated loading indicator

Upload ('use client'):
  components/upload/FileDropzone.tsx
    Native HTML5 drag-and-drop, no library.
    Run validateFileType() then validateFileSize() before accepting.
    Show inline error on failure. Call onFileAccepted(file) on success.
  components/upload/UploadProgress.tsx
    Progress bar from percent: number prop.
  components/upload/UploadCard.tsx
    Composes FileDropzone + UploadProgress.
    Uses useUpload(). router.push('/jobs/'+jobId) on done.

Job status:
  components/job/StageBadge.tsx  (Server)
    upload_validation=grey, frame_extraction=blue, ai_analysis=purple,
    aggregation=amber, completed=green
  components/job/ErrorBanner.tsx  (Server)
    Shows error_message. Returns null if message is null.
  components/job/JobStatusClient.tsx  ('use client')
    Props: jobId, initialStatus: StatusResponse.
    Uses useJobPoller(jobId, initialStatus).
    Renders: StageBadge, progress bar, ErrorBanner.
    On completed: fetch summary + timeline, show SummaryCard + TimelineList.

Summary (both Server):
  components/summary/SummaryCard.tsx — summary text, word_count, generated_at
  components/summary/TimelineList.tsx
    Left: formatTimestamp(event.timestamp) in Badge. Right: event.event string.

Run: cd frontend && make typecheck && make lint
```

**Verify:**
- [ ] `make typecheck` zero errors
- [ ] `make lint` passes
- [ ] No 'use client' on Server Components

---

### Step 13 — Frontend pages and proxy
**Model: `claude-sonnet-4-6`**

```
Working in frontend/. Continue from Step 12.

src/app/globals.css  Tailwind directives only.
src/app/layout.tsx   (Server) RootLayout, Inter font, globals.css.
src/app/page.tsx     (Server) Hero heading + <UploadCard />. No data fetching.

src/app/jobs/[jobId]/loading.tsx   Skeleton placeholders.
src/app/jobs/[jobId]/error.tsx     ('use client') Error boundary + retry button.
src/app/jobs/[jobId]/page.tsx      (Server Component)
  Fetch initial status using BACKEND_URL directly — avoids loading flash.
  Pass initialStatus to <JobStatusClient>.
  Wrap in <Suspense>.

src/app/api/proxy/[...path]/route.ts
  Catch-all Route Handler.
  BACKEND_URL from process.env only — NEVER from NEXT_PUBLIC_*.
  Strip the /api/proxy prefix from the incoming path.
  Forward the remainder directly to BACKEND_URL.
  Example: incoming /api/proxy/api/v1/videos
           → forwards to http://ai-video-intelligence-api:8000/api/v1/videos
  Forward: method, body, all relevant headers.
  Handle multipart/form-data passthrough for file uploads.
  Preserve response status codes exactly.

Run: cd frontend && make typecheck && make build
```

**Verify:**
- [ ] `make typecheck` zero errors
- [ ] `make build` succeeds
- [ ] Proxy correctly forwards `/api/proxy/api/v1/videos` → `BACKEND_URL/api/v1/videos`

---

### Step 14 — Frontend Dockerfile and smoke test
**Model: `claude-haiku-4-5`**

```
Create frontend/Dockerfile (multi-stage):

FROM node:20-alpine AS deps
WORKDIR /app
COPY package*.json ./
RUN npm ci

FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public
EXPOSE 3000
CMD ["node", "server.js"]

Update docker-compose.yml — add frontend service:

frontend:
  container_name: ai-video-intelligence-frontend
  build:
    context: ./frontend
  ports:
    - "3000:3000"
  environment:
    NEXT_PUBLIC_API_URL: /api/proxy
    BACKEND_URL: http://ai-video-intelligence-api:8000
  depends_on:
    api:
      condition: service_healthy
  healthcheck:
    test: ["CMD", "curl", "-fsS", "http://localhost:3000"]
    interval: 5s
    timeout: 2s
    retries: 5
    start_period: 15s
  restart: unless-stopped
  networks:
    - ai-video-intelligence

Run: make up-frontend
Open http://localhost:3000. Upload a small test MP4.
Report what happens.
```

**Verify:**
- [ ] `make up-frontend` — 4 services healthy
- [ ] Upload MP4 → redirect to `/jobs/{job_id}`
- [ ] Status badge shows `queued`

---

## Phase 3 — Extractor

---

### Step 15 — Extractor scaffold and config
**Model: `claude-haiku-4-5`**

```
Read CLAUDE.md — extractor service section.

STRUCTURE RULE — two levels only:
  services/extractor/            ← service root
  services/extractor/extractor/  ← Python package named "extractor"
Do NOT create services/extractor/extractor/extractor/.

── services/extractor/pyproject.toml
[project]
name = "extractor"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
  "dramatiq[redis]>=1.16", "dramatiq-crontab>=1.0", "asyncpg>=0.29",
  "pydantic-settings>=2.0", "structlog>=24.0", "loguru>=0.7",
  "shared @ { path = '../../libs/shared', develop = true }",
]
dev-dependencies = ["ruff>=0.4", "pytest>=8.0", "pytest-asyncio>=0.23"]
[tool.hatch.build.targets.wheel]
packages = ["extractor"]
[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"

── services/extractor/.gitignore  (same as api)

── services/extractor/Makefile
install (uv sync), lint, lint-fix,
test-unit (uv run pytest tests/unit/ -v),
test (test-unit),
shell (docker compose -f ../../docker-compose.yml exec ai-video-intelligence-extractor /bin/bash),
logs (docker compose -f ../../docker-compose.yml logs -f ai-video-intelligence-extractor),
clean, clean-all, help

── services/extractor/extractor/__init__.py  (empty)
── services/extractor/extractor/core/__init__.py  (empty)
── services/extractor/extractor/core/config.py
Settings: SCENE_THRESHOLD=0.35, FRAME_INTERVAL=150, BATCH_SIZE=5,
DATA_ROOT="/data", FFMPEG_BIN="ffmpeg", FFPROBE_BIN="ffprobe",
MAX_DURATION_SEC=600, DATABASE_URL, REDIS_URL

── services/extractor/extractor/core/logging.py
Same pattern as api: configure_logging(), LoggerMixin, log_call.

── services/extractor/extractor/domain/__init__.py  (empty)
── services/extractor/extractor/domain/video.py
VideoMeta dataclass: duration_seconds, fps, width, height, codec, total_frames
DurationExceededError(ValueError)

── services/extractor/extractor/domain/frame.py
SelectionReason enum: scene_change, periodic, both
FrameMetadata dataclass: video_id, frame_id (str), frame_path,
  timestamp (float), frame_number (int), selection_reason,
  scene_score (float | None), created_at
FrameExtractionError

── services/extractor/tests/__init__.py  (empty)
── services/extractor/tests/unit/__init__.py  (empty)
── services/extractor/tests/unit/test_domain_frame.py
  FrameMetadata creation: all fields populated correctly
  SelectionReason enum: scene_change, periodic, both values exist
  DurationExceededError raised when duration > MAX_DURATION_SEC
  FrameExtractionError raised correctly

Run: cd services/extractor && make install && make test-unit
```

**Verify:**
- [ ] No `services/extractor/extractor/extractor/`
- [ ] `make install` succeeds
- [ ] `make test-unit` all green
- [ ] `uv run python -c "from extractor.core.config import get_settings; print('OK')"`

---

### Step 16 — Extractor repositories
**Model: `claude-haiku-4-5`**

```
Working in services/extractor/. Continue from Step 15.
No business logic in repositories. All inherit LoggerMixin.

── services/extractor/extractor/repositories/__init__.py
BaseRepository(LoggerMixin)

── services/extractor/extractor/repositories/ffprobe_client.py
Same logic as api — ffprobe subprocess → VideoMeta.
FFprobeError on failure.

── services/extractor/extractor/repositories/ffmpeg_runner.py
FFmpegRunner.run(video_path, output_dir, scene_threshold, frame_interval) -> (int, str)
Command:
  ffmpeg -i {video_path}
    -vf "select='gt(scene,{scene_threshold})+not(mod(n,{frame_interval}))'"
    -vsync vfr -q:v 4 {output_dir}/frame_%04d.jpg
asyncio.create_subprocess_exec.
Returns (exit_code, stderr_text).

── services/extractor/extractor/repositories/frame_repo.py
FrameRepository(BaseRepository)
bulk_insert_frames(frames: list[FrameMetadata]) -> list[str]
asyncpg executemany(). Returns inserted IDs.

── services/extractor/extractor/repositories/job_repo.py
update_status(job_id, status, stage, error_message=None)
update_progress(job_id, progress_pct)
```

**Verify:**
- [ ] All files import without error
- [ ] `FFmpegRunner` command matches CLAUDE.md exactly

---

### Step 17 — Extractor services, pipeline, queue
**Model: `claude-sonnet-4-6`**

```
Read CLAUDE.md — processing pipeline, queue names.
Working in services/extractor/. Continue from Step 16.

── services/extractor/extractor/services/__init__.py  BaseService(LoggerMixin)
── services/extractor/extractor/services/probe.py
  ProbeService.run(video_path) -> VideoMeta
  Raises DurationExceededError if > MAX_DURATION_SEC.

── services/extractor/extractor/services/extraction.py
  ExtractionService.run(video_path, output_dir, video_meta) -> list[tuple[int, str]]
  Creates {DATA_ROOT}/frames/{job_id}/ if not exists.
  Calls FFmpegRunner.run(). Scans for frame_*.jpg. Returns sorted tuples.

── services/extractor/extractor/services/metadata.py
  MetadataService.resolve(raw_frames, video_meta, video_id) -> list[FrameMetadata]
  timestamp = frame_number / fps
  selection_reason: periodic if frame_number % FRAME_INTERVAL == 0,
    scene_change otherwise, both if both true
  scene_score: None (MVP). frame_id: new UUID str.

── services/extractor/extractor/services/batcher.py
  BatcherService.partition(frames) -> list[list[FrameMetadata]]
  BATCH_SIZE chunks. Last chunk always included.

── services/extractor/extractor/pipeline/__init__.py  (empty)
── services/extractor/extractor/pipeline/orchestrator.py
  ExtractionOrchestrator.run(job_id: str) -> None
  a. update_status(running, stage=frame_extraction)
  b. probe.run(video_path) → VideoMeta
  c. extraction.run() → raw_frames
  d. metadata.resolve() → frames
  e. frame_repo.bulk_insert_frames() → frame_ids
  f. batcher.partition() → batches
  g. for each batch: enqueue_analysis_batch(job_id, batch_frame_ids)
  h. update_status(stage=ai_analysis)
  Partial failure: FFmpeg non-zero but frames exist → continue, log warning.

── services/extractor/extractor/queue/__init__.py  (empty)

── services/extractor/extractor/queue/consumer.py
CRITICAL: Configure Dramatiq broker with REDIS_URL before declaring any actor.
Do NOT rely on default localhost:6379.

from dramatiq.brokers.redis import RedisBroker
from extractor.core.config import get_settings
from shared.messages import ExtractionMessage
from shared.middleware import ActorMetricsMiddleware
import dramatiq

broker = RedisBroker(url=get_settings().REDIS_URL)
dramatiq.set_broker(broker)
broker.add_middleware(ActorMetricsMiddleware())

@dramatiq.actor(queue_name="extraction", max_retries=3)
def extraction_task(job_id: str) -> None:
  ExtractionOrchestrator(...).run(job_id)
  On exception: job_repo.update_status(failed, error_message=str(e))

── services/extractor/extractor/queue/publisher.py
CRITICAL: Broker already configured in consumer.py when this module is imported
via main.py. But if imported standalone, configure it here too.

from dramatiq.brokers.redis import RedisBroker
from extractor.core.config import get_settings
from shared.messages import AnalysisBatchMessage
import dramatiq

def _ensure_broker() -> None:
  try:
    dramatiq.get_broker()
  except Exception:
    dramatiq.set_broker(RedisBroker(url=get_settings().REDIS_URL))

_ensure_broker()

@dramatiq.actor(queue_name="analysis")
def analysis_batch_task(job_id: str, frame_ids: list[str]) -> None:  # pragma: no cover
  raise NotImplementedError("Stub — consumed by worker service.")

def enqueue_analysis_batch(job_id: str, frame_ids: list[str]) -> None:
  msg = AnalysisBatchMessage(job_id=job_id, frame_ids=frame_ids)
  analysis_batch_task.send(msg.job_id, msg.frame_ids)

── services/extractor/extractor/main.py
from extractor.queue.consumer import extraction_task  # triggers actor + broker setup
from extractor.core.logging import configure_logging
configure_logging()
Init DB pool (asyncpg) at module scope.
```

**Verify:**
- [ ] All files import without error
- [ ] Pipeline step order matches CLAUDE.md
- [ ] Broker configured from REDIS_URL — no localhost references

---

### Step 18 — Extractor Dockerfile and docker-compose
**Model: `claude-haiku-4-5`**

```
Create services/extractor/Dockerfile.
Build context is repo root. All paths relative to repo root.

FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app/services/extractor

WORKDIR /app

RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

RUN pip install uv

COPY libs/shared ./libs/shared/

COPY services/extractor/pyproject.toml ./services/extractor/
WORKDIR /app/services/extractor
RUN uv sync --no-dev

COPY services/extractor/extractor ./extractor/

CMD ["uv", "run", "dramatiq", "extractor.main", "--processes", "1", "--threads", "4"]

Update docker-compose.yml — add ffmpeg-extractor service:

ffmpeg-extractor:
  container_name: ai-video-intelligence-extractor
  build:
    context: .
    dockerfile: services/extractor/Dockerfile
  env_file:
    - .env.docker.db
    - .env.docker.extractor
  volumes:
    - ai-video-intelligence-app-data:/data
  depends_on:
    postgres:
      condition: service_healthy
    redis:
      condition: service_healthy
  restart: unless-stopped
  networks:
    - ai-video-intelligence

Run: make up-extractor
Upload a test video via the frontend.
Report: extractor logs, file count in /data/frames/{job_id}/, job stage.
```

**Verify:**
- [ ] Extractor picks up the `extraction_task` from Redis
- [ ] Frames appear in `/data/frames/{job_id}/`
- [ ] `frames` table has rows with correct timestamps
- [ ] Job `stage` = `ai_analysis`

---

## Phase 4 — Worker

---

### Step 19 — Worker scaffold and config
**Model: `claude-haiku-4-5`**

```
Read CLAUDE.md — worker service section, environment variables.

STRUCTURE RULE — two levels only:
  services/worker/          ← service root
  services/worker/worker/   ← Python package named "worker"
Do NOT create services/worker/worker/worker/.

── services/worker/pyproject.toml
[project]
name = "worker"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
  "dramatiq[redis]>=1.16", "dramatiq-crontab>=1.0", "asyncpg>=0.29",
  "openai>=1.30", "pydantic-settings>=2.0",
  "structlog>=24.0", "loguru>=0.7",
  "shared @ { path = '../../libs/shared', develop = true }",
]
dev-dependencies = ["ruff>=0.4", "pytest>=8.0", "pytest-asyncio>=0.23"]
[tool.hatch.build.targets.wheel]
packages = ["worker"]
[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"

── services/worker/.gitignore  (same as api)

── services/worker/Makefile
install (uv sync), lint, lint-fix,
test-unit (uv run pytest tests/unit/ -v),
test (test-unit),
shell-1 through shell-4 (docker compose exec worker-N),
logs (docker compose logs -f worker-1 worker-2 worker-3 worker-4 scheduler),
trigger-cleanup (docker compose exec ai-video-intelligence-worker-1
  uv run python -c "from worker.queue.consumer import cleanup_task; cleanup_task.send()"),
clean, clean-all, help

── services/worker/worker/__init__.py  (empty)
── services/worker/worker/core/__init__.py  (empty)
── services/worker/worker/core/config.py
AI_MODEL="gpt-4o", AI_BASE_URL="", AGGREGATION_MODEL="gpt-4o",
OPENAI_API_KEY, MAX_RETRIES=3, MIN_BACKOFF_SEC=15, MAX_BACKOFF_SEC=120,
JOB_TTL_DAYS=7, FAILED_JOB_TTL_DAYS=1, CLEANUP_CRON="0 2 * * *",
DATA_ROOT="/data", DATABASE_URL, REDIS_URL, BATCH_SIZE=5

AI_BASE_URL: empty string = OpenAI default.
  Set to Gemini or Ollama URL to switch provider — no code changes needed.
  See CLAUDE.md AI provider configuration section for all options.

── services/worker/worker/core/logging.py  (same pattern as api)

── services/worker/worker/domain/__init__.py  (empty)
── services/worker/worker/domain/analysis.py
FrameAnalysisResult dataclass: frame_id, description, model_used,
  raw_response (dict), created_at
EmptyDescriptionError
validate_analysis(result) -> None  raises if description empty/whitespace

── services/worker/worker/domain/summary.py
TimelineEvent dataclass: timestamp (float), event (str)
AggregationResult dataclass: summary (str), timeline (list[TimelineEvent])
MalformedAggregationError with raw_text: str field
validate_aggregation_json(raw: str) -> AggregationResult
  strip markdown fences → json.loads() → validate schema
  raise MalformedAggregationError on any failure

── services/worker/worker/domain/cleanup.py
CleanupTarget dataclass: job_id, upload_path, frames_dir

── services/worker/tests/__init__.py  (empty)
── services/worker/tests/unit/__init__.py  (empty)
── services/worker/tests/unit/test_domain_analysis.py
  FrameAnalysisResult creation
  validate_analysis raises EmptyDescriptionError on empty/whitespace
── services/worker/tests/unit/test_domain_summary.py
  validate_aggregation_json happy path
  validate_aggregation_json strips markdown fences
  MalformedAggregationError on missing fields, invalid JSON

Run: cd services/worker && make install && make test-unit
```

**Verify:**
- [ ] No `services/worker/worker/worker/`
- [ ] `make install` succeeds
- [ ] `make test-unit` all green
- [ ] `uv run python -c "from worker.core.config import get_settings; print('OK')"`

---

### Step 20 — Worker repositories
**Model: `claude-sonnet-4-6`**

```
Working in services/worker/. Continue from Step 19.
No business logic. All inherit LoggerMixin.

── services/worker/worker/repositories/__init__.py  BaseRepository(LoggerMixin)

── services/worker/worker/repositories/ai_client.py
AIProvider Protocol: analyze_frames() -> list[str], complete() -> str

AIClient(AIProvider): AsyncOpenAI client configured from settings.
Supports three providers via OpenAI-compatible API — no code changes needed:

  OpenAI:         AI_BASE_URL="" (default), OPENAI_API_KEY=sk-...
  Gemini Flash:   AI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
  Ollama local:   AI_BASE_URL=http://ai-video-intelligence-ollama:11434/v1

Client init:
  self.client = AsyncOpenAI(
      api_key=settings.OPENAI_API_KEY,
      base_url=settings.AI_BASE_URL or None,  # None = OpenAI default
  )
  # Detect Ollama by port — routes to sequential calling strategy
  self.is_ollama = "11434" in (settings.AI_BASE_URL or "")

Calling strategy — MUST implement both:
  _analyze_frames_batch(frames) → ONE API call with ALL frames as image_url blocks
    Used for: OpenAI, Gemini Flash
    Reason: large context window, fast, cost-efficient

  _analyze_frames_sequential(frames) → ONE API call PER FRAME
    Used for: Ollama (qwen2.5vl:3b)
    Reason: limited context on 8GB, OOM risk with batch

  analyze_frames(frames) → routes based on self.is_ollama:
    if self.is_ollama: return await self._analyze_frames_sequential(frames)
    else:              return await self._analyze_frames_batch(frames)

Frames always sent as base64 data URLs regardless of strategy:
  {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{data}"}}

Exponential back-off retry: MAX_RETRIES, MIN_BACKOFF_SEC, MAX_BACKOFF_SEC.

── services/worker/worker/repositories/frame_repo.py
get_frames_by_ids(frame_ids) -> list[dict]  returns frame_id, frame_path
get_all_descriptions_for_job(job_id) -> list[dict]
  JOIN frames + frame_analysis ORDER BY timestamp ASC
  returns [{timestamp, description}]

── services/worker/worker/repositories/analysis_repo.py
bulk_insert_analysis(results: list[FrameAnalysisResult]) -> None
  asyncpg executemany() into frame_analysis
nullify_raw_responses(job_id) -> None
  UPDATE frame_analysis SET ai_response = NULL
  WHERE frame_id IN (SELECT id FROM frames WHERE video_id = job_id)

── services/worker/worker/repositories/summary_repo.py
upsert_summary(video_id, result, is_partial, model_used) -> None
  INSERT ... ON CONFLICT (video_id) DO UPDATE. generated_at = NOW().

── services/worker/worker/repositories/storage_repo.py
delete_upload(job_id): Path(DATA_ROOT/uploads/{job_id}.mp4).unlink(missing_ok=True)
delete_frames(job_id): shutil.rmtree(DATA_ROOT/frames/{job_id}, ignore_errors=True)

── services/worker/worker/repositories/job_repo.py
update_status(), update_progress()
get_pending_batch_count(job_id) -> int
  COUNT(frames) - COUNT(frame_analysis rows for those frames)
get_expired_jobs() -> list[dict]
  WHERE expires_at < NOW() AND cleaned_at IS NULL
  AND status IN ('completed','failed')
is_analysis_complete(job_id) -> bool
mark_cleaned(job_id) -> None
```

**Verify:**
- [ ] All files import without error
- [ ] No business logic — only DB/file operations

---

### Step 21 — Worker services
**Model: `claude-sonnet-4-6`**

```
Read CLAUDE.md — processing pipeline, exactly-once aggregation.
Working in services/worker/. Continue from Step 20.

── services/worker/worker/services/__init__.py  BaseService(LoggerMixin)

── services/worker/worker/services/vision.py
VisionService.analyze(frame_ids, job_id) -> list[FrameAnalysisResult]
Read JPEG bytes → base64.b64encode() in memory only — never stored.
Single OpenAI call with all frames as image_url content blocks.
Parse response into FrameAnalysisResult per frame.
validate_analysis() each result. Discard base64 after response.

── services/worker/worker/services/aggregator.py
AggregatorService.aggregate(job_id) -> AggregationResult
get_all_descriptions_for_job() → format "[T=25.2s] description" per frame.
AIClient.complete() → validate_aggregation_json()

── services/worker/worker/services/completion.py
CompletionChecker.check(job_id) -> None
Uses synchronous Redis client (dramatiq uses sync Redis — not asyncio).
get_pending_batch_count(). If 0:
  redis_client.set(f"agg_lock:{job_id}", 1, nx=True, ex=60)
  If acquired (returns True): send aggregation_task message.
  If not acquired (returns None): another worker triggered — skip.

── services/worker/worker/services/cleanup.py
CleanupService.clean(job) -> None
Order: delete_upload → delete_frames → nullify_raw_responses → mark_cleaned
Log each step with job_id.
```

**Verify:**
- [ ] base64 encoding is only in-memory in `vision.py`
- [ ] `completion.py` uses sync Redis `set(..., nx=True, ex=60)` not async

---

### Step 22 — Worker pipelines, queue, scheduler, main
**Model: `claude-sonnet-4-6`**

```
Read CLAUDE.md — retry policy, cleanup retention.
Working in services/worker/. Continue from Step 21.

── services/worker/worker/pipeline/__init__.py  (empty)

── services/worker/worker/pipeline/batch_orchestrator.py
BatchOrchestrator.run(job_id, frame_ids) -> None
a. update stage=ai_analysis only on first batch (check current stage first)
b. VisionService.analyze() → results
c. validate_analysis() each result
d. analysis_repo.bulk_insert_analysis()
e. progress_pct = analysed_frames / total_frames * 100
f. job_repo.update_progress()
g. CompletionChecker.check()
On exception: update_status(failed, error_message=str(e))

── services/worker/worker/pipeline/agg_orchestrator.py
AggOrchestrator.run(job_id) -> None
a. update_status(stage=aggregation)
b. AggregatorService.aggregate() → AggregationResult
c. summary_repo.upsert_summary()
d. mark_completed()  — sets completed_at + expires_at=NOW()+JOB_TTL_DAYS
On exception: mark_failed(stage=aggregation) expires_at=NOW()+FAILED_JOB_TTL_DAYS

── services/worker/worker/pipeline/cleanup_orchestrator.py
CleanupOrchestrator.run() -> None
get_expired_jobs() → for each:
  skip if not is_analysis_complete()
  CleanupService.clean()
Log total count of cleaned jobs.

── services/worker/worker/queue/__init__.py  (empty)

── services/worker/worker/queue/consumer.py
CRITICAL: Configure Dramatiq broker with REDIS_URL before declaring any actor.
Do NOT rely on default localhost:6379.

from dramatiq.brokers.redis import RedisBroker
from worker.core.config import get_settings
from shared.messages import AnalysisBatchMessage, AggregationMessage
from shared.middleware import ActorMetricsMiddleware
import dramatiq

broker = RedisBroker(url=get_settings().REDIS_URL)
dramatiq.set_broker(broker)
broker.add_middleware(ActorMetricsMiddleware())

from worker.pipeline.batch_orchestrator import BatchOrchestrator
from worker.pipeline.agg_orchestrator import AggOrchestrator
from worker.pipeline.cleanup_orchestrator import CleanupOrchestrator

@dramatiq.actor(queue_name="analysis", max_retries=3)
def analysis_batch_task(job_id: str, frame_ids: list[str]) -> None:
  BatchOrchestrator(...).run(job_id, frame_ids)

@dramatiq.actor(queue_name="aggregation", max_retries=1)
def aggregation_task(job_id: str) -> None:
  AggOrchestrator(...).run(job_id)

@dramatiq.actor(queue_name="cleanup", max_retries=3)
def cleanup_task() -> None:
  CleanupOrchestrator(...).run()

── services/worker/worker/scheduler.py
IMPORTANT: Do not call get_settings() at module level — it may fail if
env is not yet loaded. Use a lambda or import inside the decorator.

from dramatiq_crontab import crontab
from worker.queue.consumer import cleanup_task

@crontab("0 2 * * *")  # or read from env inside a factory function
def schedule_cleanup():
    cleanup_task.send()

── services/worker/worker/main.py
from worker.queue.consumer import analysis_batch_task  # triggers broker + actor setup
from worker.core.logging import configure_logging
configure_logging()
Init DB pool (asyncpg) at module scope.
```

**Verify:**
- [ ] All imports resolve correctly
- [ ] Broker configured from REDIS_URL — no localhost references
- [ ] `scheduler.py` does NOT call `get_settings()` at module level

---

### Step 23 — Worker Dockerfile and end-to-end test
**Model: `claude-haiku-4-5`**

```
Create services/worker/Dockerfile.
Build context is repo root. All paths relative to repo root.

FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app/services/worker

WORKDIR /app

RUN pip install uv

COPY libs/shared ./libs/shared/

COPY services/worker/pyproject.toml ./services/worker/
WORKDIR /app/services/worker
RUN uv sync --no-dev

COPY services/worker/worker ./worker/
COPY services/worker/scheduler.py ./scheduler.py

CMD ["uv", "run", "dramatiq", "worker.main", "--processes", "1", "--threads", "3"]

Update docker-compose.yml — add workers and scheduler:

worker-1: &worker
  container_name: ai-video-intelligence-worker-1
  build:
    context: .
    dockerfile: services/worker/Dockerfile
  env_file:
    - .env.docker.db
    - .env.docker.worker
  volumes:
    - ai-video-intelligence-app-data:/data
  depends_on:
    postgres:
      condition: service_healthy
    redis:
      condition: service_healthy
  restart: unless-stopped
  networks:
    - ai-video-intelligence

worker-2:
  <<: *worker
  container_name: ai-video-intelligence-worker-2

worker-3:
  <<: *worker
  container_name: ai-video-intelligence-worker-3

worker-4:
  <<: *worker
  container_name: ai-video-intelligence-worker-4

scheduler:
  container_name: ai-video-intelligence-scheduler
  build:
    context: .
    dockerfile: services/worker/Dockerfile
  env_file:
    - .env.docker.db
    - .env.docker.worker
  depends_on:
    redis:
      condition: service_healthy
  command: ["uv", "run", "python", "-m", "dramatiq_crontab", "worker.scheduler"]
  restart: unless-stopped
  networks:
    - ai-video-intelligence

To switch AI provider before running — edit .env.docker.worker:

  Local dev (Ollama):
    ollama pull qwen2.5vl && ollama serve
    AI_MODEL=qwen2.5vl
    AI_BASE_URL=http://host.docker.internal:11434/v1
    OPENAI_API_KEY=ollama

  Gemini Flash 2.0:
    AI_MODEL=gemini-2.0-flash
    AI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
    OPENAI_API_KEY=your_google_ai_studio_key

  OpenAI (default):
    AI_MODEL=gpt-4o
    AI_BASE_URL=
    OPENAI_API_KEY=sk-...

For 30-60sec videos also set in .env.docker.extractor:
  FRAME_INTERVAL=60
  SCENE_THRESHOLD=0.3
  BATCH_SIZE=15

Add optional Ollama service to docker-compose.yml:

ollama:
  container_name: ai-video-intelligence-ollama
  image: ollama/ollama
  ports:
    - "11434:11434"
  environment:
    OLLAMA_MODEL: qwen2.5vl:3b
  entrypoint: ["/bin/sh", "/scripts/ollama-entrypoint.sh"]
  volumes:
    - ai-video-intelligence-ollama-data:/root/.ollama
    - ./scripts:/scripts:ro
  healthcheck:
    test: ["CMD", "curl", "-fsS", "http://localhost:11434/api/tags"]
    interval: 10s
    timeout: 5s
    retries: 10
    start_period: 300s   # 5 min — enough for model download on first run
  restart: unless-stopped
  networks:
    - ai-video-intelligence

Also add ai-video-intelligence-ollama-data to the volumes: block at top
of docker-compose.yml (already in skeleton from Step 1).

Update worker-1 depends_on to include ollama when using local AI:
NOTE: Only add ollama dependency when AI_BASE_URL points to ollama.
      Leave workers independent for cloud provider deployments.

To use Ollama — update .env.docker.worker:
  AI_MODEL=qwen2.5vl:3b
  AI_BASE_URL=http://ai-video-intelligence-ollama:11434/v1
  OPENAI_API_KEY=ollama
  AGGREGATION_MODEL=qwen2.5vl:3b

To use OpenAI/Gemini — update .env.docker.worker:
  AI_MODEL=gpt-4o                   # or gemini-2.0-flash
  AI_BASE_URL=                      # empty for OpenAI
  OPENAI_API_KEY=sk-...
  AGGREGATION_MODEL=gpt-4o

Run full stack (cloud provider):
  make up

Run with Ollama (8GB RAM — 1 worker only):
  make up-ollama
  NOTE: first run downloads qwen2.5vl:3b (~2GB) — allow 2-5 min
  Check model ready: make ollama-list

End-to-end test:
1. Upload an MP4 via http://localhost:3000
2. Watch logs: make logs
3. Wait for status=completed in the UI
4. Confirm summary and timeline are non-empty

Cleanup test:
5. make api-shell-db
   UPDATE videos SET expires_at = NOW() - interval '1 second' WHERE id = '<job_id>';
   \q
6. make worker-trigger-cleanup
7. Confirm /data/uploads/ file deleted
8. Confirm /data/frames/{job_id}/ directory deleted
9. Confirm frame_analysis.ai_response = NULL, description intact
10. Confirm videos.cleaned_at is populated

Report result for each numbered step.
```

**Verify:**
- [ ] `make up` — all 10 services healthy
- [ ] Full pipeline: upload → `completed` with summary + timeline
- [ ] Cleanup test: all 6 steps pass

---

## Phase 5 — Quality

---

### Step 24 — Integration tests
**Model: `claude-sonnet-4-6`**

```
Read CLAUDE.md — test structure section.
Integration tests live inside services/api/tests/integration/.
Unit tests already done in Step 9.

── services/api/tests/integration/__init__.py  (empty)

── services/api/tests/integration/conftest.py
pytest-asyncio fixtures:
test_db:
  Create test DB, run alembic upgrade head (from services/api/ dir),
  yield AsyncSession, drop DB after suite.
test_redis: yield Redis client (sync, for Dramatiq compat)
test_client: yield httpx.AsyncClient pointing at FastAPI app
mock_ai_client:
  Fixture that monkeypatches AIClient.
  Returns deterministic FrameAnalysisResult responses — no real OpenAI calls.

── services/api/tests/fixtures/
Generate 5-second 720p test video:
  ffmpeg -f lavfi -i testsrc=duration=5:size=1280x720:rate=30 \
    services/api/tests/fixtures/sample.mp4

── services/api/tests/integration/test_upload_pipeline.py
POST /api/v1/videos with sample.mp4
Assert: 202, job_id in response body
Assert: job row in DB with status=queued, stage=upload_validation
Assert: extraction task message in Redis extraction queue

── services/api/tests/integration/test_extraction_pipeline.py
Call extraction_task(job_id) directly with sample.mp4 and real FFmpeg.
Assert: frame JPEG files written to /data/frames/{job_id}/
Assert: frame rows in DB with correct timestamps
Assert: analysis_batch_task messages in Redis analysis queue

── services/api/tests/integration/test_analysis_pipeline.py
Call analysis_batch_task(job_id, frame_ids) with mock_ai_client.
Assert: frame_analysis rows inserted with description populated
Assert: progress_pct updated on job row

── services/api/tests/integration/test_aggregation_pipeline.py
Call aggregation_task(job_id) with mock_ai_client returning fixed JSON:
  {"summary": "Test summary", "timeline": [{"timestamp": 1.0, "event": "Test event"}]}
Assert: video_summary row created with summary + timeline
Assert: job status=completed, completed_at populated

── services/api/tests/integration/test_cleanup_pipeline.py
Setup: completed job with expires_at = NOW() - 1 second
Call cleanup_task() directly.
Assert: upload file deleted from /data/uploads/
Assert: frames directory deleted from /data/frames/
Assert: frame_analysis.ai_response = NULL
Assert: frame_analysis.description still present
Assert: videos.cleaned_at populated

Run: cd services/api && make test
Report pass/fail counts.
```

**Verify:**
- [ ] `services/api/tests/integration/` has 5 test files + conftest.py
- [ ] `cd services/api && make test` all green
- [ ] No real OpenAI API calls in any test

---

### Step 25 — Observability and pipeline logging
**Model: `claude-sonnet-4-6`**

```
Task 1 — Confirm devtrack dashboard:
  make up-api
  curl http://localhost:8000/__devtrack__/dashboard
  Should return HTML. If 404 — check devtrack_router is included in main.py
  without any prefix.

Task 2 — Add structured log lines to all three pipeline orchestrators:

services/extractor/extractor/pipeline/orchestrator.py
services/worker/worker/pipeline/batch_orchestrator.py
services/worker/worker/pipeline/agg_orchestrator.py
services/worker/worker/pipeline/cleanup_orchestrator.py

Each orchestrator must log:
  Entry:   logger.info("pipeline_start", job_id=job_id, stage="<name>")
  Exit:    logger.info("pipeline_done", job_id=job_id, stage="<name>", duration_ms=<ms>)
  Failure: logger.error("pipeline_failed", job_id=job_id, stage="<name>",
             error=str(e))

Task 3 — Final local verification. Run each and report result:
  make lint        → must be zero errors
  make test        → must be all green
  make up          → all 10 services healthy
  Upload MP4 end-to-end → status=completed with summary + timeline
  http://localhost:8000/__devtrack__/dashboard → metrics visible
```

**Verify:**
- [ ] `make lint` zero errors
- [ ] `make test` all green
- [ ] All 10 services healthy
- [ ] DevTrack dashboard accessible and shows request metrics

---

### Step 26 — Alembic migration check
**Model: `claude-haiku-4-5`**

```
Open services/api/alembic/versions/0001_initial.py.

Confirm all of these columns exist on the videos table:
  expires_at TIMESTAMPTZ
  cleaned_at TIMESTAMPTZ

If either is missing:
  Generate services/api/alembic/versions/0002_add_cleanup_columns.py
  Rebuild and restart: make up-api
  Confirm migration runs in container logs.

Verify clean migration on fresh DB:
  make down-all          ← removes volumes
  make up-api            ← fresh postgres + runs migrations automatically
  docker compose logs api | grep -E "migration|alembic"
Report the output.
```

**Verify:**
- [ ] `expires_at` and `cleaned_at` present in migration
- [ ] Fresh `make up-api` runs migrations automatically with zero errors

---

### Step 27 — GitHub Actions
**Model: `claude-haiku-4-5`**

```
Create two GitHub Actions workflow files.

── .github/workflows/ci.yml
Trigger: pull_request → main

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: cd libs/shared && uv sync
      - run: cd services/api && uv sync
      - run: cd services/extractor && uv sync
      - run: cd services/worker && uv sync
      - run: make lint

  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_DB: test
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 5s
          --health-retries 5
        ports: ["5432:5432"]
      redis:
        image: redis:7-alpine
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 5s
          --health-retries 5
        ports: ["6379:6379"]
    env:
      DATABASE_URL: postgresql+asyncpg://postgres:test@localhost/test
      REDIS_URL: redis://localhost:6379
      DATA_ROOT: /tmp/test-data
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: cd libs/shared && uv sync
      - run: cd services/api && uv sync
      - run: cd services/extractor && uv sync
      - run: cd services/worker && uv sync
      - run: cd services/api && uv run alembic upgrade head
      - run: make test

── .github/workflows/build.yml
Trigger: push → main

jobs:
  build:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        include:
          - service: api
            dockerfile: services/api/Dockerfile
            context: .
          - service: extractor
            dockerfile: services/extractor/Dockerfile
            context: .
          - service: worker
            dockerfile: services/worker/Dockerfile
            context: .
          - service: frontend
            dockerfile: frontend/Dockerfile
            context: frontend
    steps:
      - uses: actions/checkout@v4
      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: pkaranje
          password: ${{ secrets.GHCR_TOKEN }}
      - uses: docker/build-push-action@v5
        with:
          context: ${{ matrix.context }}
          dockerfile: ${{ matrix.dockerfile }}
          push: true
          tags: ghcr.io/pkaranje/ai-video-intelligence/${{ matrix.service }}:${{ github.sha }}
```

**Verify:**
- [ ] Both YAML files are valid
- [ ] Open a test PR → CI workflow triggers and passes

---

### Step 28 — Final checklist
**Model: `claude-haiku-4-5`**

```
Final verification before merging to main.
Check each item and report pass or fail:

1. .gitignore: .env.docker.* files are ignored, .env.docker.*.example files are NOT
2. .dockerignore exists at repo root and excludes .venv, __pycache__, tests/, .env files
3. uv.lock committed: libs/shared/, services/api/, services/extractor/, services/worker/
4. Makefiles: root, libs/shared/, services/api/, services/extractor/, services/worker/, frontend/
5. Dockerfiles: services/api/, services/extractor/, services/worker/, frontend/
6. docker-compose.yml has exactly 10 services with correct container names:
   ai-video-intelligence-postgres, ai-video-intelligence-redis,
   ai-video-intelligence-api, ai-video-intelligence-frontend,
   ai-video-intelligence-extractor,
   ai-video-intelligence-worker-1..4, ai-video-intelligence-scheduler
7. All volumes and network have explicit name: fields (no project prefix)
8. All services have restart: unless-stopped
9. api service has command: block running alembic upgrade head before uvicorn
10. make lint → zero errors
11. make test → all green
12. make up → all 10 services healthy, all healthchecks passing
13. Full upload → pipeline → summary + timeline visible in UI
14. http://localhost:8000/__devtrack__/dashboard shows request metrics
15. scripts/ollama-entrypoint.sh exists and is executable (chmod +x)
16. make up-ollama → starts 1 worker + ollama, qwen2.5vl:3b pulls automatically
17. make ollama-list → shows qwen2.5vl:3b in model list

Fix any failures before opening PR to main.
```

**Verify:**
- [ ] All 14 checklist items pass
- [ ] PR CI green before merge

---

## Build schedule

| Day | Steps | Goal |
|---|---|---|
| Day 1 | 1–3 | Root scaffold + libs/shared working |
| Day 2 | 4–9 | Full API backend — smoke test passing |
| Day 3 | 10–14 | Frontend upload → queued working |
| Day 4 | 15–18 | Extractor: upload → frames in DB |
| Day 5 (Friday) | 19–23 | Worker: full pipeline end-to-end |
| Day 5 (stretch) | 24–28 | Tests + CI + final checklist |
