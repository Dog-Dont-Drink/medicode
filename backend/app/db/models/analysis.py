"""Analysis and AnalysisResult models."""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import Base, GUID


class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    dataset_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), ForeignKey("datasets.id", ondelete="SET NULL"), nullable=True)
    name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    analysis_type: Mapped[str] = mapped_column(String(30), nullable=False)
    configuration: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    tokens_consumed: Mapped[int] = mapped_column(Integer, default=0)
    created_by: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    executed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    execution_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    analysis_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False, index=True)
    result_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    tables: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    charts: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    script_r: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    script_python: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
