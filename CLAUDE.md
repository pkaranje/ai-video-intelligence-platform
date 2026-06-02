# CLAUDE.md — AI Video Summarization Platform

## Project overview

Users upload MP4 videos via a web UI. The system extracts representative frames,
runs them through an OpenAI-compatible Vision API in parallel, and returns an
AI-generated prose summary plus a timestamped event timeline.

Single-server Docker Compose deployment. 4 vCPU, 8 GB RAM.

---

## Monorepo layout

```
/
├── services/
│   ├── api/                  # FastAPI backend
│   │   ├── api/              # Python package
│   │   ├── pyproject.toml
│   │   ├── Makefile
│   │   ├── Dockerfile
│   │   └── .gitignore
│   ├── extractor/            # FFmpeg extractor (Dramatiq, no HTTP)
│   │   ├── extractor/        # Python package
│   │   ├── pyproject.toml
│   │   ├── Makefile
│   │   ├── Dockerfile
│   │   └── .gitignore
│   └── worker/               # AI analysis + aggregation + cleanup (Dramatiq, no HTTP)
│       ├── worker/           # Python package
│       ├── pyproject.toml
│       ├── Makefile
│       ├── Dockerfile
│       └── .gitignore
├── libs/
│   └── shared/               # Internal shared library
│       ├── shared/           # Python package
│       │   ├── __init__.py
│       │   ├── middleware.py
│       │   └── messages.py
│       ├── pyproject.toml
│       └── Makefile
├── frontend/                 # Next.js 15 App Router
│   ├── src/
│   ├── package.json
│   ├── Makefile
│   └── Dockerfile
├── tests/                    # Integration + unit tests (repo root)
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── build.yml
├── docker-compose.yml
├── Makefile                  # Root — delegates to service Makefiles
├── pyproject.toml            # Tooling config only (ruff + pytest)
├── .env.example
├── .env.docker.example
└── .gitignore
```

---

## Package naming and import rules

Each service directory contains a Python package with the same name as the service.
The outer directory is the project root. The inner directory is the Python package.

```
services/api/api/         ← package "api"        → from api.core.config import ...
services/extractor/extractor/  ← package "extractor" → from extractor.core.config import ...
services/worker/worker/   ← package "worker"     → from worker.core.config import ...
libs/shared/shared/       ← package "shared"     → from shared.messages import ...
```

Each `pyproject.toml` declares its package explicitly to prevent nesting:
```toml
[tool.hatch.build.targets.wheel]
packages = ["api"]        # or "extractor", "worker", "shared"
```

### shared/ dependency declaration

All three services depend on shared:
```toml
dependencies = [
    "shared @ { path = '../../libs/shared', develop = true }",
]
```

### Import boundary

| Service | May import from shared | What |
|---|---|---|
| `services/api/api/queue/` | Yes | `messages.py` only |
| `services/api/` everywhere else | No | — |
| `services/extractor/` | Yes | `messages.py` + `middleware.py` |
| `services/worker/` | Yes | `messages.py` + `middleware.py` |
| `frontend/` | No | — |

---

## Architecture rules

### Dependency direction (all Python services)

```
routes/actors → services → repositories → DB / Redis / external
```

- Routes never import repositories directly
- Services never import routes or schemas
- Repositories never import services
- `domain/` is pure Python — zero external imports, fully unit-testable
- Queue publishers called by services only, never by routes
- Pipeline orchestrators wire services — contain no business logic

### Layer responsibilities

| Layer | Does | Never does |
|---|---|---|
| `routes/` | Parse request, call service, return response | Business logic, DB queries |
| `services/` | Orchestrate: validate → persist → enqueue | HTTP concerns, raw SQL |
| `repositories/` | DB CRUD, subprocess calls, external API | Business logic |
| `domain/` | Pure validation, typed exceptions, enums | Any I/O |
| `queue/publisher` | `send_message()` wrapper only | Actor definition, retry config |
| `pipeline/` | Sequence service calls | Own any logic |

---

## Service architectures

### 1. libs/shared/

```
libs/shared/
├── pyproject.toml          # name="shared", packages=["shared"]
├── Makefile
└── shared/
    ├── __init__.py
    ├── middleware.py        # ActorMetricsMiddleware
    └── messages.py         # ExtractionMessage, AnalysisBatchMessage, AggregationMessage
```

