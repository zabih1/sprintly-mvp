"""Email generation schemas."""
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class EmailTone(str, Enum):
    """Email tone options."""
    FORMAL = "formal"
    CASUAL = "casual"
    ENTHUSIASTIC = "enthusiastic"


class EmailGenerationResponse(BaseModel):
    """Response containing generated email variants."""
    target_investor: str = Field(..., description="Investor name and company")
    intro_via: str = Field(..., description="Mutual connection name")
    match_score: float = Field(..., description="Overall match score (0-100)")
    emails: Dict[EmailTone, str] = Field(..., description="Generated email drafts keyed by tone")


class EmailGenerationRequest(BaseModel):
    """Request body for email generation."""
    source_id: Optional[int] = Field(1, description="Founder ID (default: 1)")
    tones: Optional[List[EmailTone]] = Field(
        default=[EmailTone.FORMAL, EmailTone.CASUAL, EmailTone.ENTHUSIASTIC],
        description="List of tones to generate"
    )
