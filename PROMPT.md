# PROMPT.md — Execution Guide

## How to use this file

Each step is a prompt you paste directly into Claude Code.
Nothing else. No extra context needed — CLAUDE.md is already in the repo
and Claude Code reads it automatically.

**Rules:**
- Complete and verify each step before starting the next
- Use the model shown for each step
- If a step fails, fix it before continuing — do not skip ahead

## Model guide

| Phase | Model |
|---|---|
| Phase 0 — Root scaffold | `claude-haiku-4-5` |
| Phase 1 — FastAPI backend | `claude-sonnet-4-6` |
| Phase 2 — Next.js frontend | `claude-sonnet-4-6` |
| Phase 3 — FFmpeg extractor | `claude-haiku-4-5` |
| Phase 4 — Worker service | `claude-sonnet-4-6` |
| Phase 5 — Quality | `claude-sonnet-4-6` |
| Phase 6 — CI/CD | `claude-haiku-4-5` |

---

## Phase 0 — Root scaffold

> **Before anything else.** Sets up the repo skeleton all services build on.

---

### Step 0 — Root files and shared package
**Model: `claude-haiku-4-5`**

---

**Prompt:**

```
Read CLAUDE.md fully.

Create the following root-level files exactly as specified in CLAUDE.md:

1. .gitignore
   Cover: Python (__pycache__, .venv, *.pyc, .pytest_cache, .ruff_cache),
   uv.lock files are NOT ignored (commit them),
   environment files (.env, .env.docker but NOT .env.example or .env.docker.example),
   Node (node_modules/, .next/, frontend/out/),
   data volumes (data/),
   IDE (.vscode/, .idea/)

2. .env.example
   All env vars from CLAUDE.md environment variables table.
   Group by: Database, Redis, AI, Extraction, Workers, Cleanup, Frontend, Observability.
   Use placeholder values. Add a comment on each line explaining what it does.

3. .env.docker.example
   Docker-only overrides: DATABASE_URL with host=postgres, REDIS_URL with host=redis,
   DATA_ROOT=/data, BACKEND_URL=http://api:8000

4. pyproject.toml (root — tooling config only, NOT a uv workspace)
   [tool.ruff] line-length=100, target-version="py312", select E/F/I/UP/B/SIM
   [tool.pytest.ini_options] asyncio_mode="auto", testpaths=["tests"]

5. docker-compose.yml (skeleton only — services added in later steps)
   Define: volumes (postgres_data, redis_data, app_data)
   Define: networks (default, name: videosumm)
   No services yet.

6. Makefile (root)
   Delegates to service Makefiles via $(MAKE) -C <service> <target>.
   Install order: shared → app → extractor → worker → frontend.
   Targets: env-check, install, lint, lint-fix, test, test-unit, test-integration,
   build, up, up-dev, up-app, up-frontend, up-extractor, up-workers,
   down, restart, logs, db-migrate, db-rollback, db-reset, clean, clean-all.
   Wildcard delegation: shared-%, app-%, extractor-%, worker-%, frontend-%
   make help must print all targets with descriptions.

7. shared/pyproject.toml
   name="shared", requires-python=">=3.12"
   dependencies: loguru>=0.7, dramatiq>=1.16
   build-system: hatchling

8. shared/Makefile
   Targets: install (uv sync), lint, lint-fix, clean, clean-all, help
   help must print import boundary rules:
     app/queue/publisher.py → messages.py only
     extractor/ → messages.py + middleware.py
     worker/ → messages.py + middleware.py
     frontend/ → nothing

9. shared/shared/__init__.py (empty)

10. shared/shared/middleware.py
    ActorMetricsMiddleware class as defined in CLAUDE.md observability section.
    Imports: time, dramatiq, loguru logger
    before_process_message: stores started_at in message.options
    after_process_message: emits structured log with actor, queue, duration_ms,
    status (success/failed), job_id (from message.kwargs), retries

11. shared/shared/messages.py
    Three dataclasses as defined in CLAUDE.md messages section:
    ExtractionMessage(job_id: str)
    AnalysisBatchMessage(job_id: str, frame_ids: list[str])
    AggregationMessage(job_id: str)
    stdlib dataclasses only — no external imports.

After creating all files run:
  make env-check
  cd shared && make install
  make lint
Report any errors.
```

---

**Verify before Step 1:**
- [ ] `.env` is gitignored, `.env.example` is not
- [ ] `make help` prints all targets
- [ ] `cd shared && make install` succeeds
- [ ] `make lint` runs without error (may have no Python files yet — that is fine)

---

## Phase 1 — FastAPI Backend

> **Goal:** Working HTTP API with PostgreSQL. Queue publisher is a stub.

---

### Step 1 — App scaffold and config
**Model: `claude-haiku-4-5`**

---

**Prompt:**

```
Read CLAUDE.md.

Create the FastAPI backend scaffold at app/:

1. app/__init__.py (empty)

2. app/pyproject.toml
   name="app", requires-python=">=3.12"
   dependencies:
     fastapi>=0.115, uvicorn[standard]>=0.30, pydantic-settings>=2.0,
     sqlalchemy[asyncio]>=2.0, asyncpg>=0.29, alembic>=1.13,
     redis>=5.0, dramatiq[redis]>=1.16, structlog>=24.0, loguru>=0.7,
     python-multipart>=0.0.9, devtrack-sdk, shared @ ../shared
   dev-dependencies: pytest>=8.0, pytest-asyncio>=0.23, httpx>=0.27, ruff>=0.4

3. app/Makefile
   Targets: install (uv pip install -e ../shared then uv sync), lint, lint-fix,
   test, test-unit, test-integration,
   db-migrate (alembic upgrade head), db-rollback (alembic downgrade -1), db-reset,
   shell (exec into api container), shell-db (psql), shell-redis (redis-cli),
   clean, clean-all, help

4. app/.gitignore
   Cover: __pycache__, *.py[cod], .venv/, .pytest_cache/, .ruff_cache/

5. app/core/__init__.py (empty)

6. app/core/config.py
   pydantic-settings Settings class with @lru_cache.
   Include every env var from CLAUDE.md that belongs to the FastAPI service.
   Sensible defaults for all except DATABASE_URL, REDIS_URL, OPENAI_API_KEY.

7. app/core/logging.py
   configure_logging(): structlog with JSON renderer.
   LoggerMixin: gives self.logger to any class that inherits it.
   log_call decorator: logs function name, entry, exit, elapsed ms.

Run: cd app && make install
Report success or any errors.
```

---

**Verify before Step 2:**
- [ ] `cd app && make install` succeeds
- [ ] `python -c "from app.core.config import get_settings; print(get_settings())"` works

---

### Step 2 — Domain layer
**Model: `claude-sonnet-4-6`**

---

**Prompt:**

