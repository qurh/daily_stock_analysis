"""Knowledge Base Schemas."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class CategoryCreate(BaseModel):
    """Category creation schema."""

    name: str = Field(..., description="Category name")
    slug: str = Field(..., description="URL-friendly slug")
    parent_id: Optional[int] = Field(None, description="Parent category ID")
    description: Optional[str] = None
    icon: Optional[str] = None
    sort_order: int = 0


class CategoryResponse(BaseModel):
    """Category response schema."""

    id: int
    name: str
    slug: str
    parent_id: Optional[int]
    description: Optional[str]
    icon: Optional[str]
    sort_order: int
    created_at: datetime
    document_count: int = 0


class DocumentCreate(BaseModel):
    """Document creation schema."""

    title: str = Field(..., description="Document title")
    slug: Optional[str] = Field(None, description="URL-friendly slug")
    category_id: Optional[int] = Field(None, description="Category ID")
    content: str = Field(..., description="Document content in Markdown")
    tags: Optional[List[str]] = Field(default_factory=list)
    related_codes: Optional[List[str]] = Field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class DocumentUpdate(BaseModel):
    """Document update schema."""

    title: Optional[str] = None
    category_id: Optional[int] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None
    related_codes: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    status: Optional[str] = None


class DocumentResponse(BaseModel):
    """Document response schema."""

    id: int
    title: str
    slug: Optional[str]
    category_id: Optional[int]
    category: Optional[CategoryResponse] = None
    status: str
    content: str
    tags: List[str]
    related_codes: List[str]
    auto_generated: bool
    version: int
    created_at: datetime
    updated_at: Optional[datetime] = None


class DocumentListResponse(BaseModel):
    """Document list response."""

    documents: List[DocumentResponse]
    total: int
    limit: int
    offset: int


class SearchRequest(BaseModel):
    """Knowledge base search request."""

    query: str = Field(..., description="Search query")
    limit: int = Field(default=10, description="Max results")
    filters: Optional[Dict[str, Any]] = Field(None, description="Search filters")
    category_ids: Optional[List[int]] = None
    tags: Optional[List[str]] = None


class SearchResult(BaseModel):
    """Single search result."""

    document_id: int
    title: str
    content: str
    score: float
    highlights: List[str]
    metadata: Dict[str, Any]


class SearchResponse(BaseModel):
    """Search response schema."""

    query: str
    results: List[SearchResult]
    total: int
    took_ms: int


class KnowledgeGraphNode(BaseModel):
    """Knowledge graph node."""

    id: int
    name: str
    type: str
    code: Optional[str]
    metadata: Dict[str, Any]


class KnowledgeGraphEdge(BaseModel):
    """Knowledge graph edge."""

    source: int
    target: int
    relation_type: str
    weight: float


class KnowledgeGraphResponse(BaseModel):
    """Knowledge graph response."""

    nodes: List[KnowledgeGraphNode]
    edges: List[KnowledgeGraphEdge]


class ImportFromChatRequest(BaseModel):
    """Import content from chat to knowledge base."""

    message_id: Optional[str] = None
    content: str = Field(..., description="Content to import")
    title: str = Field(..., description="Document title")
    category_id: Optional[int] = None
    tags: Optional[List[str]] = None
    related_codes: Optional[List[str]] = None
