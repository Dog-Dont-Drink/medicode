"""Project-related Pydantic schemas."""
from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel


class ProjectCreate(BaseModel):
    name: str
    study_type: str | None = None
    description: str | None = None


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    status: str | None = None


class ProjectResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    study_type: str | None = None
    status: str = "active"
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectListItem(BaseModel):
    id: str
    name: str
    description: str | None = None
    study_type: str | None = None
    status: str
    dataset_count: int = 0
    analysis_count: int = 0
    updated_at: datetime

    model_config = {"from_attributes": True}
