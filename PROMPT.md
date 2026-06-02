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

.gitignore
  Python: __pycache__/, *.py[cod], .venv/, .pytest_cache/, .ruff_cache/,
          *.egg-info/, dist/, .coverage, htmlcov/
  Env:    .env, .env.docker  (NOT .env.example or .env.docker.example)
  Node:   node_modules/, .next/, frontend/out/
  Data:   data/
  IDE:    .vscode/, .idea/, *.swp
  Note:   uv.lock is NOT ignored — commit it

.env.example
  All variables from CLAUDE.md environment variables table.
  Group by: Database, Redis, AI, Extraction, Workers, Cleanup, Frontend.
  Placeholder values. One comment per line.

.env.docker.example
  DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/videosumm
  REDIS_URL=redis://redis:6379
  DATA_ROOT=/data
  BACKEND_URL=http://api:8000

pyproject.toml  (root — tooling config only, NOT a package, NOT a workspace)
  [tool.ruff] line-length=100, target-version="py312"
  [tool.ruff.lint] select=["E","F","I","UP","B","SIM"]
  [tool.pytest.ini_options] asyncio_mode="auto", testpaths=["tests"]

docker-compose.yml  (skeleton only — services added in later steps)
  version: "3.9"
  volumes: postgres_data, redis_data, app_data
  networks: default, name: videosumm

Run: make env-check
```

**Verify:**
- [ ] `.env` is gitignored, `.env.example` is not
- [ ] `make env-check` creates `.env.docker` from `.env.docker.example`

---

### Step 2 — Root Makefile
**Model: `claude-haiku-4-5`**

```
Create the root Makefile.

Pattern: delegates to service Makefiles via $(MAKE) -C <path> <target>
Never duplicates service-level logic in the root.

Wildcard delegation rules:
  shared-%:    $(MAKE) -C libs/shared $*
  api-%:       $(MAKE) -C services/api $*
  extractor-%: $(MAKE) -C services/extractor $*
  worker-%:    $(MAKE) -C services/worker $*
  frontend-%:  $(MAKE) -C frontend $*

Aggregate targets (fan out to services):
  env-check    copy .env.docker.example → .env.docker if missing
  install      libs/shared → services/api → services/extractor → services/worker → frontend
  lint         libs/shared + services/api + services/extractor + services/worker
  lint-fix     same with --fix
  test         delegates to services/api

Docker targets (direct docker compose calls):
  build        docker compose build
  up           docker compose up -d  then print: API http://localhost:8000 | UI http://localhost:3000
  up-dev       docker compose up
  up-api       postgres + redis + api
  up-frontend  postgres + redis + api + frontend
  up-extractor postgres + redis + api + ffmpeg-extractor
  up-workers   postgres + redis + api + ffmpeg-extractor + worker-1..4 + scheduler
  down         docker compose down
  restart      down then up
  logs         docker compose logs -f

DB targets (delegate to services/api):
  db-migrate   $(MAKE) -C services/api db-migrate
  db-rollback  $(MAKE) -C services/api db-rollback
  db-reset     $(MAKE) -C services/api db-reset

Cleanup:
  clean        loop $(MAKE) -C $$svc clean for all services
  clean-all    clean + docker image prune -f

make help must print every target with a short description.
```

**Verify:**
- [ ] `make help` prints all targets
- [ ] `make env-check` works

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
  ActorMetricsMiddleware as defined in CLAUDE.md observability section.
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

Create:

services/api/pyproject.toml
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

services/api/.gitignore
  __pycache__/, *.py[cod], .venv/, .pytest_cache/, .ruff_cache/

services/api/Makefile
  install    uv sync
  lint       uv run ruff check api/ && uv run ruff format --check api/
  lint-fix   uv run ruff check --fix api/ && uv run ruff format api/
  test       uv run pytest ../../tests/ -v
  test-unit  uv run pytest ../../tests/unit/ -v
  test-integration  uv run pytest ../../tests/integration/ -v
  db-migrate   uv run alembic upgrade head
  db-rollback  uv run alembic downgrade -1
  db-reset     drop + recreate + migrate (print warning, require confirmation)
  shell        docker compose -f ../../docker-compose.yml exec api /bin/bash
  shell-db     docker compose -f ../../docker-compose.yml exec postgres psql -U postgres -d videosumm
  shell-redis  docker compose -f ../../docker-compose.yml exec redis redis-cli
  clean        remove __pycache__, .pytest_cache, .ruff_cache
  clean-all    clean + remove .venv
  help

services/api/api/__init__.py  (empty)

services/api/api/core/__init__.py  (empty)

services/api/api/core/config.py
  Settings(BaseSettings) with @lru_cache.
  Fields from CLAUDE.md: DATABASE_URL, REDIS_URL, MAX_FILE_SIZE_MB=500,
  MAX_DURATION_SEC=600, DATA_ROOT="/data", BATCH_SIZE=5,
  JOB_TTL_DAYS=7, FAILED_JOB_TTL_DAYS=1.

services/api/api/core/logging.py
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

services/api/api/domain/__init__.py  (empty)

services/api/api/domain/video.py
  VideoStatus enum: queued, running, completed, failed
  UploadTooLargeError(ValueError), UnsupportedFormatError(ValueError)
  validate_upload(filename, content_type, size_bytes) -> None
    UnsupportedFormatError if content_type != "video/mp4"
    UploadTooLargeError if size_bytes > MAX_FILE_SIZE_MB * 1024 * 1024

services/api/api/domain/frame.py
  SelectionReason enum: scene_change, periodic, both
  FrameValidationError
  validate_frame_metadata(metadata: dict) -> None
    required keys: video_id, frame_id, frame_path, timestamp,
    frame_number, selection_reason

services/api/api/domain/summary.py
  MalformedAggregationError
  AggregationResult dataclass: summary (str), timeline (list[dict])
  validate_timeline(timeline: list) -> None
    each item needs timestamp (float) and event (str)

Create database models:

services/api/api/db/__init__.py  (empty)

services/api/api/db/models.py
  Async SQLAlchemy Base. All 4 tables from CLAUDE.md schema.
  videos: all columns including expires_at TIMESTAMPTZ, cleaned_at TIMESTAMPTZ.
  frames: all columns including created_at TIMESTAMPTZ.
  frame_analysis: id, frame_id FK, ai_response JSONB, description TEXT,
    model_used TEXT, created_at TIMESTAMPTZ.
  video_summary: id, video_id FK UNIQUE, summary TEXT, timeline JSONB,
    is_partial BOOL DEFAULT FALSE, model_used TEXT, generated_at TIMESTAMPTZ.
  UUID primary keys. TIMESTAMPTZ for all timestamps.

Create Alembic:

services/api/alembic.ini  (script_location = alembic)

services/api/alembic/env.py
  Async-compatible, asyncio + asyncpg.
  Import Base from api.db.models.

services/api/alembic/versions/0001_initial.py
  Creates all 4 tables with every column.
  expires_at and cleaned_at must be in this migration.

Run: cd services/api && make db-migrate
Report output.
```