```
Read CLAUDE.md domain rules.

Create the domain layer for the FastAPI backend. Zero imports outside stdlib in any domain file.

1. app/domain/__init__.py
   Re-export all validators, exceptions, enums.

2. app/domain/video.py
   VideoStatus enum: queued, running, completed, failed
   UploadTooLargeError, UnsupportedFormatError (both inherit ValueError)
   validate_upload(filename: str, content_type: str, size_bytes: int) -> None
     raises UnsupportedFormatError if content_type != "video/mp4"
     raises UploadTooLargeError if size_bytes > MAX_FILE_SIZE_MB * 1024 * 1024
   Constants: MAX_FILE_SIZE_MB, MAX_DURATION_SEC

3. app/domain/frame.py
   SelectionReason enum: scene_change, periodic, both
   FrameValidationError
   validate_frame_metadata(metadata: dict) -> None
     asserts required keys present: video_id, frame_id, frame_path,
     timestamp, frame_number, selection_reason

4. app/domain/summary.py
   MalformedAggregationError
   AggregationResult dataclass: summary (str), timeline (list[dict])
   validate_timeline(timeline: list) -> None
     each item must have timestamp (float) and event (str)
     raises MalformedAggregationError if not

Write pytest unit tests in tests/unit/ for every validator.
Cover: happy path, every error path, edge cases (empty string, zero bytes, etc).
No mocks, no DB — domain is pure functions.
```

---

**Verify before Step 3:**
- [ ] `cd app && make test-unit` passes
- [ ] No imports outside stdlib in any domain file

---

### Step 3 — Database models and migrations
**Model: `claude-sonnet-4-6`**

---

**Prompt:**

```
Read CLAUDE.md database schema section.

Create async SQLAlchemy models and the initial Alembic migration:

1. app/db/__init__.py (empty)

2. app/db/models.py
   Async SQLAlchemy Base with all four tables.
   videos: every column from CLAUDE.md including expires_at and cleaned_at.
   frames: every column including created_at.
   frame_analysis: id, frame_id FK, ai_response JSONB, description TEXT,
                   model_used TEXT, created_at.
   video_summary: id, video_id FK UNIQUE, summary TEXT, timeline JSONB,
                  is_partial BOOL DEFAULT FALSE, model_used TEXT, generated_at.
   Use UUID primary keys. All timestamps are TIMESTAMPTZ.

3. alembic.ini (standard alembic config pointing to app/db)

4. alembic/env.py
   Async-compatible env.py using asyncio + asyncpg.
   Import Base from app.db.models.

5. alembic/versions/0001_initial.py
   Creates all four tables with every column.
   expires_at and cleaned_at must be in this migration — not a follow-up.

Then run: cd app && make db-migrate
Report the output. If it errors, fix and retry.
```

---

**Verify before Step 4:**
- [ ] `make db-migrate` output shows 0001_initial complete
- [ ] All four tables exist with correct columns

---

### Step 4 — Repositories
**Model: `claude-sonnet-4-6`**

---

**Prompt:**

```
Read CLAUDE.md repository layer rules. No business logic in repositories.
All repositories inherit LoggerMixin.

Create:

1. app/repositories/__init__.py
   BaseRepository(LoggerMixin) — base class, holds db session reference.

2. app/repositories/job_repo.py
   JobRepository methods:
   - create(filename, file_size_bytes, duration_seconds, resolution, fps) -> Job
     sets status=queued, stage=upload_validation
   - get_by_id(job_id) -> Job | None
   - update_status(job_id, status, stage, error_message=None) -> None
     single atomic UPDATE for status + stage + error_message
   - update_progress(job_id, progress_pct) -> None
   - mark_completed(job_id) -> None
     sets status=completed, stage=completed, progress_pct=100,
     completed_at=NOW(), expires_at=NOW()+JOB_TTL_DAYS
   - mark_failed(job_id, stage, error_message, ttl_days) -> None
     sets status=failed, expires_at=NOW()+ttl_days
   - get_expired_jobs() -> list[Job]
     WHERE expires_at < NOW() AND cleaned_at IS NULL
     AND status IN (completed, failed)
   - is_analysis_complete(job_id) -> bool
     COUNT(frame_analysis) == COUNT(frames) for this job_id
   - mark_cleaned(job_id) -> None

3. app/repositories/frame_repo.py
   FrameRepository methods:
   - bulk_insert_frames(frames: list[dict]) -> list[str]  (returns inserted IDs)
   - get_frames_for_job(job_id) -> list[Frame]
   - get_descriptions_for_job(job_id) -> list[dict]
     JOIN frames + frame_analysis ORDER BY timestamp ASC
     returns [{timestamp, description}]

4. app/repositories/ffprobe_client.py
   FFprobeClient.probe(video_path: str) -> FFprobeResult
   FFprobeResult dataclass: duration_seconds, fps, width, height, codec
   Run: ffprobe -v quiet -print_format json -show_format -show_streams
   Raise FFprobeError on non-zero exit or JSON parse failure.
   Use asyncio.create_subprocess_exec.
```

---

**Verify before Step 5:**
- [ ] All classes import without error
- [ ] No business logic — only DB queries and subprocess calls

---

### Step 5 — Services
**Model: `claude-sonnet-4-6`**

---

**Prompt:**

```
Read CLAUDE.md service layer rules. Services orchestrate — they do not contain SQL.

Create:

1. app/services/__init__.py
   BaseService(LoggerMixin)

2. app/services/upload.py
   UploadService.upload(file: UploadFile) -> UploadResponse
   Exact order:
     a. validate_upload() from domain — raise on bad MIME or size
     b. Write file to {DATA_ROOT}/uploads/{job_id}.mp4
     c. FFprobeClient.probe() — raise if duration > MAX_DURATION_SEC
     d. job_repo.create() with ffprobe metadata
     e. publisher.enqueue_extraction(job_id)
     f. Return UploadResponse(job_id=job_id, status="queued")

3. app/services/status.py
   StatusService.get(job_id: str) -> StatusResponse
   Fetch job row. Raise HTTPException 404 if not found.
   Map all DB fields to StatusResponse including stage, progress_pct, error_message.

4. app/services/summary.py
   SummaryService.get_summary(job_id) -> SummaryResponse
   SummaryService.get_timeline(job_id) -> TimelineResponse
   Both raise HTTPException 404 if job not completed or summary not found.
```

---

**Verify before Step 6:**
- [ ] All services import without error
- [ ] No raw SQL in any service file

---

### Step 6 — Queue publisher stub
**Model: `claude-haiku-4-5`**

---

**Prompt:**

```
Create app/queue/__init__.py (empty) and app/queue/publisher.py.

publisher.py must:
- Import ExtractionMessage from shared.messages
- Define RedisPublisher class inheriting LoggerMixin
- Implement enqueue_extraction(self, job_id: str) -> None:
    msg = ExtractionMessage(job_id=job_id)
    self.logger.info("extraction_enqueued", job_id=msg.job_id)
    # TODO: replace with real Dramatiq send in Step 25
    pass

The interface must be identical to what the real implementation will use.
No service code changes in Step 25 — only this file changes.
```

---

**Verify before Step 7:**
- [ ] `from app.queue.publisher import RedisPublisher` works
- [ ] `from shared.messages import ExtractionMessage` works

---

### Step 7 — API schemas
**Model: `claude-haiku-4-5`**

---

**Prompt:**

