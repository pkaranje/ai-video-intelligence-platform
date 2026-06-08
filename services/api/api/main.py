from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from devtrack_sdk.controller import router as devtrack_router
from devtrack_sdk.middleware import DevTrackMiddleware

from api.core.config import get_settings
from api.core.logging import configure_logging
from api.core.middleware import RequestLoggingMiddleware
from api.routes import frames, health, status, summary, timeline, videos


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    configure_logging()
    settings = get_settings()

    engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
    app.state.session_factory = async_sessionmaker(engine, expire_on_commit=False)
    app.state.redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)

    yield

    await app.state.redis.aclose()
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(title="AI Video Intelligence Platform", lifespan=lifespan)

    app.include_router(devtrack_router)
    app.include_router(health.router)
    app.include_router(videos.router, prefix="/api")
    app.include_router(status.router, prefix="/api")
    app.include_router(summary.router, prefix="/api")
    app.include_router(timeline.router, prefix="/api")
    app.include_router(frames.router, prefix="/api")

    app.add_middleware(
        DevTrackMiddleware,
        exclude_path=["/healthz", "/docs", "/redoc", "/openapi.json"],
    )
    app.add_middleware(RequestLoggingMiddleware)

    return app


app = create_app()