**Verify:**
- [ ] `make db-migrate` applies 0001_initial with zero errors
- [ ] All 4 tables exist in DB with correct columns
- [ ] No imports outside stdlib in any domain file

---

### Step 6 — API repositories and services
**Model: `claude-sonnet-4-6`**

```
Read CLAUDE.md — repository and service layer rules.
Working in services/api/. No business logic in repositories.
All repositories inherit LoggerMixin.

Repositories:

services/api/api/repositories/__init__.py
  BaseRepository(LoggerMixin)

services/api/api/repositories/job_repo.py
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

services/api/api/repositories/frame_repo.py
  FrameRepository(BaseRepository)
  bulk_insert_frames(frames: list[dict]) -> list[str]
  get_frames_for_job(job_id) -> list[Frame]
  get_descriptions_for_job(job_id) -> list[dict]
    JOIN frames + frame_analysis ORDER BY timestamp ASC
    returns [{timestamp, description}]

services/api/api/repositories/ffprobe_client.py
  FFprobeResult dataclass: duration_seconds, fps, width, height, codec
  FFprobeError
  FFprobeClient.probe(video_path) -> FFprobeResult
    ffprobe -v quiet -print_format json -show_format -show_streams
    asyncio.create_subprocess_exec. Raise FFprobeError on failure.

Services (orchestrate — no SQL):

services/api/api/services/__init__.py
  BaseService(LoggerMixin)

services/api/api/services/upload.py
  UploadService.upload(file: UploadFile) -> UploadResponse
  Exact order:
    validate_upload() → write {DATA_ROOT}/uploads/{job_id}.mp4
    → FFprobeClient.probe() → raise if duration > MAX_DURATION_SEC
    → job_repo.create() → publisher.enqueue_extraction(job_id)
    → return UploadResponse

services/api/api/services/status.py
  StatusService.get(job_id) -> StatusResponse
  404 if not found. Map all DB fields.

services/api/api/services/summary.py
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

Queue publisher (stub — wired for real in Step 17):

services/api/api/queue/__init__.py  (empty)

services/api/api/queue/publisher.py
  from shared.messages import ExtractionMessage
  class RedisPublisher(LoggerMixin):
    def enqueue_extraction(self, job_id: str) -> None:
      msg = ExtractionMessage(job_id=job_id)
      self.logger.info("extraction_enqueued", job_id=msg.job_id)
      pass  # TODO: real Dramatiq send added in Step 17

Schemas:

services/api/api/schemas/__init__.py  (empty)
services/api/api/schemas/common.py
  ErrorDetail(message: str, code: str), HealthResponse(status: str)

services/api/api/schemas/video.py
  ProgressStage Literal:
    upload_validation, frame_extraction, ai_analysis, aggregation, completed
  JobStatus Literal: queued, running, completed, failed
  UploadResponse(job_id: str, status: str)
  StatusResponse(job_id, status, stage, progress_pct,
    error_message, created_at, updated_at)

services/api/api/schemas/summary.py
  TimelineEvent(timestamp: float, event: str)
  SummaryResponse(job_id, summary, word_count, generated_at)
  TimelineResponse(job_id, timeline: list[TimelineEvent])

Dependencies + middleware:

services/api/api/core/dependencies.py
  get_db() -> AsyncSession
  get_redis() -> Redis
  get_job_repo(), get_frame_repo()
  get_upload_service(), get_status_service(), get_summary_service()

services/api/api/core/middleware.py
  RequestLoggingMiddleware:
    UUID request_id per request, bind to structlog context.
    Log method, path, status_code, duration_ms on every response.

Routes:

services/api/api/routes/__init__.py  (empty)
services/api/api/routes/health.py    GET /healthz → HealthResponse(status="ok")
services/api/api/routes/videos.py    POST /api/videos → 202 UploadResponse
services/api/api/routes/status.py    GET /api/videos/{job_id}/status
services/api/api/routes/summary.py   GET /api/videos/{job_id}/summary
services/api/api/routes/timeline.py  GET /api/videos/{job_id}/timeline
services/api/api/routes/frames.py    GET /api/videos/{job_id}/frames

App factory:

services/api/api/main.py
  FastAPI(). Mount all routers (/api prefix except /healthz).
  Add RequestLoggingMiddleware.
  lifespan(): DB pool + Redis init/teardown.
  configure_logging() at startup.
  Register devtrack-sdk:
    Fetch https://github.com/pkaranje/devtrack-sdk README first.
    Confirm exact import and init signature before writing.
```

