# CLAUDE.md — AI Video Summarization Platform

## Project overview

Production-grade MVP/POC: users upload MP4 videos via a web UI; the system extracts
representative frames, runs them through an OpenAI-compatible Vision API in parallel,
and returns an AI-generated prose summary plus a timestamped event timeline.

Single-server Docker Compose deployment (4 vCPU, 8 GB RAM).
Five services: Next.js frontend, FastAPI backend, FFmpeg extractor, Worker pool, Scheduler.

---

## Repository layout

```
/
├── frontend/          # Next.js 15 App Router
├── app/               # FastAPI backend
├── extractor/         # FFmpeg extractor (Dramatiq worker, no HTTP)
├── worker/            # AI analysis + aggregation + cleanup (Dramatiq worker, no HTTP)
├── .github/
│   └── workflows/
│       ├── ci.yml     # Lint + test on every PR
│       └── build.yml  # Docker image build on merge to main
├── docker-compose.yml
├── .env.example
├── PROMPT.md
└── CLAUDE.md
```

---

## Root scaffold files

These live at repo root and must exist before any service is built.

```
/
├── .gitignore             # Python, Node, uv, .env, data/, IDE
├── .env.example           # all env vars with placeholder values + comments
├── .env.docker.example    # Docker Compose overrides (service hostnames)
├── Makefile               # single interface for all dev + ops tasks
├── docker-compose.yml     # all 10 services, shared volumes, network
├── pyproject.toml         # tooling config only: ruff + pytest rules
│                          # NOT a uv workspace — services are independent
└── shared/                # internal package: code shared by extractor + worker only
    ├── pyproject.toml
    ├── shared/__init__.py
    └── shared/middleware.py  # ActorMetricsMiddleware
```

### .env.example sections

```
# Database, Redis, AI (OPENAI_API_KEY, AI_MODEL, AI_BASE_URL, AGGREGATION_MODEL)
# Extraction (SCENE_THRESHOLD, FRAME_INTERVAL, BATCH_SIZE, MAX_FILE_SIZE_MB,
#             MAX_DURATION_SEC, DATA_ROOT)
# Workers (WORKER_COUNT, WORKER_CONCURRENCY, MAX_RETRIES,
#          MIN_BACKOFF_SEC, MAX_BACKOFF_SEC)
# Cleanup (JOB_TTL_DAYS, FAILED_JOB_TTL_DAYS, CLEANUP_CRON)
# Frontend (NEXT_PUBLIC_API_URL, BACKEND_URL)
# Observability — devtrack dashboard URL comment
```

### .env.docker.example

Docker-specific overrides. Replaces `localhost` with Docker service names:
```
DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/videosumm
REDIS_URL=redis://redis:6379
DATA_ROOT=/data
BACKEND_URL=http://api:8000
```

### Per-service .gitignore

Each Python service (`app/`, `extractor/`, `worker/`) has its own `.gitignore`:
```
__pycache__/  *.py[cod]  .venv/  .pytest_cache/  .ruff_cache/
```

Frontend has its own `.gitignore`:
```
.next/  out/  node_modules/  .env.local  *.env.local
```

### Makefile structure

Each service owns its own `Makefile` with service-specific commands.
The root `Makefile` delegates to them — it never duplicates logic.

```
Makefile              ← root: delegates via $(MAKE) -C <service> <target>
app/Makefile          ← install, lint, test, db-migrate, shell, shell-db
extractor/Makefile    ← install, lint, shell, logs
worker/Makefile       ← install, lint, shell-1..4, logs, trigger-cleanup
frontend/Makefile     ← install, dev, build, typecheck, lint, shell
```

**Delegation pattern** — every `app-<target>` call at root maps to
`$(MAKE) -C app <target>`. This means:

```bash
make app-shell        # → cd app && make shell
make worker-logs      # → cd worker && make logs
make frontend-dev     # → cd frontend && make dev
make extractor-lint   # → cd extractor && make lint
```

Teammates working on a single service can `cd` into it and use
`make help` + `make <target>` directly without touching root.

**New contributor onboarding — three commands:**
```bash
make env-check   # creates .env.docker from .env.docker.example
make install     # installs deps for all services
make up-app      # starts api + postgres + redis
```

