from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from api.core.dependencies import get_summary_service
from api.domain.video import JobNotFoundError, SummaryNotReadyError
from api.schemas.summary import SummaryResponse
from api.services.summary import SummaryService

router = APIRouter()


@router.get("/videos/{job_id}/summary", response_model=SummaryResponse)
async def get_summary(
    job_id: str,
    service: Annotated[SummaryService, Depends(get_summary_service)],
) -> SummaryResponse:
    try:
        return await service.get_summary(job_id)
    except (JobNotFoundError, SummaryNotReadyError) as exc:
        raise HTTPException(status_code=404, detail=str(exc))