```
Read CLAUDE.md API endpoints section.

Create Pydantic response schemas:

1. app/api/__init__.py (empty)
2. app/api/schemas/__init__.py (empty)

3. app/api/schemas/common.py
   ErrorDetail(message: str, code: str)
   HealthResponse(status: str)

4. app/api/schemas/video.py
   ProgressStage: Literal enum with values:
     upload_validation, frame_extraction, ai_analysis, aggregation, completed
   JobStatus: Literal enum with values:
     queued, running, completed, failed
   UploadResponse(job_id: str, status: str)
   StatusResponse(job_id: str, status: JobStatus, stage: ProgressStage | None,
     progress_pct: int, error_message: str | None,
     created_at: datetime, updated_at: datetime)

5. app/api/schemas/summary.py
   TimelineEvent(timestamp: float, event: str)
   SummaryResponse(job_id: str, summary: str, word_count: int, generated_at: datetime)
   TimelineResponse(job_id: str, timeline: list[TimelineEvent])
```

---

**Verify before Step 8:**
- [ ] All schemas import without error
- [ ] ProgressStage and JobStatus values match CLAUDE.md exactly

---

### Step 8 — Routes, middleware, app factory
**Model: `claude-sonnet-4-6`**

---

**Prompt:**

```
Read CLAUDE.md API endpoints and observability sections.

Create the full FastAPI application:

1. app/core/dependencies.py
   Async dependency factories using FastAPI Depends():
   get_db() -> AsyncSession
   get_redis() -> Redis
   get_job_repo() -> JobRepository
   get_frame_repo() -> FrameRepository
   get_upload_service() -> UploadService
   get_status_service() -> StatusService
   get_summary_service() -> SummaryService

2. app/core/middleware.py
   RequestLoggingMiddleware:
   - Generate UUID request_id for each request
   - Bind request_id to structlog context
   - Log: method, path, status_code, duration_ms on every response

3. app/api/routes/__init__.py (empty)

4. app/api/routes/health.py
   GET /healthz -> HealthResponse(status="ok")

5. app/api/routes/videos.py
   POST /api/videos
   Accept UploadFile (field name: "file")
   Delegate to UploadService
   Return 202 UploadResponse

6. app/api/routes/status.py
   GET /api/videos/{job_id}/status -> StatusResponse

7. app/api/routes/summary.py
   GET /api/videos/{job_id}/summary -> SummaryResponse

8. app/api/routes/timeline.py
   GET /api/videos/{job_id}/timeline -> TimelineResponse

9. app/api/routes/frames.py
   GET /api/videos/{job_id}/frames -> list of frame metadata

10. app/main.py
    FastAPI app factory.
    Register all routers with /api prefix (except /healthz).
    Add RequestLoggingMiddleware.
    Call configure_logging() on startup.
    lifespan(): create DB pool and Redis connection on startup, close on shutdown.
    Register devtrack-sdk: fetch https://github.com/pkaranje/devtrack-sdk
    and read README before writing the import — confirm exact init signature.
```

---

**Verify before Step 9:**
- [ ] `cd app && uv run python -c "from app.main import app; print('OK')"` succeeds
- [ ] All routes importable without error

---

### Step 9 — Dockerfile and smoke test
**Model: `claude-haiku-4-5`**

---

**Prompt:**

```
Create app/Dockerfile:

FROM python:3.12-slim
WORKDIR /app
RUN pip install uv
COPY ../shared /shared
RUN uv pip install /shared
COPY pyproject.toml .
RUN uv sync --no-dev
COPY . .
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

Update docker-compose.yml — add these three services:

postgres:
  image: postgres:16-alpine
  volumes: [postgres_data:/var/lib/postgresql/data]
  env_file: .env.docker
  environment: {POSTGRES_DB: videosumm, POSTGRES_USER: postgres, POSTGRES_PASSWORD: postgres}
  healthcheck: {test: ["CMD","pg_isready","-U","postgres"], interval: 5s, retries: 5}

redis:
  image: redis:7-alpine
  volumes: [redis_data:/data]
  healthcheck: {test: ["CMD","redis-cli","ping"], interval: 5s, retries: 5}

api:
  build:
    context: .
    dockerfile: app/Dockerfile
  ports: ["8000:8000"]
  env_file: .env.docker
  volumes: [app_data:/data]
  depends_on: {postgres: {condition: service_healthy}, redis: {condition: service_healthy}}

Then run: make up-app

Verify:
  curl http://localhost:8000/healthz
  → should return {"status":"ok"}
Report the response.
```

---

**Verify before Phase 2:**
- [ ] `GET /healthz` returns `{"status":"ok"}`
- [ ] `POST /api/videos` with a test MP4 returns `202` with a `job_id`
- [ ] `GET /api/videos/{job_id}/status` returns `{"status":"queued"}`

---

## Phase 2 — Next.js Frontend

> **Goal:** Upload UI with live status polling. Backend must be running.

---

### Step 10 — App scaffold
**Model: `claude-haiku-4-5`**

---

**Prompt:**

```
Scaffold the Next.js frontend:

1. Run: npx create-next-app@latest frontend
   Options: App Router yes, TypeScript yes, Tailwind yes, src/ dir yes,
   import alias @/* yes.

2. Update frontend/next.config.ts:
   output: 'standalone'
   No rewrites — the proxy is a Route Handler, not a rewrite rule.

3. Update frontend/tsconfig.json:
   Enable strict mode.
   Path aliases: @/components, @/lib, @/types

4. Create frontend/.gitignore:
   .next/, out/, node_modules/,
   .env.local, .env.development.local, .env.test.local, .env.production.local

5. Create frontend/.env.local.example:
   NEXT_PUBLIC_API_URL=/api/proxy
   BACKEND_URL=http://localhost:8000

6. Create frontend/Makefile:
   Targets: install (npm ci), dev (npm run dev), build (npm run build),
   typecheck (npx tsc --noEmit), lint (npm run lint), lint-fix,
   shell (exec into frontend container), logs, clean (.next/ out/),
   clean-all (clean + node_modules/), help

Add frontend service to docker-compose.yml:
  frontend:
    build:
      context: ./frontend
    ports: ["3000:3000"]
    environment: {NEXT_PUBLIC_API_URL: /api/proxy, BACKEND_URL: http://api:8000}
    depends_on: [api]

Run: cd frontend && make install
Report success or errors.
```

---

**Verify before Step 11:**
- [ ] `cd frontend && make install` succeeds
- [ ] `make typecheck` passes

---

### Step 11 — Types, constants, API client
**Model: `claude-haiku-4-5`**

---

**Prompt:**