| Root aggregate target | What it does |
|---|---|
| `make lint` | Calls `app lint` + `extractor lint` + `worker lint` |
| `make test` | Delegates to `app test` |
| `make build` | `docker compose build` |
| `make up` / `make up-dev` | Full stack detached / with logs |
| `make up-app/frontend/extractor/workers` | Subset stacks per phase |
| `make db-migrate/rollback/reset` | Delegates to `app db-*` |
| `make clean` / `make clean-all` | Loops `clean` across all services |

### shared/ — internal package

Contains code shared exclusively between `extractor/` and `worker/`.
`app/` and `frontend/` never import from it.

```
shared/
├── pyproject.toml        # name="shared", deps: loguru, dramatiq
├── shared/__init__.py
├── shared/middleware.py  # ActorMetricsMiddleware
└── shared/messages.py    # typed message contracts for all queues
```

**pyproject.toml**:
```toml
[project]
name = "shared"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = ["loguru>=0.7", "dramatiq>=1.16"]
```

`app/`, `extractor/`, and `worker/` all declare it as a local path dependency:
```toml
dependencies = [
    ...
    "shared @ ../shared",
]
```

**Import boundary rule:**

| Service | May import from shared/ | What |
|---|---|---|
| `app/queue/` | Yes | `messages.py` only |
| `app/` everywhere else | No | — |
| `extractor/` | Yes | `messages.py` + `middleware.py` |
| `worker/` | Yes | `messages.py` + `middleware.py` |
| `frontend/` | No | — |

**Dockerfile pattern** — both extractor and worker copy `shared/` before installing:
```dockerfile
COPY ../shared /shared
RUN uv pip install /shared
```

`shared/` has its own `make install` and `make lint` targets.
Root `make install` and `make lint` include it.

### Root pyproject.toml — tooling config only