**shared/middleware.py**
```python
import time
import dramatiq
from loguru import logger

class ActorMetricsMiddleware(dramatiq.Middleware):
    def before_process_message(self, broker, message):
        message.options["started_at"] = time.monotonic()

    def after_process_message(self, broker, message, *, result=None, exception=None):
        duration_ms = round((time.monotonic() - message.options["started_at"]) * 1000, 2)
        logger.info("actor_completed",
            actor=message.actor_name,
            queue=message.queue_name,
            duration_ms=duration_ms,
            status="failed" if exception else "success",
            job_id=message.kwargs.get("job_id"),
            retries=message.options.get("retries", 0),
        )
```

**shared/messages.py**
```python
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
```

---

### 2. services/api/

```
services/api/
├── pyproject.toml          # name="api", packages=["api"]
├── Makefile
├── Dockerfile
├── .gitignore
├── alembic.ini
├── alembic/
│   ├── env.py
│   └── versions/
│       └── 0001_initial.py
└── api/
    ├── __init__.py
    ├── main.py             # FastAPI app factory, lifespan, routers, devtrack-sdk
    ├── core/
    │   ├── __init__.py
    │   ├── config.py       # pydantic-settings Settings, lru_cache
    │   ├── dependencies.py # DI: get_db, get_redis, get_*_service
    │   ├── middleware.py   # RequestLoggingMiddleware
    │   └── logging.py      # configure_logging(), LoggerMixin, log_call
    ├── domain/
    │   ├── __init__.py
    │   ├── video.py        # VideoStatus, validate_upload(), typed errors
    │   ├── frame.py        # SelectionReason, validate_frame_metadata()
    │   └── summary.py      # AggregationResult, validate_timeline()
    ├── db/
    │   ├── __init__.py
    │   └── models.py       # SQLAlchemy async models — all 4 tables
    ├── repositories/
    │   ├── __init__.py
    │   ├── job_repo.py
    │   ├── frame_repo.py
    │   └── ffprobe_client.py
    ├── services/
    │   ├── __init__.py
    │   ├── upload.py
    │   ├── status.py
    │   └── summary.py
    ├── queue/
    │   ├── __init__.py
    │   └── publisher.py    # enqueue_extraction() — imports ExtractionMessage
    └── schemas/
        ├── __init__.py
        ├── common.py
        ├── video.py        # UploadResponse, StatusResponse, ProgressStage, JobStatus
        └── summary.py      # SummaryResponse, TimelineEvent, TimelineResponse
```

Note: `routes/` lives inside `api/` not in a separate `api/` directory:

```
api/
└── routes/
    ├── __init__.py
    ├── videos.py    # POST /api/videos
    ├── status.py    # GET  /api/videos/{job_id}/status
    ├── summary.py   # GET  /api/videos/{job_id}/summary
    ├── timeline.py  # GET  /api/videos/{job_id}/timeline
    ├── frames.py    # GET  /api/videos/{job_id}/frames
    └── health.py    # GET  /healthz
```

**Entry point:** `uvicorn api.main:app`

---

### 3. services/extractor/

```
services/extractor/
├── pyproject.toml          # name="extractor", packages=["extractor"]
├── Makefile
├── Dockerfile
├── .gitignore
└── extractor/
    ├── __init__.py
    ├── main.py             # Dramatiq entry, ActorMetricsMiddleware registration
    ├── core/
    │   ├── __init__.py
    │   ├── config.py
    │   └── logging.py
    ├── domain/
    │   ├── __init__.py
    │   ├── video.py        # VideoMeta, DurationExceededError
    │   └── frame.py        # FrameMetadata, SelectionReason, FrameExtractionError
    ├── repositories/
    │   ├── __init__.py
    │   ├── ffprobe_client.py
    │   ├── ffmpeg_runner.py
    │   ├── frame_repo.py
    │   └── job_repo.py
    ├── services/
    │   ├── __init__.py
    │   ├── probe.py
    │   ├── extraction.py
    │   ├── metadata.py
    │   └── batcher.py
    ├── pipeline/
    │   ├── __init__.py
    │   └── orchestrator.py # ExtractionOrchestrator.run(job_id)
    └── queue/
        ├── __init__.py
        ├── consumer.py     # extraction_task actor
        └── publisher.py    # enqueue_analysis_batch()
```

**Entry point:** `dramatiq extractor.main`

---

### 4. services/worker/