**Verify:**
- [ ] `cd services/api && uv run python -c "from api.main import app; print('OK')"`
- [ ] ProgressStage + JobStatus values match CLAUDE.md exactly

---

### Step 8 — API Dockerfile and smoke test
**Model: `claude-haiku-4-5`**

```
Create services/api/Dockerfile.
IMPORTANT: Build context is repo root — paths are relative to repo root.

FROM python:3.12-slim
WORKDIR /build
RUN pip install uv
COPY libs/shared ./libs/shared/
RUN uv pip install ./libs/shared/
COPY services/api/pyproject.toml ./services/api/
WORKDIR /build/services/api
RUN uv sync --no-dev
COPY services/api/ ./services/api/
CMD ["uv", "run", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]

Update docker-compose.yml — add three services:

postgres:
  image: postgres:16-alpine
  volumes: [postgres_data:/var/lib/postgresql/data]
  env_file: .env.docker
  environment:
    POSTGRES_DB: videosumm
    POSTGRES_USER: postgres
    POSTGRES_PASSWORD: postgres
  healthcheck:
    test: ["CMD","pg_isready","-U","postgres"]
    interval: 5s
    retries: 5

redis:
  image: redis:7-alpine
  volumes: [redis_data:/data]
  healthcheck:
    test: ["CMD","redis-cli","ping"]
    interval: 5s
    retries: 5

api:
  build:
    context: .
    dockerfile: services/api/Dockerfile
  ports: ["8000:8000"]
  env_file: .env.docker
  volumes: [app_data:/data]
  depends_on:
    postgres: {condition: service_healthy}
    redis: {condition: service_healthy}

Run:
  make up-api
  curl http://localhost:8000/healthz
Report the response.
```

**Verify:**
- [ ] `make up-api` — 3 services healthy
- [ ] `GET /healthz` → `{"status":"ok"}`
- [ ] `POST /api/videos` with MP4 → `202` + `job_id`
- [ ] `GET /api/videos/{job_id}/status` → `{"status":"queued"}`

---

### Step 9 — Unit tests for API domain
**Model: `claude-sonnet-4-6`**

```
Create tests/ at repo root.

tests/__init__.py  (empty)

tests/unit/__init__.py  (empty)

tests/unit/test_domain_video.py
  validate_upload happy path: valid MP4, valid size
  validate_upload raises UnsupportedFormatError: content_type != video/mp4
  validate_upload raises UploadTooLargeError: size > MAX_FILE_SIZE_MB * 1024 * 1024
  validate_upload boundary: exactly at size limit passes

tests/unit/test_domain_frame.py
  validate_frame_metadata happy path: all required keys present
  raises FrameValidationError for each missing required key individually

tests/unit/test_domain_summary.py
  validate_timeline happy path: valid [{timestamp, event}]
  raises MalformedAggregationError: missing timestamp
  raises MalformedAggregationError: missing event
  raises MalformedAggregationError: empty list still passes (valid)
  validate_aggregation_json: valid JSON with summary + timeline
  validate_aggregation_json: markdown fences stripped before parsing
  validate_aggregation_json: missing fields raise MalformedAggregationError

Rules: no mocks, no DB — domain is pure functions. All tests must pass.

Run: cd services/api && make test-unit
Report pass/fail count.
```

**Verify:**
- [ ] `make test-unit` all green
- [ ] No mocks or DB connections in unit tests

---

## Phase 2 — Frontend

---

### Step 10 — Frontend scaffold and types
**Model: `claude-sonnet-4-6`**

```
Read CLAUDE.md — frontend section, API endpoints.
make up-api must be running.

1. Run: npx create-next-app@latest frontend
   App Router: yes, TypeScript: yes, Tailwind: yes,
   src/ directory: yes, import alias @/*: yes.

2. frontend/next.config.ts
   output: 'standalone'
   No rewrites — proxy is a Route Handler not a rewrite rule.

3. frontend/tsconfig.json
   strict: true
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
Report results.
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
  formatBytes(bytes: number): string
    returns "1.2 MB" format

frontend/src/lib/utils/validation.ts
  validateFileType(file): { valid: boolean; message?: string }
    valid only if file.type === 'video/mp4'
  validateFileSize(file): { valid: boolean; message?: string }
    valid only if file.size <= MAX_FILE_SIZE_BYTES
  Must match backend constraints exactly.

frontend/src/lib/hooks/useJobPoller.ts
  useJobPoller(jobId: string, initialStatus: StatusResponse)
  setInterval at POLL_INTERVAL_MS while status queued|running.
  Clears interval on completed, failed, or unmount.
  Returns: { status, error, isLoading }

frontend/src/lib/hooks/useUpload.ts
  State machine: idle → uploading → polling → done | error
  Must use XMLHttpRequest not fetch (needed for progress events).
  upload(file): validate type + size, XHR POST to /api/proxy/videos
  Tracks progress percentage.
  On 202: extract job_id, transition to polling.
  Returns: { state, jobId, uploadProgress, upload, error }

Run: cd frontend && make typecheck
```