```toml
[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

ruff and pytest walk up the directory tree for config, so this single file
governs all three Python services when run from root.
Each service (`app/`, `extractor/`, `worker/`) has its own `pyproject.toml`
and its own `uv.lock` — they are independent uv projects, not workspace members.
Services share no code and run in separate Docker containers, so shared
dependency resolution adds no value.

---

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 15 (App Router), Tailwind CSS, TypeScript |
| Backend | FastAPI, Python 3.12, pydantic-settings, asyncpg |
| Queue | Redis 7, Dramatiq, dramatiq-crontab |
| Video processing | FFmpeg, FFprobe |
| AI | OpenAI Vision API (provider-abstracted via AIProvider protocol) |
| Database | PostgreSQL 16 |
| Storage | Docker shared volume → MinIO (Phase 2) |
| Observability | devtrack-sdk (FastAPI middleware, DuckDB storage, built-in dashboard) |
| Logging | Loguru + structlog (JSON, job_id bound to every log line) |
| Dev tooling | uv, Ruff, Pytest |
| CI/CD | GitHub Actions |

---

## Architecture rules

### Dependency direction (all Python services)

```
api/routes → services → repositories → DB / Redis / external
```

- Routes never import repositories directly
- Services never import routes or schemas
- Repositories never import services
- `domain/` is pure Python — zero external imports, fully unit-testable
- Queue publishers are called by services only, never by routes
- Pipeline orchestrators wire services together; they contain no business logic

### Layer responsibilities

| Layer | Does | Never does |
|---|---|---|
| `api/routes` | Parse request, call service, return response | Business logic, DB queries |
| `services/` | Orchestrate: validate → persist → enqueue | HTTP concerns, raw SQL |
| `repositories/` | DB CRUD, subprocess calls, external API calls | Business logic |
| `domain/` | Pure validation, typed exceptions, enums, constants | I/O of any kind |
| `queue/publisher` | `send_message()` wrapper only | Actor definition, retry config |
| `pipeline/` | Sequence service calls for a full workflow | Own any logic |

### Frontend Server vs Client split

Default to Server Components. Add `'use client'` only when the component
needs browser APIs, event listeners, or mutable React state.

| Always Server | Always Client |
|---|---|
| Page shells, initial data fetch | Upload form, drag-and-drop |
| Pure display (SummaryCard, TimelineList, ui/*) | Polling loop (JobStatusClient) |
| | Error boundaries (required by Next.js) |

All client-side API calls route through `app/api/proxy/[...path]/route.ts`.
`BACKEND_URL` is server-side only — never sent to the browser.

---

## Service architectures

### FastAPI backend (`app/`)

Own `pyproject.toml` (uv). Key deps: `fastapi`, `uvicorn`, `pydantic-settings`,
`sqlalchemy[asyncio]`, `asyncpg`, `alembic`, `redis`, `dramatiq[redis]`,
`structlog`, `loguru`, `python-multipart`, `devtrack-sdk`, `shared @ ../shared`.

`shared/` is imported exclusively in `app/queue/publisher.py` for message contracts.
No other file in `app/` imports from `shared/`.

```
app/
├── pyproject.toml
├── main.py                  # App factory, router mounts, lifespan(), configure_logging(),
│                            #   devtrack-sdk middleware registration
├── core/
│   ├── config.py            # pydantic-settings singleton (lru_cache). All env vars here.
│   ├── dependencies.py      # DI: get_db, get_redis, get_*_service — injected via Depends()
│   ├── middleware.py        # RequestLoggingMiddleware: attaches request_id, structlog ctx
│   └── logging.py           # configure_logging(), LoggerMixin, log_call decorator
├── domain/
│   ├── video.py             # VideoStatus enum, validate_upload(), UploadTooLargeError,
│   │                        #   UnsupportedFormatError, MAX_FILE_SIZE, MAX_DURATION_SEC
│   ├── frame.py             # SelectionReason enum, validate_frame_metadata()
│   └── summary.py           # AggregationResult dataclass, validate_timeline(),
│                            #   MalformedAggregationError
├── services/
│   ├── upload.py            # validate → write /data/uploads/ → ffprobe → create job → enqueue
│   ├── status.py            # read job row → StatusResponse
│   └── summary.py           # fetch video_summary → SummaryResponse / TimelineResponse
├── repositories/
│   ├── job_repo.py          # CRUD: videos, video_summary tables
│   ├── frame_repo.py        # CRUD: frames, frame_analysis tables
│   └── ffprobe_client.py    # subprocess ffprobe → FFprobeResult dataclass
├── queue/
│   └── publisher.py         # enqueue_extraction(job_id) — only public method
└── api/
    ├── schemas/
    │   ├── common.py        # ErrorDetail, HealthResponse, PaginatedResponse
    │   ├── video.py         # UploadResponse, StatusResponse, ProgressStage enum
    │   └── summary.py       # SummaryResponse, TimelineEvent, TimelineResponse
    └── routes/
        ├── videos.py        # POST /api/videos  (multipart/form-data, field="file")
        ├── status.py        # GET  /api/videos/{job_id}/status
        ├── summary.py       # GET  /api/videos/{job_id}/summary
        ├── timeline.py      # GET  /api/videos/{job_id}/timeline
        ├── frames.py        # GET  /api/videos/{job_id}/frames
        └── health.py        # GET  /healthz
```

### FFmpeg extractor (`extractor/`)

No HTTP server. Dramatiq actor only.
Own `pyproject.toml` (uv). Key deps: `dramatiq[redis]`, `dramatiq-crontab`, `asyncpg`, `pydantic-settings`, `loguru`, `shared @ ../shared`.

`shared/` used in `queue/consumer.py` (message contracts) and `main.py` (ActorMetricsMiddleware).

```
extractor/
├── pyproject.toml
├── main.py                  # Worker entry: import actors, configure_logging(),
│                            #   init DB pool + Redis at module scope,
│                            #   register ActorMetricsMiddleware on broker
├── core/
│   ├── config.py            # SCENE_THRESHOLD, FRAME_INTERVAL, BATCH_SIZE,
│   │                        #   DATA_ROOT, FFMPEG_BIN, FFPROBE_BIN, MAX_DURATION_SEC
│   └── logging.py           # configure_logging(), LoggerMixin
│                            # ActorMetricsMiddleware imported from shared/
├── domain/
│   ├── frame.py             # FrameMetadata dataclass, SelectionReason enum,
│   │                        #   validate_frame_metadata(), FrameExtractionError
│   └── video.py             # VideoMeta dataclass (duration, fps, resolution, codec,
│                            #   total_frames), DurationExceededError
├── services/
│   ├── probe.py             # ProbeService: FFprobeClient → VideoMeta
│   ├── extraction.py        # ExtractionService: build FFmpeg cmd → run → raw file list
│   ├── metadata.py          # MetadataService: frame_number/fps → timestamp,
│   │                        #   resolve selection_reason, scene_score
│   └── batcher.py           # BatcherService: partition FrameMetadata[] into BATCH_SIZE chunks
├── repositories/
│   ├── ffmpeg_runner.py     # FFmpegRunner: asyncio subprocess, streams stderr
│   ├── ffprobe_client.py    # FFprobeClient: ffprobe JSON → FFprobeResult
│   ├── frame_repo.py        # bulk_insert_frames() via asyncpg executemany()
│   └── job_repo.py          # update_status(), update_progress()
├── queue/
│   ├── consumer.py          # @dramatiq.actor(queue_name='extraction', max_retries=3)
│   └── publisher.py         # enqueue_analysis_batch(job_id, frame_ids)
└── pipeline/
    └── orchestrator.py      # ExtractionOrchestrator.run(job_id)