```
services/worker/
├── pyproject.toml          # name="worker", packages=["worker"]
├── Makefile
├── Dockerfile
├── .gitignore
└── worker/
    ├── __init__.py
    ├── main.py             # Dramatiq entry, ActorMetricsMiddleware registration
    ├── scheduler.py        # @crontab declarations only
    ├── core/
    │   ├── __init__.py
    │   ├── config.py
    │   └── logging.py
    ├── domain/
    │   ├── __init__.py
    │   ├── analysis.py     # FrameAnalysisResult, validate_analysis()
    │   ├── summary.py      # AggregationResult, validate_aggregation_json()
    │   └── cleanup.py      # CleanupTarget
    ├── repositories/
    │   ├── __init__.py
    │   ├── ai_client.py    # AIProvider protocol, AsyncOpenAI, retry
    │   ├── frame_repo.py
    │   ├── analysis_repo.py
    │   ├── summary_repo.py
    │   ├── storage_repo.py # delete_upload(), delete_frames()
    │   └── job_repo.py
    ├── services/
    │   ├── __init__.py
    │   ├── vision.py       # base64 in-memory only
    │   ├── aggregator.py
    │   ├── completion.py   # Redis SET NX EX 60 lock
    │   └── cleanup.py
    ├── pipeline/
    │   ├── __init__.py
    │   ├── batch_orchestrator.py
    │   ├── agg_orchestrator.py
    │   └── cleanup_orchestrator.py
    └── queue/
        ├── __init__.py
        └── consumer.py     # analysis_batch_task, aggregation_task, cleanup_task
```

**Entry point:** `dramatiq worker.main`
**Scheduler:** `python -m dramatiq_crontab worker.scheduler`

---

### 5. frontend/

```
frontend/
├── package.json
├── next.config.ts          # output: 'standalone'
├── tsconfig.json           # strict, @/components @/lib @/types aliases
├── Makefile
├── Dockerfile
├── .gitignore
├── .env.local.example
└── src/
    ├── app/
    │   ├── layout.tsx
    │   ├── page.tsx
    │   ├── globals.css
    │   ├── jobs/[jobId]/
    │   │   ├── page.tsx    # Server Component — fetches initial status
    │   │   ├── loading.tsx
    │   │   └── error.tsx
    │   └── api/proxy/[...path]/route.ts  # Catch-all → BACKEND_URL
    ├── components/
    │   ├── upload/
    │   │   ├── UploadCard.tsx       # 'use client'
    │   │   ├── FileDropzone.tsx     # 'use client'
    │   │   └── UploadProgress.tsx   # 'use client'
    │   ├── job/
    │   │   ├── JobStatusClient.tsx  # 'use client'
    │   │   ├── StageBadge.tsx
    │   │   └── ErrorBanner.tsx
    │   ├── summary/
    │   │   ├── SummaryCard.tsx
    │   │   └── TimelineList.tsx
    │   └── ui/
    │       ├── Badge.tsx
    │       ├── Button.tsx
    │       ├── Card.tsx
    │       └── Spinner.tsx
    ├── lib/
    │   ├── api/
    │   │   ├── client.ts
    │   │   ├── videos.ts
    │   │   └── types.ts
    │   ├── hooks/
    │   │   ├── useJobPoller.ts
    │   │   └── useUpload.ts
    │   ├── utils/
    │   │   ├── format.ts
    │   │   └── validation.ts
    │   └── constants.ts
    └── types/
        └── index.ts
```

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
`id UUID PK` · `frame_id UUID FK CASCADE` · `ai_response JSONB` · `description TEXT`
`model_used TEXT` · `created_at TIMESTAMPTZ`

### video_summary
`id UUID PK` · `video_id UUID FK UNIQUE` · `summary TEXT` · `timeline JSONB`
`is_partial BOOL DEFAULT FALSE` · `model_used TEXT` · `generated_at TIMESTAMPTZ`

---

## Processing pipeline

```
POST /api/videos
  → validate MIME + size → FFprobe duration check
  → job created (queued) → Redis: extraction queue

[extractor] extraction_task(job_id)
  → FFmpeg hybrid extraction → frames to /data/frames/{job_id}/
  → frame metadata to DB → Redis: analysis queue (per batch)

[worker ×4] analysis_batch_task(job_id, frame_ids)
  → JPEG → base64 in memory → Vision API → frame_analysis rows
  → CompletionChecker: all batches done?
    → Redis SET NX EX 60 agg_lock:{job_id} → Redis: aggregation queue

[worker] aggregation_task(job_id)
  → all descriptions → LLM → video_summary row → status=completed

[scheduler @CLEANUP_CRON] cleanup_task()
  → expired jobs → delete files → nullify ai_response → cleaned_at=NOW()
```

---

## Queue names

