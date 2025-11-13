"""Upload related schemas."""
from pydantic import BaseModel, Field


class UploadStats(BaseModel):
    """Statistics from CSV upload processing."""
    total: int = Field(..., description="Total rows in CSV")
    created: int = Field(..., description="Number of entities created")
    skipped: int = Field(..., description="Number of entities skipped (already exist)")
    errors: int = Field(..., description="Number of rows with errors")


class UploadResponse(BaseModel):
    """Response schema for file upload."""
    message: str
    stats: UploadStats