**Verify:**
- [ ] `make typecheck` zero errors
- [ ] `useUpload` uses XHR not fetch

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
    stage → colour Badge:
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
  components/summary/SummaryCard.tsx
    Shows summary text, word_count, generated_at formatted.
  components/summary/TimelineList.tsx
    Maps timeline[] → vertical list.
    Left: formatTimestamp(event.timestamp) in Badge.
    Right: event.event string.

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

src/app/layout.tsx  (Server)
  RootLayout: html + body, Inter via next/font/google, import globals.css.
  No data fetching.

src/app/page.tsx  (Server)
  Hero heading + <UploadCard />. No data fetching.

src/app/jobs/[jobId]/loading.tsx
  Skeleton placeholders matching job page layout.

src/app/jobs/[jobId]/error.tsx  ('use client')
  Error boundary with friendly message + retry button.
  Receives error and reset from Next.js.

src/app/jobs/[jobId]/page.tsx  (Server Component)
  Receives params: { jobId: string }
  Fetch initial status using BACKEND_URL directly (not the proxy).
  This prevents a loading flash on first render.
  Pass initialStatus to <JobStatusClient>.
  Wrap in <Suspense fallback={<loading />}.

src/app/api/proxy/[...path]/route.ts
  Catch-all Route Handler.
  Read BACKEND_URL from process.env only — never NEXT_PUBLIC_*.
  Forward: method, body, all relevant headers.
  Handle multipart/form-data passthrough correctly.
  Preserve response status codes.

Run: cd frontend && make typecheck && make build
```

**Verify:**
- [ ] `make typecheck` zero errors
- [ ] `make build` succeeds

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

Update docker-compose.yml — add:
frontend:
  build:
    context: ./frontend
  ports: ["3000:3000"]
  environment:
    NEXT_PUBLIC_API_URL: /api/proxy
    BACKEND_URL: http://api:8000
  depends_on: [api]

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

Create:

services/extractor/pyproject.toml
  [project]
  name = "extractor"
  version = "0.1.0"
  requires-python = ">=3.12"
  dependencies = [
    "dramatiq[redis]>=1.16", "dramatiq-crontab>=1.0", "asyncpg>=0.29",
    "pydantic-settings>=2.0", "structlog>=24.0", "loguru>=0.7",
    "shared @ { path = '../../libs/shared', develop = true }",
  ]
  dev-dependencies = ["ruff>=0.4"]
  [tool.hatch.build.targets.wheel]
  packages = ["extractor"]

services/extractor/.gitignore  (same as api)

services/extractor/Makefile
  install (uv sync), lint, lint-fix,
  shell (exec ffmpeg-extractor), logs (tail ffmpeg-extractor),
  clean, clean-all, help

services/extractor/extractor/__init__.py  (empty)

services/extractor/extractor/core/__init__.py  (empty)
services/extractor/extractor/core/config.py
  Settings: SCENE_THRESHOLD=0.35, FRAME_INTERVAL=150, BATCH_SIZE=5,
  DATA_ROOT="/data", FFMPEG_BIN="ffmpeg", FFPROBE_BIN="ffprobe",
  MAX_DURATION_SEC=600, DATABASE_URL, REDIS_URL

services/extractor/extractor/core/logging.py
  Same pattern as api: configure_logging(), LoggerMixin, log_call.

services/extractor/extractor/domain/__init__.py  (empty)
services/extractor/extractor/domain/video.py
  VideoMeta dataclass: duration_seconds, fps, width, height, codec, total_frames
  DurationExceededError(ValueError)

services/extractor/extractor/domain/frame.py
  SelectionReason enum: scene_change, periodic, both
  FrameMetadata dataclass: video_id, frame_id (str), frame_path,
    timestamp (float), frame_number (int), selection_reason,
    scene_score (float | None), created_at
  FrameExtractionError

Run: cd services/extractor && make install
Confirm no services/extractor/extractor/extractor/ exists.
```

**Verify:**
- [ ] No `services/extractor/extractor/extractor/`
- [ ] `make install` succeeds
- [ ] `cd services/extractor && uv run python -c "from extractor.core.config import get_settings; print('OK')"`

---

### Step 16 — Extractor repositories
**Model: `claude-haiku-4-5`**