```
Create the API layer for the frontend. All types must mirror CLAUDE.md backend schemas exactly.

1. frontend/src/lib/constants.ts
   POLL_INTERVAL_MS = 3000
   MAX_FILE_SIZE_BYTES = 500 * 1024 * 1024
   ACCEPTED_TYPES = ['video/mp4']

2. frontend/src/lib/api/types.ts
   JobStatus: 'queued' | 'running' | 'completed' | 'failed'
   ProgressStage: 'upload_validation' | 'frame_extraction' | 'ai_analysis' | 'aggregation' | 'completed'
   UploadResponse: { job_id: string; status: string }
   StatusResponse: { job_id: string; status: JobStatus; stage: ProgressStage | null;
     progress_pct: number; error_message: string | null;
     created_at: string; updated_at: string }
   TimelineEvent: { timestamp: number; event: string }
   SummaryResponse: { job_id: string; summary: string; word_count: number; generated_at: string }
   TimelineResponse: { job_id: string; timeline: TimelineEvent[] }
   APIError: class extending Error with status: number field

3. frontend/src/lib/api/client.ts
   fetchAPI(path: string, init?: RequestInit): Promise<unknown>
   Prepends NEXT_PUBLIC_API_URL env var.
   On non-2xx: throws APIError with status code and response body.

4. frontend/src/lib/api/videos.ts
   uploadVideo(file: File): Promise<UploadResponse>
   getStatus(jobId: string): Promise<StatusResponse>
   getSummary(jobId: string): Promise<SummaryResponse>
   getTimeline(jobId: string): Promise<TimelineResponse>

5. frontend/src/types/index.ts
   Re-export everything from lib/api/types.ts
```

---

**Verify before Step 12:**
- [ ] `make typecheck` passes with no errors

---

### Step 12 — Utilities and hooks
**Model: `claude-sonnet-4-6`**

---

**Prompt:**

```
Create utility functions and React hooks:

1. frontend/src/lib/utils/format.ts
   formatTimestamp(seconds: number): string
     converts 83.5 → "1m 23s", 45.0 → "45s", 0 → "0s"
   formatBytes(bytes: number): string
     converts to KB/MB with one decimal

2. frontend/src/lib/utils/validation.ts
   validateFileType(file: File): { valid: boolean; message?: string }
     valid only if file.type === 'video/mp4'
   validateFileSize(file: File): { valid: boolean; message?: string }
     valid only if file.size <= MAX_FILE_SIZE_BYTES
   Both must match backend constraints exactly.

3. frontend/src/lib/hooks/useJobPoller.ts
   useJobPoller(jobId: string, initialStatus: StatusResponse)
   Sets up setInterval at POLL_INTERVAL_MS.
   Calls getStatus(jobId) each tick.
   Stops polling when status is 'completed' or 'failed'.
   Clears interval on component unmount.
   Returns: { status: StatusResponse; error: Error | null; isLoading: boolean }

4. frontend/src/lib/hooks/useUpload.ts
   State machine: idle → uploading → polling → done | error
   Must use XMLHttpRequest (not fetch) — required for upload progress events.
   upload(file: File): void
     validates file first (type + size)
     XHR POST to /api/proxy/videos with FormData
     tracks upload progress percentage
     on 202: extracts job_id, transitions to polling state
   Returns: { state, jobId, uploadProgress, upload, error }
```

---

**Verify before Step 13:**
- [ ] `make typecheck` passes

---

### Step 13 — UI components
**Model: `claude-sonnet-4-6`**

---

**Prompt:**

```
Create all UI components. Follow the Server/Client split from CLAUDE.md exactly.

UI primitives (all Server Components):
  frontend/src/components/ui/Badge.tsx    — variant prop maps to Tailwind colour classes
  frontend/src/components/ui/Button.tsx   — polymorphic, as prop defaults to button
  frontend/src/components/ui/Card.tsx     — shadow card wrapper
  frontend/src/components/ui/Spinner.tsx  — animated loading indicator

Upload components:
  frontend/src/components/upload/FileDropzone.tsx  — 'use client'
    Native HTML5 drag-and-drop, no library.
    Calls validateFileType() then validateFileSize() before accepting.
    Shows inline error message on failure.
    Calls onFileAccepted(file: File) prop on success.

  frontend/src/components/upload/UploadProgress.tsx — 'use client'
    Renders a progress bar from percent: number prop.

  frontend/src/components/upload/UploadCard.tsx — 'use client'
    Composes FileDropzone and UploadProgress.
    Uses useUpload() hook.
    On done state: calls router.push('/jobs/' + jobId).

Job components:
  frontend/src/components/job/StageBadge.tsx  — Server Component
    Maps ProgressStage values to colour-coded Badge pills.
    upload_validation=grey, frame_extraction=blue, ai_analysis=purple,
    aggregation=amber, completed=green

  frontend/src/components/job/ErrorBanner.tsx — Server Component
    Renders error_message in red banner. Returns null if message is null.

  frontend/src/components/job/JobStatusClient.tsx — 'use client'
    Props: jobId: string, initialStatus: StatusResponse
    Uses useJobPoller(jobId, initialStatus).
    Renders: StageBadge for current stage, progress bar from progress_pct,
    ErrorBanner if status === 'failed',
    SummaryCard + TimelineList once status === 'completed'
    (fetches summary and timeline on transition to completed).

Summary components (both Server Components):
  frontend/src/components/summary/SummaryCard.tsx
    Displays summary text, word_count, generated_at (formatted).

  frontend/src/components/summary/TimelineList.tsx
    Maps timeline[] to a vertical list.
    Each row: left = formatTimestamp(event.timestamp) in Badge,
    right = event.event string.
```

---

**Verify before Step 14:**
- [ ] `make typecheck` passes
- [ ] `make lint` passes

---

### Step 14 — Pages, layout, and proxy
**Model: `claude-sonnet-4-6`**

---

**Prompt:**

```
Create the Next.js App Router pages and the API proxy Route Handler.

1. frontend/src/app/globals.css
   Tailwind base/components/utilities directives.

2. frontend/src/app/layout.tsx  — Server Component
   RootLayout: html/body tags, load Inter font via next/font/google,
   import globals.css. Wrap children — no data fetching here.

3. frontend/src/app/page.tsx  — Server Component
   Home page. Render a hero heading and <UploadCard />.
   No data fetching.

4. frontend/src/app/jobs/[jobId]/loading.tsx
   Suspense skeleton: placeholder cards matching the job page layout.

5. frontend/src/app/jobs/[jobId]/error.tsx  — 'use client'
   Error boundary. Shows friendly error message + retry button.
   Receives error and reset props from Next.js.

6. frontend/src/app/jobs/[jobId]/page.tsx  — Server Component
   Receives params: { jobId: string }
   Fetches initial status using BACKEND_URL (not the proxy) directly.
   This avoids a loading flash on first render.
   Passes initialStatus to <JobStatusClient>.
   Wraps in Suspense with loading.tsx as fallback.

7. frontend/src/app/api/proxy/[...path]/route.ts
   Catch-all Route Handler for all API calls from client components.
   Reads BACKEND_URL from process.env — never from NEXT_PUBLIC_*.
   Forwards: method, body, relevant headers.
   Handles multipart/form-data passthrough for file uploads.
   Preserves response status codes.
```

---

**Verify before Step 15:**
- [ ] `make typecheck` passes
- [ ] `make build` succeeds (Next.js production build)

---

### Step 15 — Frontend Dockerfile and smoke test
**Model: `claude-haiku-4-5`**

---

**Prompt:**

