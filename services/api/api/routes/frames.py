from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from api.core.dependencies import get_frame_repo, get_job_repo
from api.repositories.frame_repo import FrameRepository
from api.repositories.job_repo import JobRepository
from api.schemas.video import FrameMetadataResponse

router = APIRouter()


@router.get("/videos/{job_id}/frames", response_model=list[FrameMetadataResponse])
async def get_frames(
    job_id: str,
    job_repo: Annotated[JobRepository, Depends(get_job_repo)],
    frame_repo: Annotated[FrameRepository, Depends(get_frame_repo)],
) -> list[FrameMetadataResponse]:
    job = await job_repo.get_by_id(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job {job_id!r} not found.")
    frames = await frame_repo.get_frames_for_job(job_id)
    return [
        FrameMetadataResponse(
            id=f.id,
            timestamp=f.timestamp,
            frame_number=f.frame_number,
            selection_reason=f.selection_reason,
            scene_score=f.scene_score,
        )
        for f in frames
    ]