```

### Worker service (`worker/`)

No HTTP server. Dramatiq actors + dramatiq-crontab scheduler.
Own `pyproject.toml` (uv). Key deps: `dramatiq[redis]`, `dramatiq-crontab`, `asyncpg`, `openai`, `pydantic-settings`, `loguru`, `shared @ ../shared`.

`shared/` used in `queue/consumer.py` (message contracts) and `main.py` (ActorMetricsMiddleware).

```
worker/
├── pyproject.toml
├── main.py                  # Worker entry: import actors, configure_logging(),
│                            #   init DB + Redis at module scope,
│                            #   register ActorMetricsMiddleware on broker
├── scheduler.py             # Crontab declarations only:
│                            #   @crontab(CLEANUP_CRON) schedule_cleanup → cleanup_task.send()
├── core/
│   ├── config.py            # AI_MODEL, AI_BASE_URL, AGGREGATION_MODEL,
│   │                        #   MAX_RETRIES, MIN_BACKOFF_SEC, MAX_BACKOFF_SEC,
│   │                        #   JOB_TTL_DAYS, FAILED_JOB_TTL_DAYS, CLEANUP_CRON
│   └── logging.py
│                            # ActorMetricsMiddleware imported from shared/
├── domain/
│   ├── analysis.py          # FrameAnalysisResult, validate_analysis(), EmptyDescriptionError
│   ├── summary.py           # AggregationResult, TimelineEvent,
│   │                        #   validate_aggregation_json(), MalformedAggregationError
│   └── cleanup.py           # CleanupTarget dataclass, validate_cleanup()
├── services/
│   ├── vision.py            # Read JPEG → base64 (in-memory only) → Vision API
│   ├── aggregator.py        # All descriptions + timestamps → LLM → AggregationResult
│   ├── completion.py        # COUNT check + Redis SET NX EX 60 → enqueue aggregation
│   └── cleanup.py           # delete files, nullify JSONB, mark cleaned_at
├── repositories/
│   ├── ai_client.py         # AIProvider protocol, AsyncOpenAI, base_url override
│   ├── frame_repo.py        # get_frames_by_ids(), get_all_descriptions_for_job()
│   ├── analysis_repo.py     # bulk_insert_analysis(), nullify_raw_responses()
│   ├── summary_repo.py      # upsert_summary() INSERT ON CONFLICT DO UPDATE
│   ├── storage_repo.py      # delete_upload(), delete_frames() — swappable for MinIO
│   └── job_repo.py          # update_status(), update_progress(),
│                            #   get_pending_batch_count(), get_expired_jobs(),
│                            #   is_analysis_complete(), mark_cleaned()
├── queue/
│   └── consumer.py          # analysis_batch_task (max_retries=3)
│                            # aggregation_task (max_retries=1)
│                            # cleanup_task (max_retries=3)
└── pipeline/
    ├── batch_orchestrator.py
    ├── agg_orchestrator.py   # sets expires_at on completion
    └── cleanup_orchestrator.py
