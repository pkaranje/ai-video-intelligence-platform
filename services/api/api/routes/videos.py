from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status

from api.core.dependencies import get_upload_service
from api.domain.video import (
    DurationExceededError,
    UnsupportedFormatError,
    UploadTooLargeError,
)
from api.schemas.video import UploadResponse
from api.services.upload import UploadService

router = APIRouter()


@router.post(
    "/videos", response_model=UploadResponse, status_code=status.HTTP_202_ACCEPTED
)
async def upload_video(
    file: UploadFile,
    service: Annotated[UploadService, Depends(get_upload_service)],
) -> UploadResponse:
    try:
        return await service.upload(file)
    except UnsupportedFormatError as exc:
        raise HTTPException(status_code=415, detail=str(exc))
    except UploadTooLargeError as exc:
        raise HTTPException(status_code=413, detail=str(exc))
    except DurationExceededError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
