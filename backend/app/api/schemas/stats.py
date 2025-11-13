"""Statistics related schemas."""
from pydantic import BaseModel


class NetworkStatsResponse(BaseModel):
    """Response schema for network statistics."""
    total_entities: int
    investors: int
    founders: int
    enablers: int
    others: int