```

### Next.js frontend (`frontend/`)

Managed by npm. Key: Next.js 15, Tailwind CSS, TypeScript.
Own `.gitignore` covering `.next/`, `node_modules/`, `.env.local`.
Own `.env.local.example` with `NEXT_PUBLIC_API_URL` and `BACKEND_URL`.

```
frontend/
├── .gitignore
├── .env.local.example
├── next.config.ts            # output: 'standalone'
├── src/
│   ├── app/
│   │   ├── layout.tsx        # RootLayout: font, globals.css, Providers
│   │   ├── page.tsx          # / — Server Component: hero + <UploadCard />
│   │   ├── globals.css
│   │   ├── jobs/[jobId]/
│   │   │   ├── page.tsx      # Server Component: fetch initial status server-side
│   │   │   ├── loading.tsx   # Suspense skeleton
│   │   │   └── error.tsx     # 'use client' error boundary
│   │   └── api/proxy/[...path]/route.ts  # Catch-all → BACKEND_URL (server-only)
│   ├── components/
│   │   ├── upload/
│   │   │   ├── UploadCard.tsx       # 'use client': useUpload, navigation
│   │   │   ├── FileDropzone.tsx     # 'use client': HTML5 drag-and-drop
│   │   │   └── UploadProgress.tsx   # 'use client': XHR progress bar
│   │   ├── job/
│   │   │   ├── JobStatusClient.tsx  # 'use client': useJobPoller, badges, progress
│   │   │   ├── StageBadge.tsx       # Server: stage → colour pill
│   │   │   └── ErrorBanner.tsx      # Server: displays error_message
│   │   ├── summary/
│   │   │   ├── SummaryCard.tsx      # Server: prose summary
│   │   │   └── TimelineList.tsx     # Server: timeline[] → vertical list
│   │   └── ui/
│   │       ├── Button.tsx · Card.tsx · Spinner.tsx · Badge.tsx
│   ├── lib/
│   │   ├── api/
│   │   │   ├── client.ts     # fetchAPI(): base URL, throws APIError on non-2xx
│   │   │   ├── videos.ts     # uploadVideo, getStatus, getSummary, getTimeline
│   │   │   └── types.ts      # All response types — mirrors backend schemas exactly
│   │   ├── hooks/
│   │   │   ├── useJobPoller.ts   # setInterval 3s, stops on completed|failed
│   │   │   └── useUpload.ts      # idle→uploading→polling→done|error, XHR for progress
│   │   ├── utils/
│   │   │   ├── format.ts         # formatTimestamp(), formatBytes()
│   │   │   └── validation.ts     # validateFileType(), validateFileSize()
│   │   └── constants.ts          # POLL_INTERVAL_MS=3000, MAX_FILE_SIZE_BYTES, ACCEPTED_TYPES
│   └── types/index.ts
```

---

## Observability — devtrack-sdk

devtrack-sdk replaces Prometheus + Grafana for MVP. It is a plug-and-play FastAPI
middleware that captures request count, latency, status codes, and per-endpoint
insights using DuckDB for local storage. No separate service required.

Source: https://github.com/pkaranje/devtrack-sdk

### Integration in `app/main.py`

```python
from devtrack import DevTrack          # exact import — verify against repo

app = FastAPI()
DevTrack(app)                          # single-line registration
# All endpoints tracked automatically from this point
```

devtrack provides a built-in dashboard route (typically `/devtrack` or `/analytics`).
Confirm the exact route from the repo README before documenting it.

### What devtrack covers for MVP

| Metric | Covered |
|---|---|
| Request count per endpoint | Yes |
| Latency (avg, p95) | Yes |
| Status code distribution | Yes |
| Per-endpoint breakdown | Yes |
| Worker queue depth | No — log via Loguru |
| AI API retry rate | No — log via Loguru |
| Frame extraction time | No — log via Loguru |

Worker and extractor metrics not covered by devtrack are captured as structured
Loguru log lines with `job_id` in context and can be aggregated via log tooling.

### Worker and extractor actor observability

Both `extractor/main.py` and `worker/main.py` register `ActorMetricsMiddleware`
on the Dramatiq broker. The class lives in `shared/shared/middleware.py` —
imported by both services, defined once.

```python
# shared/shared/middleware.py
import time
import dramatiq
from loguru import logger

