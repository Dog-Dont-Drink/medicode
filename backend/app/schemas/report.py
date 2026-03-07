"""Schemas for saved analysis reports."""

from typing import Literal

from pydantic import BaseModel


class ReportListItemResponse(BaseModel):
    analysis_id: str
    name: str
    analysis_type: str
    status: str
    project_id: str
    project_name: str
    dataset_id: str | None = None
    dataset_name: str | None = None
    feature_name: str | None = None
    language: Literal["zh", "en"] | None = None
    model: str | None = None
    group_variable: str | None = None
    content: str | None = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    actual_tokens: int = 0
    billed_tokens: int = 0
    created_at: str
    executed_at: str | None = None

