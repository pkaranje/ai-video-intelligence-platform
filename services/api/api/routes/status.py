from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from api.core.dependencies import get_status_service
from api.domain.video import JobNotFoundError
from api.schemas.video import StatusResponse
from api.services.status import StatusService

router = APIRouter()


@router.get("/videos/{job_id}/status", response_model=StatusResponse)
async def get_status(
    job_id: str,
    service: Annotated[StatusService, Depends(get_status_service)],
) -> StatusResponse:
    try:
        return await service.get(job_id)
    except JobNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
