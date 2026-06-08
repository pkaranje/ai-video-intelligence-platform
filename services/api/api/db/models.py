import uuid

from sqlalchemy import Boolean, BigInteger, Float, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func
from sqlalchemy import TIMESTAMP


class Base(DeclarativeBase):
    pass


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


class Video(Base):
    __tablename__ = "videos"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    filename: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    stage: Mapped[str | None] = mapped_column(Text, nullable=True)
    progress_pct: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    resolution: Mapped[str | None] = mapped_column(Text, nullable=True)
    fps: Mapped[float | None] = mapped_column(Float, nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    uploaded_at: Mapped[object] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    completed_at: Mapped[object | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    expires_at: Mapped[object | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    cleaned_at: Mapped[object | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)


class Frame(Base):
    __tablename__ = "frames"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    video_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)
    frame_path: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[float] = mapped_column(Float, nullable=False)
    frame_number: Mapped[int] = mapped_column(Integer, nullable=False)
    selection_reason: Mapped[str] = mapped_column(Text, nullable=False)
    scene_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[object] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)


class FrameAnalysis(Base):
    __tablename__ = "frame_analysis"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    frame_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("frames.id", ondelete="CASCADE"), nullable=False)
    ai_response: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_used: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[object] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)


class VideoSummary(Base):
    __tablename__ = "video_summary"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    video_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("videos.id", ondelete="CASCADE"), unique=True, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    timeline: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    is_partial: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    model_used: Mapped[str | None] = mapped_column(Text, nullable=True)
    generated_at: Mapped[object | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
