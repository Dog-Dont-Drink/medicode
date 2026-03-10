"""Execution records for clinical workflow runs."""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import Base, GUID


class WorkflowRun(Base):
    __tablename__ = "workflow_runs"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    dataset_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    workflow_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), ForeignKey("project_workflows.id", ondelete="SET NULL"), nullable=True, index=True)
    owner_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    template_kind: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="completed", nullable=False)
    request_payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    dataset_state: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    final_predictors: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    logs: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    engine_notes: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    node_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    artifact_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class WorkflowRunNode(Base):
    __tablename__ = "workflow_run_nodes"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("workflow_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    node_id: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    module_id: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    label: Mapped[str] = mapped_column(String(200), nullable=False)
    stage_id: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    input_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    output_summary: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    output_tables: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    output_plots: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    logs: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    next_dataset_ref: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    next_variable_set: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    execution_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class WorkflowArtifact(Base):
    __tablename__ = "workflow_artifacts"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("workflow_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    run_node_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), ForeignKey("workflow_run_nodes.id", ondelete="CASCADE"), nullable=True, index=True)
    owner_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    artifact_type: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    media_type: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    storage_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
