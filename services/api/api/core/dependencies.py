from typing import Annotated, AsyncGenerator

from fastapi import Depends, Request
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from api.repositories.frame_repo import FrameRepository
from api.repositories.job_repo import JobRepository
from api.services.status import StatusService
from api.services.summary import SummaryService
from api.services.upload import UploadService


async def get_db(request: Request) -> AsyncGenerator[AsyncSession, None]:
    async with request.app.state.session_factory.begin() as session:
        yield session


async def get_redis(request: Request) -> Redis:
    return request.app.state.redis


async def get_job_repo(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> JobRepository:
    return JobRepository(session)


async def get_frame_repo(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> FrameRepository:
    return FrameRepository(session)


async def get_upload_service(
    job_repo: Annotated[JobRepository, Depends(get_job_repo)],
) -> UploadService:
    return UploadService(job_repo)


async def get_status_service(
    job_repo: Annotated[JobRepository, Depends(get_job_repo)],
) -> StatusService:
    return StatusService(job_repo)


async def get_summary_service(
    session: Annotated[AsyncSession, Depends(get_db)],
    job_repo: Annotated[JobRepository, Depends(get_job_repo)],
) -> SummaryService:
    return SummaryService(session, job_repo)