```
Create frontend/Dockerfile using multi-stage build:

Stage 1 (deps): node:20-alpine, WORKDIR /app, COPY package*.json, RUN npm ci
Stage 2 (builder): COPY from deps, COPY source, RUN npm run build
Stage 3 (runner): node:20-alpine, NODE_ENV=production,
  COPY --from=builder .next/standalone, .next/static, public
  EXPOSE 3000, CMD ["node", "server.js"]

Then run: make up-frontend

Verify:
  Open http://localhost:3000
  Upload a small MP4 file
  Confirm redirect to /jobs/{job_id}
  Confirm status badge shows "queued"
Report what you see.
```

---

**Verify before Phase 3:**
- [ ] Upload works end to end to the `queued` state

---

## Phase 3 — FFmpeg Extractor

> **Goal:** Pipeline runs through frame extraction. Wire publisher to Redis at the end.

---

### Step 16 — Extractor scaffold
**Model: `claude-haiku-4-5`**

---

**Prompt:**

```
Create the FFmpeg extractor service scaffold at extractor/:

1. extractor/__init__.py (empty)

2. extractor/pyproject.toml
   name="extractor", requires-python=">=3.12"
   dependencies: dramatiq[redis]>=1.16, dramatiq-crontab>=1.0,
     asyncpg>=0.29, pydantic-settings>=2.0, structlog>=24.0, loguru>=0.7,
     shared @ ../shared
   dev-dependencies: pytest>=8.0, pytest-asyncio>=0.23, ruff>=0.4

3. extractor/Makefile
   Targets: install (uv pip install -e ../shared then uv sync),
   lint, lint-fix, shell (exec into ffmpeg-extractor container),
   logs (tail ffmpeg-extractor logs), clean, clean-all, help

4. extractor/.gitignore
   __pycache__, *.py[cod], .venv/, .pytest_cache/, .ruff_cache/

5. extractor/core/__init__.py (empty)

6. extractor/core/config.py
   Settings class with all extractor env vars from CLAUDE.md:
   SCENE_THRESHOLD=0.35, FRAME_INTERVAL=150, BATCH_SIZE=5,
   DATA_ROOT=/data, FFMPEG_BIN=ffmpeg, FFPROBE_BIN=ffprobe,
   MAX_DURATION_SEC=600, DATABASE_URL, REDIS_URL

7. extractor/core/logging.py
   Same pattern as app/core/logging.py: configure_logging(), LoggerMixin.

Run: cd extractor && make install
Report success or errors.
```

---

**Verify before Step 17:**
- [ ] `cd extractor && make install` succeeds

---

### Step 17 — Extractor domain and repositories
**Model: `claude-sonnet-4-6`**

---

**Prompt:**

```
Create extractor domain and repositories.

Domain (zero external imports):

1. extractor/domain/__init__.py (empty)

2. extractor/domain/video.py
   VideoMeta dataclass: duration_seconds, fps, width, height, codec, total_frames
   DurationExceededError(ValueError)

3. extractor/domain/frame.py
   SelectionReason enum: scene_change, periodic, both
   FrameMetadata dataclass: video_id, frame_id (UUID str), frame_path,
     timestamp (float), frame_number (int), selection_reason (SelectionReason),
     scene_score (float | None), created_at
   FrameExtractionError

Repositories (inherit LoggerMixin, no business logic):

4. extractor/repositories/__init__.py (BaseRepository with LoggerMixin)

5. extractor/repositories/ffprobe_client.py
   Same as app/repositories/ffprobe_client.py — run ffprobe subprocess,
   parse JSON, return VideoMeta. Raise FFprobeError on failure.

6. extractor/repositories/ffmpeg_runner.py
   FFmpegRunner.run(video_path, output_dir, scene_threshold, frame_interval) -> (int, str)
   Builds this command:
     ffmpeg -i {video_path}
       -vf "select='gt(scene,{scene_threshold})+not(mod(n,{frame_interval}))'"
       -vsync vfr -q:v 4 {output_dir}/frame_%04d.jpg
   Runs via asyncio.create_subprocess_exec.
   Returns (exit_code, stderr_text).

7. extractor/repositories/frame_repo.py
   FrameRepository.bulk_insert_frames(frames: list[FrameMetadata]) -> list[str]
   Bulk INSERT via asyncpg executemany(). Returns inserted frame IDs.

8. extractor/repositories/job_repo.py
   update_status(job_id, status, stage, error_message=None)
   update_progress(job_id, progress_pct)
```

---

### Step 18 — Extractor services and pipeline
**Model: `claude-sonnet-4-6`**

---

**Prompt:**

```
Create extractor services, pipeline, and queue actors.

Services (orchestrate repositories, no SQL):

1. extractor/services/__init__.py (BaseService with LoggerMixin)

2. extractor/services/probe.py
   ProbeService.run(video_path) -> VideoMeta
   Calls FFprobeClient. Raises DurationExceededError if duration > MAX_DURATION_SEC.

3. extractor/services/extraction.py
   ExtractionService.run(video_path, output_dir, video_meta) -> list[tuple[int, str]]
   Builds output_dir path: {DATA_ROOT}/frames/{job_id}/
   Creates dir if not exists.
   Calls FFmpegRunner.run().
   Scans output_dir for frame_*.jpg files.
   Returns list of (frame_number, file_path) tuples sorted by frame_number.

4. extractor/services/metadata.py
   MetadataService.resolve(raw_frames, video_meta, video_id) -> list[FrameMetadata]
   For each (frame_number, path):
     timestamp = frame_number / video_meta.fps
     selection_reason: periodic if frame_number % FRAME_INTERVAL == 0,
       scene_change otherwise, both if both conditions true
     scene_score: None for now (requires ffmpeg stderr parsing — skip for MVP)
     frame_id: new UUID

5. extractor/services/batcher.py
   BatcherService.partition(frames: list[FrameMetadata]) -> list[list[FrameMetadata]]
   Split into chunks of BATCH_SIZE. Last chunk may be smaller — always include it.

Pipeline:

6. extractor/pipeline/__init__.py (empty)

7. extractor/pipeline/orchestrator.py
   ExtractionOrchestrator.run(job_id: str) -> None
   Exact sequence:
     a. job_repo.update_status(running, stage=frame_extraction)
     b. video_path = {DATA_ROOT}/uploads/{job_id}.mp4
     c. probe.run(video_path) → VideoMeta
     d. extraction.run(video_path, output_dir, video_meta) → raw_frames
     e. metadata.resolve(raw_frames, video_meta, job_id) → frames
     f. frame_repo.bulk_insert_frames(frames) → frame_ids
     g. batcher.partition(frames) → batches
     h. For each batch: publisher.enqueue_analysis_batch(job_id, [f.frame_id for f in batch])
     i. job_repo.update_status(stage=ai_analysis)
   Partial failure: if FFmpeg exits non-zero but frames exist on disk,
     log warning, continue with available frames, set is_partial flag on job.

Queue:

8. extractor/queue/__init__.py (empty)

9. extractor/queue/consumer.py
   Import ActorMetricsMiddleware from shared.middleware.
   Import ExtractionMessage from shared.messages.
   @dramatiq.actor(queue_name='extraction', max_retries=3)
   def extraction_task(job_id: str) -> None:
     Instantiate ExtractionOrchestrator, call run(job_id).
     On any exception: job_repo.update_status(failed, error_message=str(e)).

10. extractor/queue/publisher.py
    Import AnalysisBatchMessage from shared.messages.
    enqueue_analysis_batch(job_id, frame_ids: list[str]) -> None
      msg = AnalysisBatchMessage(job_id=job_id, frame_ids=frame_ids)
      analysis_batch_task.send(msg.job_id, msg.frame_ids)

11. extractor/main.py
    Import consumer (triggers actor registration).
    Configure logging.
    Get broker, register ActorMetricsMiddleware.
    Init DB pool and Redis at module scope (shared across actor invocations).
```

