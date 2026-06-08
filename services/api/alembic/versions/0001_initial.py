"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-06-08 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "videos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("filename", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("stage", sa.Text(), nullable=True),
        sa.Column("progress_pct", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
        sa.Column("resolution", sa.Text(), nullable=True),
        sa.Column("fps", sa.Float(), nullable=True),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("uploaded_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("cleaned_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )

    op.create_table(
        "frames",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("video_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("videos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("frame_path", sa.Text(), nullable=False),
        sa.Column("timestamp", sa.Float(), nullable=False),
        sa.Column("frame_number", sa.Integer(), nullable=False),
        sa.Column("selection_reason", sa.Text(), nullable=False),
        sa.Column("scene_score", sa.Float(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "frame_analysis",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("frame_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("frames.id", ondelete="CASCADE"), nullable=False),
        sa.Column("ai_response", postgresql.JSONB(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("model_used", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "video_summary",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("video_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("timeline", postgresql.JSONB(), nullable=True),
        sa.Column("is_partial", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("model_used", sa.Text(), nullable=True),
        sa.Column("generated_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("video_summary")
    op.drop_table("frame_analysis")
    op.drop_table("frames")
    op.drop_table("videos")
