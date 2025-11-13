"""Common schemas shared across multiple endpoints."""
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class MatchFactors(BaseModel):
    """Match factor scores for different dimensions."""
    sector: Optional[float] = Field(None, description="Sector match score (0-100)")
    stage: Optional[float] = Field(None, description="Stage alignment score (0-100)")
    geography: Optional[float] = Field(None, description="Geography fit score (0-100)")
    checkSize: Optional[float] = Field(None, description="Check size fit score (0-100)")
    traction: Optional[float] = Field(None, description="Traction signals score (0-100)")
    graph_proximity: Optional[float] = Field(None, description="Graph proximity score (0-100)")


class IntroPathNode(BaseModel):
    """A node in an introduction path."""
    id: int
    name: str
    company: Optional[str] = None
    position: Optional[str] = None
    role: Optional[str] = None
    linkedin_url: Optional[str] = None


class BaseEntityData(BaseModel):
    """Base entity data fields."""
    id: int
    name: str
    email: Optional[str] = None
    company: Optional[str] = None
    position: Optional[str] = None
    role: Optional[str] = None
    linkedin_url: Optional[str] = None

