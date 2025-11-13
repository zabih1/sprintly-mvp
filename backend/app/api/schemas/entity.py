"""Entity-related schemas."""
from typing import List, Optional

from pydantic import BaseModel, Field


class EntityResponse(BaseModel):
    """Response schema for a single entity."""
    id: int
    name: str
    email: Optional[str] = None
    company: Optional[str] = None
    position: Optional[str] = None
    role: Optional[str] = None
    sector_focus: Optional[List[str]] = None
    stage_focus: Optional[List[str]] = None
    location: Optional[str] = None
    linkedin_url: Optional[str] = None

    class Config:
        from_attributes = True


class EntityListResponse(BaseModel):
    """Response schema for list of entities."""
    count: int
    entities: List[EntityResponse]