---

### Step 19 — Wire FastAPI publisher and extractor Dockerfile
**Model: `claude-haiku-4-5`**

---

**Prompt:**

```
Two changes:

1. Update app/queue/publisher.py
   Replace the stub with the real Dramatiq implementation.
   Keep the ExtractionMessage import and log line.
   Replace the pass with:
     from dramatiq import Message
     broker.enqueue(Message(
       queue_name="extraction",
       actor_name="extraction_task",
       args=[msg.job_id],
       kwargs={},
       options={}
     ))
   Do NOT import extractor code. Use Dramatiq's generic message API only.

2. Create extractor/Dockerfile:
   FROM python:3.12-slim
   RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*
   WORKDIR /extractor
   RUN pip install uv
   COPY ../shared /shared
   RUN uv pip install /shared
   COPY pyproject.toml .
   RUN uv sync --no-dev
   COPY . .
   CMD ["uv", "run", "dramatiq", "extractor.main", "--processes", "1", "--threads", "4"]

3. Update docker-compose.yml — add:
   ffmpeg-extractor:
     build: {context: ., dockerfile: extractor/Dockerfile}
     env_file: .env.docker
     volumes: [app_data:/data]
     depends_on: {postgres: {condition: service_healthy}, redis: {condition: service_healthy}}

Then run: make up-extractor
Upload a video. Verify in logs:
  - Extractor picks up the extraction_task message
  - Frames appear in /data/frames/{job_id}/
  - frames table has rows with correct timestamps
  - Job stage moves to ai_analysis
Report what you see.
```

---

**Verify before Phase 4:**
- [ ] Frames appear in `/data/frames/{job_id}/`
- [ ] `frames` table has rows
- [ ] Job `stage` = `ai_analysis`

---

## Phase 4 — Worker Service

> **Goal:** Full end-to-end pipeline including AI analysis, aggregation, and scheduled cleanup.

---

### Step 20 — Worker scaffold
**Model: `claude-haiku-4-5`**

---

**Prompt:**

```
Create the worker service scaffold at worker/:

1. worker/__init__.py (empty)

2. worker/pyproject.toml
   name="worker", requires-python=">=3.12"
   dependencies: dramatiq[redis]>=1.16, dramatiq-crontab>=1.0,
     asyncpg>=0.29, openai>=1.30, pydantic-settings>=2.0,
     structlog>=24.0, loguru>=0.7, shared @ ../shared
   dev-dependencies: pytest>=8.0, pytest-asyncio>=0.23, ruff>=0.4

3. worker/Makefile
   Targets: install (uv pip install -e ../shared then uv sync),
   lint, lint-fix,
   shell (exec into worker-1), shell-1 through shell-4,
   logs (tail worker-1..4 and scheduler),
   trigger-cleanup (exec cleanup_task manually in worker-1),
   clean, clean-all, help

4. worker/.gitignore — same as extractor

5. worker/core/__init__.py (empty)

6. worker/core/config.py
   All worker env vars from CLAUDE.md: AI_MODEL, AI_BASE_URL, AGGREGATION_MODEL,
   MAX_RETRIES, MIN_BACKOFF_SEC, MAX_BACKOFF_SEC,
   JOB_TTL_DAYS, FAILED_JOB_TTL_DAYS, CLEANUP_CRON,
   DATABASE_URL, REDIS_URL, DATA_ROOT

7. worker/core/logging.py — same pattern as other services

Run: cd worker && make install
Report success or errors.
```

---

### Step 21 — Worker domain and repositories
**Model: `claude-sonnet-4-6`**

---

**Prompt:**

```
Create worker domain and repositories.

Domain (zero external imports):

1. worker/domain/__init__.py (empty)

2. worker/domain/analysis.py
   FrameAnalysisResult dataclass: frame_id (str), description (str),
     model_used (str), raw_response (dict), created_at
   EmptyDescriptionError
   validate_analysis(result: FrameAnalysisResult) -> None
     raises EmptyDescriptionError if description is empty or whitespace-only

3. worker/domain/summary.py
   TimelineEvent dataclass: timestamp (float), event (str)
   AggregationResult dataclass: summary (str), timeline (list[TimelineEvent])
   MalformedAggregationError (include raw_text: str field for debugging)
   validate_aggregation_json(raw: str) -> AggregationResult
     strip markdown fences (```json ... ```)
     json.loads()
     validate: has "summary" (str) and "timeline" (list)
     each timeline item has "timestamp" (float) and "event" (str)
     raise MalformedAggregationError with raw text if any check fails

4. worker/domain/cleanup.py
   CleanupTarget dataclass: job_id (str), upload_path (str), frames_dir (str)

Repositories (inherit LoggerMixin, no business logic):

5. worker/repositories/__init__.py (BaseRepository)

6. worker/repositories/ai_client.py
   AIProvider Protocol: analyze_frames(frames, prompt) -> list[str], complete(messages) -> str
   AIClient implements AIProvider using openai.AsyncOpenAI.
   base_url override from config (supports OpenRouter, Ollama).
   All calls wrapped in exponential back-off retry:
     MAX_RETRIES attempts, MIN_BACKOFF_SEC to MAX_BACKOFF_SEC.

7. worker/repositories/frame_repo.py
   get_frames_by_ids(frame_ids: list[str]) -> list[dict]
     returns frame_id, frame_path for each ID
   get_all_descriptions_for_job(job_id: str) -> list[dict]
     JOIN frames + frame_analysis WHERE video_id = job_id
     ORDER BY frames.timestamp ASC
     returns [{timestamp, description}]

8. worker/repositories/analysis_repo.py
   bulk_insert_analysis(results: list[FrameAnalysisResult]) -> None
     INSERT into frame_analysis via asyncpg executemany
   nullify_raw_responses(job_id: str) -> None
     UPDATE frame_analysis SET ai_response = NULL
     WHERE frame_id IN (SELECT id FROM frames WHERE video_id = job_id)

9. worker/repositories/summary_repo.py
   upsert_summary(video_id, result: AggregationResult, is_partial: bool, model_used: str) -> None
     INSERT INTO video_summary ... ON CONFLICT (video_id) DO UPDATE
     Sets generated_at = NOW()

10. worker/repositories/storage_repo.py
    delete_upload(job_id: str) -> None
      Path({DATA_ROOT}/uploads/{job_id}.mp4).unlink(missing_ok=True)
    delete_frames(job_id: str) -> None
      shutil.rmtree({DATA_ROOT}/frames/{job_id}, ignore_errors=True)

11. worker/repositories/job_repo.py
    update_status(job_id, status, stage, error_message=None) -> None
    update_progress(job_id, progress_pct) -> None
    get_pending_batch_count(job_id) -> int
      SELECT COUNT(frames) - COUNT(frame_analysis rows) for this job
    get_expired_jobs() -> list[dict]
      WHERE expires_at < NOW() AND cleaned_at IS NULL AND status IN (completed, failed)
    is_analysis_complete(job_id) -> bool
    mark_cleaned(job_id) -> None
      UPDATE videos SET cleaned_at = NOW()
```

