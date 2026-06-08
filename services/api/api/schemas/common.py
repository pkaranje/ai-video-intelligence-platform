from pydantic import BaseModel


class ErrorDetail(BaseModel):
    message: str
    code: str


class HealthResponse(BaseModel):
    status: str
