"""Pydantic request/response schemas for the Knowledge Service API."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ── Request Schemas ─────────────────────────────────────────────────


class DocumentCreate(BaseModel):
    title: str = Field(..., min_length=1, description="Document title")
    source: str | None = Field(None, description="Document source (URL, file path, etc.)")
    category: str = Field(
        ...,
        description="Knowledge category: policy, plan, faq, compliance, process",
    )
    content: str = Field(..., min_length=1, description="Full document text")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Search query")
    category: str | None = Field(None, description="Filter by category")
    top_k: int = Field(5, ge=1, le=50, description="Number of results to return")


# ── Response Schemas ────────────────────────────────────────────────


class DocumentResponse(BaseModel):
    document_id: str
    title: str
    source: str | None
    category: str
    chunk_count: int
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class DocumentDetailResponse(DocumentResponse):
    content: str


class SearchResult(BaseModel):
    chunk_id: str
    document_id: str
    document_title: str
    category: str
    content: str
    similarity: float


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]
    total: int


class CategoryResponse(BaseModel):
    categories: list[str]
