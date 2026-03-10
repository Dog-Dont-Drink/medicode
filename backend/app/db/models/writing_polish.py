"""Writing polish persistence models (documents, versions, and sentence edits)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import Base, GUID


class WritingDocument(Base):
    __tablename__ = "writing_documents"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), default="Untitled")
    raw_text: Mapped[str] = mapped_column(Text, default="")
    text_type: Mapped[str] = mapped_column(String(20), default="paragraph")  # sentence|paragraph|full
    section_type: Mapped[str] = mapped_column(String(30), default="Abstract")  # Abstract|Introduction|Methods|Results|Discussion|Other
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class WritingDocumentVersion(Base):
    __tablename__ = "writing_document_versions"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("writing_documents.id", ondelete="CASCADE"), nullable=False, index=True)
    version_no: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, default="")
    source_module: Mapped[str] = mapped_column(String(50), default="grammar")
    settings: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    llm_tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class GrammarEdit(Base):
    __tablename__ = "grammar_edits"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("writing_documents.id", ondelete="CASCADE"), nullable=False, index=True)
    version_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("writing_document_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    sentence_index: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    suffix: Mapped[str] = mapped_column(Text, default="")
    original_text: Mapped[str] = mapped_column(Text, default="")
    revised_text: Mapped[str] = mapped_column(Text, default="")
    edit_types: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)
    reasons: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    changed: Mapped[bool] = mapped_column(Boolean, default=False)
    accepted: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

