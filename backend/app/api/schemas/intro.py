"""Introduction path related schemas."""
from typing import List, Optional

from pydantic import BaseModel

from .common import IntroPathNode


class MutualConnection(BaseModel):
    """A mutual connection between two entities."""
    id: int
    name: str
    company: Optional[str] = None
    position: Optional[str] = None
    role: Optional[str] = None


class IntroPathResponse(BaseModel):
    """Response schema for introduction path endpoint."""
    source_id: int
    target_id: int
    intro_path: List[IntroPathNode]
    mutual_connections: List[MutualConnection]
    connection_strength: float

