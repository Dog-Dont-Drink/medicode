"""Schemas for writing polish modules (grammar proofreading, etc.)."""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


TextType = Literal["sentence", "paragraph", "full"]
SectionType = Literal["Abstract", "Introduction", "Methods", "Results", "Discussion", "Other"]
PolishStrength = Literal["conservative", "standard", "deep"]


class GrammarDocumentCreateRequest(BaseModel):
    title: str = Field(default="Untitled", max_length=200)
    raw_text: str = Field(default="")
    text_type: TextType = Field(default="paragraph")
    section_type: SectionType = Field(default="Abstract")


class GrammarDocumentSummaryResponse(BaseModel):
    id: str
    title: str
    text_type: TextType
    section_type: SectionType
    updated_at: datetime
    created_at: datetime


class GrammarVersionResponse(BaseModel):
    id: str
    version_no: int
    source_module: str
    settings: Optional[dict] = None
    model: Optional[str] = None
    llm_tokens_used: int = 0
    created_at: datetime


class GrammarEditResponse(BaseModel):
    id: str
    sentence_index: int
    original_text: str
    revised_text: str
    edit_types: list[str] = []
    reasons: list[str] = []
    confidence: float | None = None
    changed: bool = False
    accepted: bool | None = None


class GrammarDocumentDetailResponse(BaseModel):
    id: str
    title: str
    raw_text: str
    text_type: TextType
    section_type: SectionType
    versions: list[GrammarVersionResponse] = []


class GrammarPolishRequest(BaseModel):
    raw_text: str
    text_type: TextType = Field(default="paragraph")
    section_type: SectionType = Field(default="Abstract")
    strength: PolishStrength = Field(default="standard")
    protect_terms: bool = Field(default=True)
    preserve_structure: bool = Field(default=False)


class GrammarPolishResponse(BaseModel):
    document_id: str
    version: GrammarVersionResponse
    revised_text: str
    edits: list[GrammarEditResponse]
    summary: dict
    charged_resources: int = 0
    charged_tokens: int = 0
    resource_balance: int | None = None


class GrammarEditDecisionRequest(BaseModel):
    accepted: bool


class GrammarUploadParseResponse(BaseModel):
    filename: str
    text: str