| Queue | Producer | Consumer | Payload |
|---|---|---|---|
| `extraction` | api `queue/publisher.py` | extractor consumer | `job_id` |
| `analysis` | extractor `queue/publisher.py` | worker consumer | `job_id, frame_ids[]` |
| `aggregation` | worker `services/completion.py` | worker consumer | `job_id` |
| `cleanup` | worker `scheduler.py` | worker consumer | — |

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

---

## Cleanup retention

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

| Variable | Default | Owner |
|---|---|---|
| `DATABASE_URL` | — | api, extractor, worker |
| `REDIS_URL` | — | api, extractor, worker |
| `OPENAI_API_KEY` | — | worker |
| `AI_MODEL` | `gpt-4o` | worker |
| `AI_BASE_URL` | — | worker |
| `AGGREGATION_MODEL` | `gpt-4o` | worker |
| `MAX_RETRIES` | `3` | worker |
| `MIN_BACKOFF_SEC` | `15` | worker |
| `MAX_BACKOFF_SEC` | `120` | worker |
| `SCENE_THRESHOLD` | `0.35` | extractor |
| `FRAME_INTERVAL` | `150` | extractor |
| `BATCH_SIZE` | `5` | extractor, worker |
| `MAX_FILE_SIZE_MB` | `500` | api |
| `MAX_DURATION_SEC` | `600` | api, extractor |
| `DATA_ROOT` | `/data` | api, extractor, worker |
| `JOB_TTL_DAYS` | `7` | worker |
| `FAILED_JOB_TTL_DAYS` | `1` | worker |
| `CLEANUP_CRON` | `0 2 * * *` | worker |
| `BACKEND_URL` | `http://api:8000` | frontend (server-side only) |
| `NEXT_PUBLIC_API_URL` | `/api/proxy` | frontend (client-side) |

---

## API endpoints

| Method | Path | Status | Notes |
|---|---|---|---|
| POST | `/api/videos` | 202 | `multipart/form-data`, field=`file` |
| GET | `/api/videos/{job_id}/status` | 200 | stage, progress_pct, error_message |
| GET | `/api/videos/{job_id}/summary` | 200 | 404 if not completed |
| GET | `/api/videos/{job_id}/timeline` | 200 | 404 if not completed |
| GET | `/api/videos/{job_id}/frames` | 200 | frame metadata list |
| GET | `/healthz` | 200 | `{"status":"ok"}` |

Upload errors: `415` wrong MIME · `413` too large · `422` duration exceeded

---

## Docker Compose services

| Service | Build context | Est. RAM |
|---|---|---|
| `postgres` | postgres:16-alpine | 512 MB |
| `redis` | redis:7-alpine | 256 MB |
| `api` | `.` dockerfile: `services/api/Dockerfile` | 512 MB |
| `frontend` | `./frontend` | 256 MB |
| `ffmpeg-extractor` | `.` dockerfile: `services/extractor/Dockerfile` | 1.5 GB peak |
| `worker-1..4` | `.` dockerfile: `services/worker/Dockerfile` | 512 MB ×4 |
| `scheduler` | `.` dockerfile: `services/worker/Dockerfile` | ~50 MB |

All Python services use repo root as build context so `libs/shared/` is accessible.

---

## Makefile structure

```
Makefile                      ← root: delegates via $(MAKE) -C
libs/shared/Makefile          ← install, lint, lint-fix, clean
services/api/Makefile         ← install, lint, test, db-*, shell, shell-db
services/extractor/Makefile   ← install, lint, shell, logs
services/worker/Makefile      ← install, lint, shell-1..4, logs, trigger-cleanup
frontend/Makefile             ← install, dev, build, typecheck, lint, shell
```

Root install order: `shared → api → extractor → worker → frontend`

---

## Naming conventions

| Item | Convention | Example |
|---|---|---|
| Python files | snake_case | `job_repo.py` |
| Python classes | PascalCase | `VisionService` |
| Python functions | snake_case | `bulk_insert_frames()` |
| TS components | PascalCase | `UploadCard.tsx` |
| TS lib files | camelCase | `useJobPoller.ts` |
| DB tables | snake_case plural | `frame_analysis` |
| DB columns | snake_case | `progress_pct` |
| Env vars | UPPER_SNAKE_CASE | `JOB_TTL_DAYS` |
| Docker services | kebab-case | `ffmpeg-extractor` |
| Redis keys | colon-namespaced | `agg_lock:{job_id}` |

---

## Not in scope (MVP)

Live streaming · audio transcription · face recognition · object tracking
Kubernetes · authentication · MinIO (Phase 2) · semantic search (Phase 2)