class ActorMetricsMiddleware(dramatiq.Middleware):
    def before_process_message(self, broker, message):
        message.options["started_at"] = time.monotonic()

    def after_process_message(self, broker, message, *, result=None, exception=None):
        duration_ms = round(
            (time.monotonic() - message.options["started_at"]) * 1000, 2
        )
        logger.info(
            "actor_completed",
            actor=message.actor_name,
            queue=message.queue_name,
            duration_ms=duration_ms,
            status="failed" if exception else "success",
            job_id=message.kwargs.get("job_id"),
            retries=message.options.get("retries", 0),
        )
```

Registered in `main.py` of both services:

```python
from shared.middleware import ActorMetricsMiddleware

broker = dramatiq.get_broker()
broker.add_middleware(ActorMetricsMiddleware())
```

The `log_call` decorator is applied to all pipeline orchestrator `run()` methods.
Failed actors log `job_id`, `stage`, `error`, and `retry_count` at ERROR level.

**Publisher enqueue logging** — `app/queue/publisher.py` logs every enqueue call:

```python
def enqueue_extraction(self, job_id: str) -> None:
    self.logger.info("extraction_enqueued", job_id=job_id)
    extraction_task.send(job_id)
```

This lets you diff timestamps across services to measure queue wait time.

### shared/messages.py — queue message contracts

Typed payload definitions used by every publisher and actor.
Defined once, imported by all three Python services.

```python
# shared/shared/messages.py
from dataclasses import dataclass

@dataclass
class ExtractionMessage:
    job_id: str

@dataclass
class AnalysisBatchMessage:
    job_id: str
    frame_ids: list[str]

@dataclass
class AggregationMessage:
    job_id: str

# CleanupMessage has no payload — no dataclass needed
```

**Usage per service:**

`app/queue/publisher.py`:
```python
from shared.messages import ExtractionMessage

def enqueue_extraction(self, job_id: str) -> None:
    self.logger.info("extraction_enqueued", job_id=job_id)
    msg = ExtractionMessage(job_id=job_id)
    extraction_task.send(msg.job_id)
```

`extractor/queue/publisher.py`:
```python
from shared.messages import AnalysisBatchMessage

def enqueue_analysis_batch(self, job_id: str, frame_ids: list[str]) -> None:
    msg = AnalysisBatchMessage(job_id=job_id, frame_ids=frame_ids)
    analysis_batch_task.send(msg.job_id, msg.frame_ids)
```

`worker/queue/consumer.py` actor signatures match the contracts exactly:
```python
from shared.messages import AnalysisBatchMessage, AggregationMessage

@dramatiq.actor(queue_name="analysis", max_retries=3)
def analysis_batch_task(job_id: str, frame_ids: list[str]) -> None: ...

@dramatiq.actor(queue_name="aggregation", max_retries=1)
def aggregation_task(job_id: str) -> None: ...
```

If a message payload shape changes, update `shared/messages.py` only.
The type mismatch surfaces at import time in every consumer, not at runtime.

---

## Processing pipeline

```
POST /api/videos  (multipart/form-data, field="file")
  ↓ MIME check → 415 on fail
  ↓ Size check  → 413 on fail
  ↓ FFprobe duration check → 422 on fail
  ↓ Job created in DB (status=queued)
  ↓ Redis: 'extraction' queue

[extractor] extraction_task(job_id)
  ↓ status=running, stage=frame_extraction
  ↓ FFmpeg hybrid extraction → /data/frames/{job_id}/
  ↓ FrameMetadata bulk inserted into frames table
  ↓ Frames partitioned into BATCH_SIZE chunks
  ↓ Redis: 'analysis' queue (one message per batch)

[worker × 4] analysis_batch_task(job_id, frame_ids)
  ↓ Read JPEGs → base64 in memory → Vision API (base64 discarded after)
  ↓ frame_analysis rows inserted
  ↓ progress_pct updated
  ↓ CompletionChecker: COUNT(frame_analysis) == COUNT(frames)?
      → Redis SET NX EX 60 agg_lock:{job_id}
      → Redis: 'aggregation' queue

[worker] aggregation_task(job_id)
  ↓ stage=aggregation
  ↓ All descriptions ordered by timestamp → aggregation LLM prompt
  ↓ Parse JSON: { summary, timeline[] }
  ↓ video_summary upserted
  ↓ status=completed, expires_at=NOW()+JOB_TTL_DAYS

