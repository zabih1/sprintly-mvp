"""Search-related schemas."""
from typing import List, Optional

from pydantic import BaseModel, Field

from .common import IntroPathNode, MatchFactors


class SearchFilters(BaseModel):
    """Search filter parameters."""
    role: Optional[str] = None
    sector: Optional[str] = None
    stage: Optional[str] = None
    location: Optional[str] = None


class MatchResult(BaseModel):
    """A single match result with comprehensive data."""
    id: int
    name: str
    company: Optional[str] = None
    position: Optional[str] = None
    linkedin_url: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    sector_focus: Optional[List[str]] = None
    stage_focus: Optional[List[str]] = None
    location: Optional[str] = None
    check_size_min: Optional[int] = None
    check_size_max: Optional[int] = None
    investment_thesis: Optional[str] = None
    tags: Optional[List[str]] = None
    score: float = Field(..., description="Overall match score (0-100)")
    similarity_score: float = Field(..., description="Vector similarity score")
    match_factors: MatchFactors
    reasons: List[str] = []
    confidence_score: Optional[float] = None
    intro_path: List[IntroPathNode] = []
    connection_strength: float = 0.0


class SearchResponse(BaseModel):
    """Response schema for search endpoint."""
    query: str
    filters: SearchFilters
    count: int
    matches: List[MatchResult]

