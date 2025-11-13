"""Prompts module for AI-powered features."""

from .email_prompts import (
    CASUAL_EMAIL_PROMPT,
    EMAIL_SYSTEM_PROMPT,
    ENTHUSIASTIC_EMAIL_PROMPT,
    FORMAL_EMAIL_PROMPT,
)
from .enrichment_prompts import ENRICHMENT_PROMPT, SYSTEM_PROMPT

__all__ = [
    "ENRICHMENT_PROMPT",
    "SYSTEM_PROMPT",
    "FORMAL_EMAIL_PROMPT",
    "CASUAL_EMAIL_PROMPT",
    "ENTHUSIASTIC_EMAIL_PROMPT",
    "EMAIL_SYSTEM_PROMPT",
]