```
Working in services/extractor/. Continue from Step 15.
No business logic in repositories. All inherit LoggerMixin.

services/extractor/extractor/repositories/__init__.py
  BaseRepository(LoggerMixin)

services/extractor/extractor/repositories/ffprobe_client.py
  Same logic as api — ffprobe subprocess → VideoMeta.
  FFprobeError on failure.

services/extractor/extractor/repositories/ffmpeg_runner.py
  FFmpegRunner.run(video_path, output_dir, scene_threshold, frame_interval) -> (int, str)
  Command:
    ffmpeg -i {video_path}
      -vf "select='gt(scene,{scene_threshold})+not(mod(n,{frame_interval}))'"
      -vsync vfr -q:v 4 {output_dir}/frame_%04d.jpg
  asyncio.create_subprocess_exec.
  Returns (exit_code, stderr_text).

services/extractor/extractor/repositories/frame_repo.py
  FrameRepository(BaseRepository)
  bulk_insert_frames(frames: list[FrameMetadata]) -> list[str]
  asyncpg executemany(). Returns inserted IDs.

services/extractor/extractor/repositories/job_repo.py
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

services/extractor/extractor/services/__init__.py  BaseService(LoggerMixin)

services/extractor/extractor/services/probe.py
  ProbeService.run(video_path) -> VideoMeta
  Calls FFprobeClient. Raises DurationExceededError if > MAX_DURATION_SEC.

services/extractor/extractor/services/extraction.py
  ExtractionService.run(video_path, output_dir, video_meta) -> list[tuple[int, str]]
  Creates {DATA_ROOT}/frames/{job_id}/ if not exists.
  Calls FFmpegRunner.run(). Scans dir for frame_*.jpg.
  Returns sorted (frame_number, file_path) tuples.

services/extractor/extractor/services/metadata.py
  MetadataService.resolve(raw_frames, video_meta, video_id) -> list[FrameMetadata]
  timestamp = frame_number / fps
  selection_reason: periodic if frame_number % FRAME_INTERVAL == 0,
    scene_change otherwise, both if both conditions true
  scene_score: None (MVP)
  frame_id: new UUID str

services/extractor/extractor/services/batcher.py
  BatcherService.partition(frames) -> list[list[FrameMetadata]]
  BATCH_SIZE chunks. Last chunk included even if smaller.

services/extractor/extractor/pipeline/__init__.py  (empty)
services/extractor/extractor/pipeline/orchestrator.py
  ExtractionOrchestrator.run(job_id: str) -> None
  a. update_status(running, stage=frame_extraction)
  b. probe.run(video_path) → VideoMeta
  c. extraction.run() → raw_frames
  d. metadata.resolve() → frames
  e. frame_repo.bulk_insert_frames() → frame_ids
  f. batcher.partition() → batches
  g. for each batch: publisher.enqueue_analysis_batch(job_id, batch_frame_ids)
  h. update_status(stage=ai_analysis)
  Partial failure: if FFmpeg non-zero but frames exist → continue, log warning.

services/extractor/extractor/queue/__init__.py  (empty)
services/extractor/extractor/queue/consumer.py
  from extractor.core.logging import configure_logging
  from shared.messages import ExtractionMessage
  from shared.middleware import ActorMetricsMiddleware
  @dramatiq.actor(queue_name='extraction', max_retries=3)
  def extraction_task(job_id: str) -> None:
    ExtractionOrchestrator(...).run(job_id)
    On exception: job_repo.update_status(failed, error_message=str(e))

services/extractor/extractor/queue/publisher.py
  from shared.messages import AnalysisBatchMessage
  def enqueue_analysis_batch(job_id, frame_ids):
    msg = AnalysisBatchMessage(job_id=job_id, frame_ids=frame_ids)
    analysis_batch_task.send(msg.job_id, msg.frame_ids)

services/extractor/extractor/main.py
  from extractor.queue import consumer  # actor registration
  from extractor.core.logging import configure_logging
  from shared.middleware import ActorMetricsMiddleware
  configure_logging()
  broker = dramatiq.get_broker()
  broker.add_middleware(ActorMetricsMiddleware())
  Init DB pool and Redis at module scope.
```

**Verify:**
- [ ] All files import without error
- [ ] Pipeline step order matches CLAUDE.md

---

### Step 18 — Wire API publisher to Redis + Extractor Dockerfile
**Model: `claude-haiku-4-5`**

```
Two changes:

1. Update services/api/api/queue/publisher.py
   Replace the stub with real Dramatiq send.
   Keep ExtractionMessage import and log line.
   Use dramatiq broker to enqueue to 'extraction' queue.
   Do NOT import extractor code.

2. Create services/extractor/Dockerfile
   Build context is repo root — paths relative to repo root.

   FROM python:3.12-slim
   RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*
   WORKDIR /build
   RUN pip install uv
   COPY libs/shared ./libs/shared/
   RUN uv pip install ./libs/shared/
   COPY services/extractor/pyproject.toml ./services/extractor/
   WORKDIR /build/services/extractor
   RUN uv sync --no-dev
   COPY services/extractor/ ./services/extractor/
   CMD ["uv", "run", "dramatiq", "extractor.main", "--processes", "1", "--threads", "4"]

3. Update docker-compose.yml — add:
   ffmpeg-extractor:
     build:
       context: .
       dockerfile: services/extractor/Dockerfile
     env_file: .env.docker
     volumes: [app_data:/data]
     depends_on:
       postgres: {condition: service_healthy}
       redis: {condition: service_healthy}

Run: make up-extractor
Upload a test video via the frontend.
Report: extractor logs, file count in /data/frames/{job_id}/, job stage.
```

**Verify:**
- [ ] Frames appear in `/data/frames/{job_id}/`
- [ ] `frames` table has rows with timestamps
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

Create:

services/worker/pyproject.toml
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
  dev-dependencies = ["ruff>=0.4"]
  [tool.hatch.build.targets.wheel]
  packages = ["worker"]

services/worker/.gitignore  (same as api)

services/worker/Makefile
  install (uv sync), lint, lint-fix,
  shell (worker-1), shell-1 through shell-4,
  logs (worker-1..4 + scheduler),
  trigger-cleanup (exec cleanup_task once in worker-1),
  clean, clean-all, help

services/worker/worker/__init__.py  (empty)
services/worker/worker/core/__init__.py  (empty)
services/worker/worker/core/config.py
  AI_MODEL="gpt-4o", AI_BASE_URL="", AGGREGATION_MODEL="gpt-4o",
  MAX_RETRIES=3, MIN_BACKOFF_SEC=15, MAX_BACKOFF_SEC=120,
  JOB_TTL_DAYS=7, FAILED_JOB_TTL_DAYS=1, CLEANUP_CRON="0 2 * * *",
  DATA_ROOT="/data", DATABASE_URL, REDIS_URL, BATCH_SIZE=5

services/worker/worker/core/logging.py  (same pattern as api)