[scheduler @ CLEANUP_CRON] cleanup_task()
  ↓ SELECT jobs WHERE expires_at < NOW() AND cleaned_at IS NULL
  ↓ is_analysis_complete()? skip if not
  ↓ delete /data/uploads/ + /data/frames/
  ↓ nullify frame_analysis.ai_response (keep description)
  ↓ mark cleaned_at = NOW()
```

---

## Queue names

| Queue | Producer | Consumer | Payload |
|---|---|---|---|
| `extraction` | FastAPI `queue/publisher.py` | Extractor consumer | `job_id` |
| `analysis` | Extractor `queue/publisher.py` | Worker consumer | `job_id, frame_ids[]` |
| `aggregation` | Worker `services/completion.py` | Worker consumer | `job_id` |
| `cleanup` | Worker `scheduler.py` (crontab) | Worker consumer | _(none)_ |

---

## Shared volume mounts

| Path | Writer | Reader |
|---|---|---|
| `/data/uploads/` | FastAPI UploadService | Extractor FFmpegRunner |
| `/data/frames/{job_id}/` | Extractor ExtractionService | Worker VisionService |
| `/data/logs/` | All services (Loguru) | Ops |

Base64 is in-memory only at the Vision API call boundary. Never stored on disk or in DB.

---

## Database schema

### videos
`id UUID PK` · `filename TEXT` · `status TEXT` · `stage TEXT` · `progress_pct INT DEFAULT 0`
`error_message TEXT` · `duration_seconds FLOAT` · `resolution TEXT` · `fps FLOAT`
`file_size_bytes BIGINT` · `uploaded_at TIMESTAMPTZ` · `completed_at TIMESTAMPTZ`
`expires_at TIMESTAMPTZ` · `cleaned_at TIMESTAMPTZ`

### frames
`id UUID PK` · `video_id UUID FK CASCADE` · `frame_path TEXT` · `timestamp FLOAT`
`frame_number INT` · `selection_reason TEXT` · `scene_score FLOAT` · `created_at TIMESTAMPTZ`

### frame_analysis
`id UUID PK` · `frame_id UUID FK CASCADE` · `ai_response JSONB` (nullified after TTL)
`description TEXT` (retained indefinitely) · `model_used TEXT` · `created_at TIMESTAMPTZ`

### video_summary
`id UUID PK` · `video_id UUID FK UNIQUE` · `summary TEXT` · `timeline JSONB`
`is_partial BOOL DEFAULT FALSE` · `model_used TEXT` · `generated_at TIMESTAMPTZ`

---

## Job status lifecycle

```
queued → running → completed
                 ↘ failed  (error_message populated)