---

### Step 22 — Worker services
**Model: `claude-sonnet-4-6`**

---

**Prompt:**

```
Create worker services. Each service inherits BaseService(LoggerMixin).

1. worker/services/__init__.py (BaseService)

2. worker/services/vision.py
   VisionService.analyze(frame_ids: list[str], job_id: str) -> list[FrameAnalysisResult]
   For each frame_id:
     Load JPEG bytes from frame_path using frame_repo.get_frames_by_ids()
     base64.b64encode() in memory only — never written to disk or DB
   Build single OpenAI API call with all frames as image_url content blocks.
   Parse response: split by frame, map to FrameAnalysisResult.
   Validate each result with validate_analysis().
   Discard base64 immediately after API response.

3. worker/services/aggregator.py
   AggregatorService.aggregate(job_id: str) -> AggregationResult
   Fetch all descriptions via frame_repo.get_all_descriptions_for_job()
   Format as: "[T=25.2s] description text" per frame, newline-joined.
   Prepend system prompt from CLAUDE.md FR-5 aggregation template.
   Call AIClient.complete(messages).
   Parse with validate_aggregation_json().

4. worker/services/completion.py
   CompletionChecker.check(job_id: str) -> None
   Call job_repo.get_pending_batch_count(job_id).
   If 0 (all batches done):
     Redis: SET agg_lock:{job_id} 1 NX EX 60
     If lock acquired: send aggregation_task message to aggregation queue.
     If not acquired: another worker already triggered — do nothing.

5. worker/services/cleanup.py
   CleanupService.clean(job: dict) -> None
   Exact order:
     storage_repo.delete_upload(job_id)
     storage_repo.delete_frames(job_id)
     analysis_repo.nullify_raw_responses(job_id)
     job_repo.mark_cleaned(job_id)
   Log each step with job_id.
```

---

### Step 23 — Worker pipelines, actors, scheduler
**Model: `claude-sonnet-4-6`**

---

**Prompt:**

```
Create worker pipelines, queue actors, scheduler, and main entry point.

Pipelines:

1. worker/pipeline/__init__.py (empty)

2. worker/pipeline/batch_orchestrator.py
   BatchOrchestrator.run(job_id: str, frame_ids: list[str]) -> None
   Sequence:
     a. Update stage=ai_analysis on first batch only
        (check current stage before updating — don't overwrite aggregation)
     b. VisionService.analyze(frame_ids, job_id) → results
     c. validate_analysis() on each result
     d. analysis_repo.bulk_insert_analysis(results)
     e. Recalculate progress_pct: analysed_frames / total_frames * 100
     f. job_repo.update_progress(job_id, progress_pct)
     g. CompletionChecker.check(job_id)
   On exception: job_repo.update_status(failed, error_message=str(e))

3. worker/pipeline/agg_orchestrator.py
   AggOrchestrator.run(job_id: str) -> None
   Sequence:
     a. job_repo.update_status(running, stage=aggregation)
     b. AggregatorService.aggregate(job_id) → AggregationResult
     c. summary_repo.upsert_summary(job_id, result, is_partial=False, model_used=AI_MODEL)
     d. job_repo.mark_completed(job_id)  — sets completed_at and expires_at
   On exception: job_repo.update_status(failed, stage=aggregation, error_message=str(e))
     set expires_at = NOW() + FAILED_JOB_TTL_DAYS

4. worker/pipeline/cleanup_orchestrator.py
   CleanupOrchestrator.run() -> None
   Sequence:
     a. jobs = job_repo.get_expired_jobs()
     b. For each job:
          if not job_repo.is_analysis_complete(job_id): skip (log warning)
          CleanupService.clean(job)
     c. Log count of cleaned jobs.

Queue actors:

5. worker/queue/__init__.py (empty)

6. worker/queue/consumer.py
   Import ActorMetricsMiddleware from shared.middleware.
   Import AnalysisBatchMessage, AggregationMessage from shared.messages.

   @dramatiq.actor(queue_name='analysis', max_retries=3)
   def analysis_batch_task(job_id: str, frame_ids: list[str]) -> None:
     BatchOrchestrator(...).run(job_id, frame_ids)

   @dramatiq.actor(queue_name='aggregation', max_retries=1)
   def aggregation_task(job_id: str) -> None:
     AggOrchestrator(...).run(job_id)

   @dramatiq.actor(queue_name='cleanup', max_retries=3)
   def cleanup_task() -> None:
     CleanupOrchestrator(...).run()

Scheduler and entry point:

7. worker/scheduler.py
   from dramatiq_crontab import crontab
   from worker.queue.consumer import cleanup_task
   from worker.core.config import get_settings

   @crontab(get_settings().CLEANUP_CRON)
   def schedule_cleanup():
       cleanup_task.send()

   Nothing else in this file.

8. worker/main.py
   Import consumer (actor registration).
   Import configure_logging, call it.
   Get broker, register ActorMetricsMiddleware from shared.middleware.
   Init DB pool and Redis at module scope.
```

---

### Step 24 — Worker Dockerfiles and end-to-end test
**Model: `claude-haiku-4-5`**

---

**Prompt:**

```
Create worker/Dockerfile:

FROM python:3.12-slim
WORKDIR /worker
RUN pip install uv
COPY ../shared /shared
RUN uv pip install /shared
COPY pyproject.toml .
RUN uv sync --no-dev
COPY . .
CMD ["uv", "run", "dramatiq", "worker.main", "--processes", "1", "--threads", "3"]

Update docker-compose.yml — add workers and scheduler:

  worker-1: &worker
    build: {context: ., dockerfile: worker/Dockerfile}
    env_file: .env.docker
    volumes: [app_data:/data]
    depends_on: {postgres: {condition: service_healthy}, redis: {condition: service_healthy}}
  worker-2: *worker
  worker-3: *worker
  worker-4: *worker

  scheduler:
    build: {context: ., dockerfile: worker/Dockerfile}
    env_file: .env.docker
    depends_on: [redis]
    command: ["uv", "run", "python", "-m", "dramatiq_crontab", "worker.scheduler"]

Then run: make up

End-to-end verification:
1. Upload an MP4 via the frontend
2. Wait for status = completed
3. Confirm summary and timeline are non-empty

Cleanup verification:
4. Run in shell-db:
   UPDATE videos SET expires_at = NOW() - interval '1 second' WHERE id = '<job_id>';
5. Run: make worker-trigger-cleanup
6. Confirm: /data/uploads/ and /data/frames/{job_id}/ deleted
7. Confirm: frame_analysis.ai_response = NULL, description still present
8. Confirm: videos.cleaned_at is populated

Report results for each step.
```

---

**Verify before Phase 5:**
- [ ] Full pipeline completes: upload → completed
- [ ] Summary and timeline are populated
- [ ] Cleanup verification passes all 8 steps