services/worker/worker/domain/__init__.py  (empty)
services/worker/worker/domain/analysis.py
  FrameAnalysisResult dataclass: frame_id, description, model_used,
    raw_response (dict), created_at
  EmptyDescriptionError
  validate_analysis(result) -> None  raises if description empty/whitespace

services/worker/worker/domain/summary.py
  TimelineEvent dataclass: timestamp (float), event (str)
  AggregationResult dataclass: summary (str), timeline (list[TimelineEvent])
  MalformedAggregationError with raw_text: str field
  validate_aggregation_json(raw: str) -> AggregationResult
    strip markdown fences → json.loads() → validate schema
    raise MalformedAggregationError on any failure

services/worker/worker/domain/cleanup.py
  CleanupTarget dataclass: job_id, upload_path, frames_dir

Run: cd services/worker && make install
Confirm no services/worker/worker/worker/ exists.
```

**Verify:**
- [ ] No `services/worker/worker/worker/`
- [ ] `make install` succeeds
- [ ] `cd services/worker && uv run python -c "from worker.core.config import get_settings; print('OK')"`

---

### Step 20 — Worker repositories
**Model: `claude-sonnet-4-6`**

```
Working in services/worker/. Continue from Step 19.
No business logic. All inherit LoggerMixin.

services/worker/worker/repositories/__init__.py  BaseRepository(LoggerMixin)

services/worker/worker/repositories/ai_client.py
  AIProvider Protocol: analyze_frames() -> list[str], complete() -> str
  AIClient(AIProvider): AsyncOpenAI with base_url override from config.
  Exponential back-off: MAX_RETRIES, MIN_BACKOFF_SEC, MAX_BACKOFF_SEC.

services/worker/worker/repositories/frame_repo.py
  get_frames_by_ids(frame_ids) -> list[dict]  returns frame_id, frame_path
  get_all_descriptions_for_job(job_id) -> list[dict]
    JOIN frames + frame_analysis ORDER BY timestamp ASC
    returns [{timestamp, description}]

services/worker/worker/repositories/analysis_repo.py
  bulk_insert_analysis(results: list[FrameAnalysisResult]) -> None
    asyncpg executemany() into frame_analysis
  nullify_raw_responses(job_id) -> None
    UPDATE frame_analysis SET ai_response = NULL
    WHERE frame_id IN (SELECT id FROM frames WHERE video_id = job_id)

services/worker/worker/repositories/summary_repo.py
  upsert_summary(video_id, result, is_partial, model_used) -> None
    INSERT ... ON CONFLICT (video_id) DO UPDATE
    generated_at = NOW()

services/worker/worker/repositories/storage_repo.py
  delete_upload(job_id): Path(DATA_ROOT/uploads/{job_id}.mp4).unlink(missing_ok=True)
  delete_frames(job_id): shutil.rmtree(DATA_ROOT/frames/{job_id}, ignore_errors=True)

services/worker/worker/repositories/job_repo.py
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

services/worker/worker/services/__init__.py  BaseService(LoggerMixin)

services/worker/worker/services/vision.py
  VisionService.analyze(frame_ids, job_id) -> list[FrameAnalysisResult]
  Read JPEG bytes → base64.b64encode() in memory only — never stored.
  Single OpenAI call with all frames as image_url content blocks.
  Parse response into FrameAnalysisResult per frame.
  validate_analysis() each result. Discard base64 after response.

services/worker/worker/services/aggregator.py
  AggregatorService.aggregate(job_id) -> AggregationResult
  get_all_descriptions_for_job() → format "[T=25.2s] description" per frame.
  Prepend system prompt from CLAUDE.md FR-5 aggregation template.
  AIClient.complete() → validate_aggregation_json()

services/worker/worker/services/completion.py
  CompletionChecker.check(job_id) -> None
  get_pending_batch_count(). If 0:
    Redis SET agg_lock:{job_id} 1 NX EX 60
    If acquired: enqueue aggregation_task.
    If not: another worker already triggered — do nothing.

services/worker/worker/services/cleanup.py
  CleanupService.clean(job) -> None
  Exact order: delete_upload → delete_frames
    → nullify_raw_responses → mark_cleaned
  Log each step with job_id.
```

**Verify:**
- [ ] base64 encoding is only in-memory in `vision.py`
- [ ] Redis `SET NX EX 60` used in `completion.py`

---

### Step 22 — Worker pipelines, queue, scheduler, main
**Model: `claude-sonnet-4-6`**

```
Read CLAUDE.md — retry policy, cleanup retention.
Working in services/worker/. Continue from Step 21.

services/worker/worker/pipeline/__init__.py  (empty)

services/worker/worker/pipeline/batch_orchestrator.py
  BatchOrchestrator.run(job_id, frame_ids) -> None
  a. update stage=ai_analysis only on first batch
     (check current stage before updating)
  b. VisionService.analyze() → results
  c. validate_analysis() each result
  d. analysis_repo.bulk_insert_analysis()
  e. progress_pct = analysed_frames / total_frames * 100
  f. job_repo.update_progress()
  g. CompletionChecker.check()
  On exception: update_status(failed, error_message=str(e))

services/worker/worker/pipeline/agg_orchestrator.py
  AggOrchestrator.run(job_id) -> None
  a. update_status(stage=aggregation)
  b. AggregatorService.aggregate() → AggregationResult
  c. summary_repo.upsert_summary()
  d. mark_completed()  sets completed_at + expires_at=NOW()+JOB_TTL_DAYS
  On exception: mark_failed(stage=aggregation)
    expires_at=NOW()+FAILED_JOB_TTL_DAYS