```

Stages: `upload_validation` → `frame_extraction` → `ai_analysis` → `aggregation` → `completed`

---

## Retry policy

| Actor | Queue | max_retries | Back-off |
|---|---|---|---|
| `extraction_task` | extraction | 3 | Dramatiq exponential 15s/30s/60s |
| `analysis_batch_task` | analysis | 3 | Exponential 15s–120s |
| `aggregation_task` | aggregation | 1 | Flat 30s |
| `cleanup_task` | cleanup | 3 | Dramatiq exponential |

All failed actors after exhausting retries go to Redis DLQ.

---

## Cleanup retention tiers

| Artifact | Retained for | Action |
|---|---|---|
| `/data/uploads/*.mp4` | JOB_TTL_DAYS | `storage_repo.delete_upload()` |
| `/data/frames/{job_id}/` | JOB_TTL_DAYS | `storage_repo.delete_frames()` |
| `frame_analysis.ai_response` | JOB_TTL_DAYS then nullified | `analysis_repo.nullify_raw_responses()` |
| `frame_analysis.description` | Indefinite | Never deleted |
| `video_summary` | Indefinite | Never deleted |

Failed jobs use `FAILED_JOB_TTL_DAYS` (default 1).

---

## Environment variables

| Variable | Default | Service |
|---|---|---|
| `SCENE_THRESHOLD` | `0.35` | Extractor |
| `FRAME_INTERVAL` | `150` | Extractor |
| `BATCH_SIZE` | `5` | Extractor + Worker |
| `WORKER_COUNT` | `4` | Worker |
| `WORKER_CONCURRENCY` | `3` | Worker |
| `MAX_FILE_SIZE_MB` | `500` | FastAPI |
| `MAX_DURATION_SEC` | `600` | FastAPI + Extractor |
| `AI_MODEL` | `gpt-4o` | Worker |
| `AI_BASE_URL` | — | Worker |
| `AGGREGATION_MODEL` | `gpt-4o` | Worker |
| `MAX_RETRIES` | `3` | Worker |
| `MIN_BACKOFF_SEC` | `15` | Worker |
| `MAX_BACKOFF_SEC` | `120` | Worker |
| `JOB_TTL_DAYS` | `7` | Worker |
| `FAILED_JOB_TTL_DAYS` | `1` | Worker |
| `CLEANUP_CRON` | `0 2 * * *` | Worker scheduler |
| `OPENAI_API_KEY` | — | Worker |
| `DATABASE_URL` | — | FastAPI + Extractor + Worker |
| `REDIS_URL` | — | All Python services |
| `BACKEND_URL` | `http://api:8000` | Frontend Route Handler only |
| `NEXT_PUBLIC_API_URL` | `/api/proxy` | Frontend client-side |

---

## API endpoints

| Method | Path | Status | Notes |
|---|---|---|---|
| POST | `/api/videos` | 202 | `{ job_id, status }` |
| GET | `/api/videos/{job_id}/status` | 200 | Includes stage, progress_pct, error_message |
| GET | `/api/videos/{job_id}/summary` | 200 | 404 if not completed |
| GET | `/api/videos/{job_id}/timeline` | 200 | 404 if not completed |
| GET | `/api/videos/{job_id}/frames` | 200 | Frame metadata list |
| GET | `/healthz` | 200 | `{ "status": "ok" }` |

Upload errors: `415` wrong MIME · `413` too large · `422` duration exceeded.

---

## Docker Compose services

`frontend` · `api` · `redis` · `postgres` · `ffmpeg-extractor`
`worker-1` · `worker-2` · `worker-3` · `worker-4` · `scheduler`

Peak RAM ~5 GB. Reduce `WORKER_COUNT` to 2 if headroom is tight.
Scheduler runs `python -m dramatiq_crontab worker.scheduler` only (~50 MB).

---

## GitHub Actions CI/CD

### `.github/workflows/ci.yml` — runs on every PR

```
trigger: pull_request → main
jobs:
  lint:   ruff check + ruff format --check (app/, extractor/, worker/)
  test:   pytest with test PostgreSQL + Redis services
          covers: domain unit tests, repository integration tests,
                  pipeline integration tests (mock AI client)
```

### `.github/workflows/build.yml` — runs on merge to main

```
trigger: push → main
jobs:
  build:  docker build for api, extractor, worker, frontend
          tag as ghcr.io/pkaranje/video-summarizer/{service}:sha
          push to GitHub Container Registry
```

Secrets required: `GHCR_TOKEN`, `OPENAI_API_KEY` (test env only).

---

## Naming conventions

| Item | Convention | Example |
|---|---|---|
| Python files | snake_case | `job_repo.py`, `vision.py` |
| Python classes | PascalCase | `VisionService`, `JobRepository` |
| Python functions | snake_case | `bulk_insert_frames()` |
| TS components | PascalCase | `UploadCard.tsx` |
| TS lib files | camelCase | `useJobPoller.ts` |
| TS interfaces | PascalCase | `StatusResponse`, `TimelineEvent` |
| DB tables | snake_case plural | `frame_analysis`, `video_summary` |
| DB columns | snake_case | `progress_pct`, `expires_at` |
| Env vars | UPPER_SNAKE_CASE | `JOB_TTL_DAYS`, `SCENE_THRESHOLD` |
| Docker services | kebab-case | `ffmpeg-extractor`, `worker-1` |
| Redis keys | colon-namespaced | `agg_lock:{job_id}` |
| Queue names | snake_case strings | `'extraction'`, `'cleanup'` |

---

## Not in scope (MVP)

Live streaming · audio transcription · face recognition · object tracking
Kubernetes · authentication · MinIO (Phase 2) · semantic search (Phase 2)
