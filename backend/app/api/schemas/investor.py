"""Investor-related schemas."""
from typing import List, Optional

from pydantic import BaseModel, Field

from .common import IntroPathNode, MatchFactors


class InvestorResponse(BaseModel):
    """Response schema for an investor with match scoring."""
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
    match_factors: MatchFactors
    intro_path: List[IntroPathNode] = []
    confidence_score: Optional[float] = None

    class Config:
        from_attributes = True


class InvestorListResponse(BaseModel):
    """Response schema for list of investors."""
    count: int
    investors: List[InvestorResponse]