services/worker/worker/pipeline/cleanup_orchestrator.py
  CleanupOrchestrator.run() -> None
  get_expired_jobs() → for each:
    skip if not is_analysis_complete()
    CleanupService.clean()
  Log total count of cleaned jobs.

services/worker/worker/queue/__init__.py  (empty)
services/worker/worker/queue/consumer.py
  from shared.messages import AnalysisBatchMessage, AggregationMessage
  from shared.middleware import ActorMetricsMiddleware
  from worker.pipeline.batch_orchestrator import BatchOrchestrator
  from worker.pipeline.agg_orchestrator import AggOrchestrator
  from worker.pipeline.cleanup_orchestrator import CleanupOrchestrator

  @dramatiq.actor(queue_name='analysis', max_retries=3)
  def analysis_batch_task(job_id: str, frame_ids: list[str]) -> None:
    BatchOrchestrator(...).run(job_id, frame_ids)

  @dramatiq.actor(queue_name='aggregation', max_retries=1)
  def aggregation_task(job_id: str) -> None:
    AggOrchestrator(...).run(job_id)

  @dramatiq.actor(queue_name='cleanup', max_retries=3)
  def cleanup_task() -> None:
    CleanupOrchestrator(...).run()

services/worker/worker/scheduler.py
  from dramatiq_crontab import crontab
  from worker.queue.consumer import cleanup_task
  from worker.core.config import get_settings

  @crontab(get_settings().CLEANUP_CRON)
  def schedule_cleanup():
      cleanup_task.send()

  Nothing else in this file.

services/worker/worker/main.py
  from worker.queue import consumer
  from worker.core.logging import configure_logging
  from shared.middleware import ActorMetricsMiddleware
  configure_logging()
  broker = dramatiq.get_broker()
  broker.add_middleware(ActorMetricsMiddleware())
  Init DB pool and Redis at module scope.
```

**Verify:**
- [ ] All imports resolve correctly
- [ ] `scheduler.py` has only the `@crontab` declaration

---

### Step 23 — Worker Dockerfile and end-to-end test
**Model: `claude-haiku-4-5`**

```
Create services/worker/Dockerfile.
Build context is repo root — paths relative to repo root.

FROM python:3.12-slim
WORKDIR /build
RUN pip install uv
COPY libs/shared ./libs/shared/
RUN uv pip install ./libs/shared/
COPY services/worker/pyproject.toml ./services/worker/
WORKDIR /build/services/worker
RUN uv sync --no-dev
COPY services/worker/ ./services/worker/
CMD ["uv", "run", "dramatiq", "worker.main", "--processes", "1", "--threads", "3"]

Update docker-compose.yml — add:

worker-1: &worker
  build:
    context: .
    dockerfile: services/worker/Dockerfile
  env_file: .env.docker
  volumes: [app_data:/data]
  depends_on:
    postgres: {condition: service_healthy}
    redis: {condition: service_healthy}
worker-2: *worker
worker-3: *worker
worker-4: *worker

scheduler:
  build:
    context: .
    dockerfile: services/worker/Dockerfile
  env_file: .env.docker
  depends_on: [redis]
  command: ["uv", "run", "python", "-m", "dramatiq_crontab", "worker.scheduler"]

Run: make up

End-to-end test:
1. Upload an MP4 via http://localhost:3000
2. Wait for status=completed
3. Confirm summary and timeline are non-empty in the UI

Cleanup test:
4. make api-shell-db
   UPDATE videos SET expires_at = NOW() - interval '1 second' WHERE id = '<job_id>';
5. make worker-trigger-cleanup
6. Confirm /data/uploads/ + /data/frames/{job_id}/ deleted
7. Confirm frame_analysis.ai_response = NULL, description intact
8. Confirm videos.cleaned_at is populated

Report result for each numbered step.
```

**Verify:**
- [ ] `make up` — all 10 services healthy
- [ ] Full pipeline: upload → `completed` with summary + timeline
- [ ] Cleanup test: all 8 steps pass

---

## Phase 5 — Quality

---

### Step 24 — Integration tests
**Model: `claude-sonnet-4-6`**

```
Read CLAUDE.md — processing pipeline.
Create integration test suite at tests/.

tests/conftest.py
  pytest-asyncio fixtures:
  test_db: async — alembic upgrade head on test DB,
    yield AsyncSession, drop after suite
  test_redis: yield Redis client
  test_client: yield httpx.AsyncClient for FastAPI app
  mock_ai_client: AIClient mock returning deterministic responses
    — no real OpenAI calls in CI

tests/fixtures/
  Generate a 5-second 720p test video:
  ffmpeg -f lavfi -i testsrc=duration=5:size=1280x720:rate=30 \
    tests/fixtures/sample.mp4

tests/integration/__init__.py  (empty)

tests/integration/test_upload_pipeline.py
  POST /api/videos with sample.mp4
  Assert: 202 response, job_id in body
  Assert: job row exists in DB with status=queued
  Assert: extraction task enqueued in Redis

tests/integration/test_extraction_pipeline.py
  Call extraction_task(job_id) directly with sample.mp4 and real FFmpeg.
  Assert: frames written to /data/frames/{job_id}/
  Assert: frame rows in DB with correct timestamps
  Assert: analysis batch tasks enqueued in Redis

tests/integration/test_analysis_pipeline.py
  Call analysis_batch_task(job_id, frame_ids) with mock_ai_client.
  Assert: frame_analysis rows inserted with description populated
  Assert: progress_pct updated on job