---

## Phase 5 — Quality and observability

---

### Step 25 — Alembic check and tests
**Model: `claude-sonnet-4-6`**

---

**Prompt:**

```
Two tasks:

Task 1 — Verify migrations:
Open alembic/versions/0001_initial.py.
Confirm these columns exist on the videos table:
  expires_at TIMESTAMPTZ, cleaned_at TIMESTAMPTZ
If either is missing, generate alembic/versions/0002_add_cleanup_columns.py.
Run: cd app && make db-migrate
Confirm zero errors.

Task 2 — Create test suite:
Create tests/ at repo root (not inside any service directory).

tests/__init__.py (empty)

tests/conftest.py
  pytest-asyncio fixtures:
  - test_db: creates test PostgreSQL DB, runs alembic upgrade head, yields
    AsyncSession, drops DB after suite
  - test_redis: yields Redis client connected to test Redis instance
  - test_client: yields httpx.AsyncClient pointed at the FastAPI app
  AIClient mock: returns deterministic fixture responses, no real API calls

tests/fixtures/
  Place a real 5-second 720p MP4 here for extraction tests.
  Create it with ffmpeg: ffmpeg -f lavfi -i testsrc=duration=5:size=1280x720:rate=30 sample.mp4

tests/unit/test_domain_video.py
  validate_upload: happy path, wrong MIME, over size limit, boundary values

tests/unit/test_domain_frame.py
  validate_frame_metadata: happy path, each missing required key

tests/unit/test_domain_summary.py
  validate_aggregation_json: valid JSON, markdown fences, missing fields,
  invalid timeline items, completely invalid input

tests/integration/test_upload_pipeline.py
  POST /api/videos with valid MP4 → 202, job created in DB, extraction queued in Redis

tests/integration/test_extraction_pipeline.py
  extraction_task with tests/fixtures/sample.mp4 and real FFmpeg.
  Confirm frames written to disk, frame rows in DB, analysis batches queued.

tests/integration/test_analysis_pipeline.py
  analysis_batch_task with mocked AIClient.
  Confirm frame_analysis rows inserted, progress updated.

tests/integration/test_aggregation_pipeline.py
  aggregation_task with mocked AIClient returning fixed JSON.
  Confirm video_summary row created, job status = completed.

tests/integration/test_cleanup_pipeline.py
  cleanup_task with expired job fixture.
  Confirm files deleted, ai_response nullified, cleaned_at set.

Run: make test
Report pass/fail counts.
```

---

### Step 26 — devtrack-sdk and final verification
**Model: `claude-sonnet-4-6`**

---

**Prompt:**

```
Task 1 — devtrack-sdk integration:
Fetch and read https://github.com/pkaranje/devtrack-sdk README.
Confirm exact import path and init call signature.
Update app/main.py with the confirmed registration code.
Add a comment to .env.example showing the dashboard URL.

Task 2 — Add pipeline observability log lines:
In each of the three pipeline orchestrators, add Loguru structured log lines:
  Entry:   logger.info("pipeline_start", job_id=job_id, stage=<stage_name>)
  Exit:    logger.info("pipeline_done", job_id=job_id, stage=<stage_name>, duration_ms=<ms>)
  Failure: logger.error("pipeline_failed", job_id=job_id, stage=<stage_name>,
             error=str(e), retry_count=<count>)

Task 3 — Final verification:
Run each of the following and report the result:
  make lint        (must be zero errors)
  make test        (must be all green)
  make up          (all 10 services must reach healthy state)

Then:
  Upload an MP4 and confirm the full pipeline completes.
  Open the devtrack dashboard URL and confirm metrics are visible.
```

---

**Verify before Phase 6:**
- [ ] `make lint` zero errors
- [ ] `make test` all green
- [ ] `make up` all 10 services healthy
- [ ] devtrack dashboard shows request metrics

---

## Phase 6 — CI/CD

> **Only start after Step 26 passes completely.**

---

### Step 27 — GitHub Actions
**Model: `claude-haiku-4-5`**

---

**Prompt:**

```
Create two GitHub Actions workflows:

1. .github/workflows/ci.yml
   Trigger: pull_request targeting main
   Jobs:

   lint:
     runs-on: ubuntu-latest
     steps:
       - uses: actions/checkout@v4
       - uses: astral-sh/setup-uv@v4
       - run: cd shared && uv sync
       - run: cd app && uv sync
       - run: cd extractor && uv sync
       - run: cd worker && uv sync
       - run: make lint

   test:
     runs-on: ubuntu-latest
     services:
       postgres: {image: postgres:16-alpine, env: {POSTGRES_DB: test, POSTGRES_PASSWORD: test},
         options: "--health-cmd pg_isready --health-interval 5s --health-retries 5",
         ports: ["5432:5432"]}
       redis: {image: redis:7-alpine,
         options: "--health-cmd 'redis-cli ping' --health-interval 5s --health-retries 5",
         ports: ["6379:6379"]}
     env:
       DATABASE_URL: postgresql+asyncpg://postgres:test@localhost/test
       REDIS_URL: redis://localhost:6379
     steps:
       - uses: actions/checkout@v4
       - uses: astral-sh/setup-uv@v4
       - run: cd shared && uv sync
       - run: cd app && uv sync
       - run: cd app && uv run alembic upgrade head
       - run: make test

2. .github/workflows/build.yml
   Trigger: push to main
   Job — build Docker images for all services in matrix:
     services: [api, extractor, worker, frontend]
     context map: api→app, extractor→extractor, worker→worker, frontend→frontend
   Steps:
     - checkout
     - docker/login-action@v3 with ghcr.io, username pkaranje, password GHCR_TOKEN secret
     - docker/build-push-action@v5
       context: repo root (.), dockerfile: {service_dir}/Dockerfile
       push: true
       tag: ghcr.io/pkaranje/video-summarizer/{service}:{github.sha}
```

---

### Step 28 — Final commit
**Model: `claude-haiku-4-5`**

---

**Prompt:**

```
Final checklist before merging to main.
Verify each item and report pass or fail:

1. .gitignore: .env and .env.docker are ignored, .env.example is NOT ignored
2. All four uv.lock files committed: shared/, app/, extractor/, worker/
3. All five Makefiles present: root, shared/, app/, extractor/, worker/, frontend/
4. All four Dockerfiles present: app/, extractor/, worker/, frontend/
5. docker-compose.yml has exactly 10 services:
   postgres, redis, api, frontend, ffmpeg-extractor,
   worker-1, worker-2, worker-3, worker-4, scheduler
6. .github/workflows/ci.yml and build.yml present
7. make lint → zero errors
8. make test → all green
9. Create a test PR to main and confirm both CI workflows pass

If any item fails, fix it and re-verify before closing.
```

---

## Done

All 28 steps complete across 6 phases:

- Full video → summary pipeline
- Dramatiq crontab scheduled cleanup
- devtrack-sdk observability on FastAPI
- ActorMetricsMiddleware on extractor and worker
- Pytest unit + integration test suite
- GitHub Actions CI (lint + test) and build (Docker images to GHCR)
