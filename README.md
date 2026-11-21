# AI Video Intelligence Platform

Upload an MP4 and get back an AI-written summary and a timestamped timeline of what happens in it.

The system extracts representative frames with FFmpeg, sends them to a vision model (OpenAI, Gemini, or a local Ollama model) in parallel, and aggregates the per-frame descriptions into a prose summary plus an event timeline.

## How it works

```
Upload (Next.js UI) -> API (FastAPI)
  -> extractor: FFmpeg frame extraction (scene changes + fixed interval)
  -> workers: vision-model analysis of frame batches (Dramatiq + Redis)
  -> aggregation: summary + timeline saved to PostgreSQL
  -> scheduler: periodic cleanup of expired uploads and frames
```

Job stages: `upload_validation` -> `frame_extraction` -> `ai_analysis` -> `aggregation` -> `completed`. The UI polls the job status and shows the summary and timeline when it is done.

## Stack

| Part | Technology |
| --- | --- |
| API | FastAPI, SQLAlchemy, Alembic |
| Queue and workers | Dramatiq, Redis |
| Frame extraction | FFmpeg / FFprobe |
| Database | PostgreSQL |
| Frontend | Next.js 15 (App Router), TypeScript |
| AI providers | Any OpenAI-compatible vision API: OpenAI, Gemini, or Ollama (`qwen2.5vl:3b`) |
| Packaging | Docker Compose, one repo (monorepo) with a shared internal library |

## Quickstart

Requires Docker with Compose v2.

```bash
make env-check        # creates .env.docker.* from the .example files
# edit .env.docker.worker: set your AI provider settings (see below)
make up               # builds and starts all services
```

- UI: http://localhost:3000
- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

Run `make help` for the full list of targets (lint, tests, database migrations, service subsets, cleanup).

### Choosing an AI provider

The worker talks to an OpenAI-compatible API, so switching providers is a configuration change in `.env.docker.worker` (`AI_MODEL`, `AGGREGATION_MODEL`, `AI_BASE_URL`, `OPENAI_API_KEY`).

- **OpenAI** (default): set `OPENAI_API_KEY`.
- **Gemini**: set `AI_BASE_URL` to Google's OpenAI-compatible endpoint, use a Gemini model name, and put your Google AI Studio key in `OPENAI_API_KEY`.
- **Ollama (local)**: the Compose file includes an optional Ollama service that pulls `qwen2.5vl:3b` on first start. Larger local models are not supported on an 8 GB machine.

See `CLAUDE.md` for the exact values and RAM guidance.

## API

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/v1/videos` | Upload an MP4 (multipart, field `file`); returns a job id |
| GET | `/api/v1/videos/{job_id}/status` | Stage and progress |
| GET | `/api/v1/videos/{job_id}/summary` | Written summary |
| GET | `/api/v1/videos/{job_id}/timeline` | Timestamped events |
| GET | `/api/v1/videos/{job_id}/frames` | Extracted frame metadata |
| GET | `/health` | Health check |

Default limits: 500 MB file size and 600 seconds of video (configurable via `MAX_FILE_SIZE_MB` and `MAX_DURATION_SEC`).

## Repository layout

```
services/api/        FastAPI backend
services/extractor/  FFmpeg frame extraction worker
services/worker/     Vision analysis, aggregation, cleanup, scheduler
libs/shared/         Shared message types and middleware
frontend/            Next.js UI
docker-compose.yml   Full stack
```

Each Python service follows the same layering: routes or actors, then services, then repositories, with a pure-Python `domain/` layer for validation. Architecture and conventions are documented in `CLAUDE.md`.

## Scope

This is an MVP. Live streaming, audio transcription, face recognition, object tracking, authentication, and semantic search are out of scope for now.