tests/integration/test_aggregation_pipeline.py
  Call aggregation_task(job_id) with mock_ai_client returning fixed JSON.
  Assert: video_summary row created
  Assert: job status=completed, summary and timeline non-empty

tests/integration/test_cleanup_pipeline.py
  Create completed job with expires_at in the past.
  Call cleanup_task() directly.
  Assert: upload file deleted
  Assert: frames directory deleted
  Assert: ai_response = NULL, description intact
  Assert: cleaned_at populated

Run: cd services/api && make test-integration
Report pass/fail counts.
```

**Verify:**
- [ ] `make test-integration` all green
- [ ] No real API calls — mock_ai_client used in all AI tests

---

### Step 25 — devtrack-sdk observability
**Model: `claude-sonnet-4-6`**

```
Task 1:
Fetch https://github.com/pkaranje/devtrack-sdk and read the README.
Confirm exact import path and init call signature.
Update services/api/api/main.py with confirmed devtrack registration.
Add dashboard URL as comment to .env.example.

Task 2 — pipeline log lines:
In each pipeline orchestrator add structured Loguru lines:
  Entry:   logger.info("pipeline_start", job_id=job_id, stage=<name>)
  Exit:    logger.info("pipeline_done", job_id=job_id, stage=<name>, duration_ms=<ms>)
  Failure: logger.error("pipeline_failed", job_id=job_id, stage=<name>,
             error=str(e), retry_count=<n>)

Task 3 — final local verification:
  make lint        must be zero errors
  make test        must be all green
  make up          all 10 services healthy

Upload an MP4 end-to-end and confirm completed.
Open devtrack dashboard URL and confirm metrics visible.
Report each result.
```

**Verify:**
- [ ] `make lint` zero errors
- [ ] `make test` all green
- [ ] All 10 services healthy
- [ ] devtrack dashboard shows request data

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
  Run: cd services/api && make db-migrate
  Confirm zero errors.

Then run on a clean database:
  make db-reset
  make db-migrate
Report the migration output.
```

**Verify:**
- [ ] `expires_at` and `cleaned_at` in migration
- [ ] `make db-migrate` on clean DB → zero errors

---

### Step 27 — GitHub Actions
**Model: `claude-haiku-4-5`**

```
Create two GitHub Actions workflow files.

.github/workflows/ci.yml
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
          env: {POSTGRES_DB: test, POSTGRES_PASSWORD: test}
          options: "--health-cmd pg_isready --health-interval 5s --health-retries 5"
          ports: ["5432:5432"]
        redis:
          image: redis:7-alpine
          options: "--health-cmd 'redis-cli ping' --health-interval 5s --health-retries 5"
          ports: ["6379:6379"]
      env:
        DATABASE_URL: postgresql+asyncpg://postgres:test@localhost/test
        REDIS_URL: redis://localhost:6379
      steps:
        - uses: actions/checkout@v4
        - uses: astral-sh/setup-uv@v4
        - run: cd libs/shared && uv sync
        - run: cd services/api && uv sync
        - run: cd services/api && uv run alembic upgrade head
        - run: make test

.github/workflows/build.yml
  Trigger: push → main

  jobs:
    build:
      runs-on: ubuntu-latest
      strategy:
        matrix:
          include:
            - {service: api,       dockerfile: services/api/Dockerfile}
            - {service: extractor, dockerfile: services/extractor/Dockerfile}
            - {service: worker,    dockerfile: services/worker/Dockerfile}
            - {service: frontend,  context: frontend, dockerfile: frontend/Dockerfile}
      steps:
        - uses: actions/checkout@v4
        - uses: docker/login-action@v3
          with:
            registry: ghcr.io
            username: pkaranje
            password: ${{ secrets.GHCR_TOKEN }}
        - uses: docker/build-push-action@v5
          with:
            context: ${{ matrix.context || '.' }}
            dockerfile: ${{ matrix.dockerfile }}
            push: true
            tags: ghcr.io/pkaranje/video-summarizer/${{ matrix.service }}:${{ github.sha }}
```

**Verify:**
- [ ] Both workflow files parse as valid YAML
- [ ] Open a test PR — CI workflow triggers and passes

---

### Step 28 — Final checklist
**Model: `claude-haiku-4-5`**

```
Final verification before merging to main.
Check each item and report pass or fail:

1. .gitignore: .env and .env.docker ignored, .env.example is NOT ignored
2. uv.lock committed in each: libs/shared/, services/api/,
   services/extractor/, services/worker/
3. Makefiles present: root, libs/shared/, services/api/,
   services/extractor/, services/worker/, frontend/
4. Dockerfiles present: services/api/, services/extractor/,
   services/worker/, frontend/
5. docker-compose.yml has exactly 10 services:
   postgres, redis, api, frontend, ffmpeg-extractor,
   worker-1, worker-2, worker-3, worker-4, scheduler
6. make lint → zero errors
7. make test → all green
8. make up → all 10 services healthy
9. Full upload → pipeline → summary + timeline visible in UI

Fix any failures, then open PR to main.
```

**Verify:**
- [ ] All 9 checklist items pass
- [ ] PR CI green before merge

---

## Build schedule

| Day | Steps | Goal |
|---|---|---|
| Day 1 | 1–3 | Root scaffold + libs/shared working |
| Day 2 | 4–9 | Full API backend with DB + smoke test |
| Day 3 | 10–14 | Frontend upload → queued working |
| Day 4 | 15–18 | Extractor: upload → frames extracted |
| Day 5 (Friday) | 19–23 | Worker: full pipeline end-to-end |
| Day 5 (stretch) | 24–28 | Tests + CI + final checklist |
