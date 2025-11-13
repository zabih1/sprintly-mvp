"""Email generation service for warm introductions."""
from __future__ import annotations

import json
from typing import Dict, List, Optional

import openai

from app.core.config import settings
from app.core.models import Entity
from app.services.prompts.email_prompts import (
    CASUAL_EMAIL_PROMPT,
    EMAIL_SYSTEM_PROMPT,
    ENTHUSIASTIC_EMAIL_PROMPT,
    FORMAL_EMAIL_PROMPT,
)

# Initialize OpenAI
openai.api_key = settings.openai_api_key


def _select_match_highlights(match_factors: Dict[str, float]) -> List[str]:
    """Select top 3 match reasons from match factors."""
    if not match_factors:
        return ["Strong overall match based on profile analysis"]
    
    # Sort by score descending
    sorted_factors = sorted(match_factors.items(), key=lambda x: x[1], reverse=True)
    
    highlights = []
    factor_labels = {
        'sector': 'Sector Match',
        'stage': 'Stage Alignment',
        'geography': 'Geography Fit',
        'checkSize': 'Check Size Fit',
        'traction': 'Traction Signals',
        'graph_proximity': 'Network Proximity'
    }
    
    for factor, score in sorted_factors[:3]:
        label = factor_labels.get(factor, factor.title())
        highlights.append(f"{label}: {score:.0f}%")
    
    return highlights


def _format_intro_path(intro_path: List[Dict]) -> str:
    """Format introduction path into readable text."""
    if not intro_path:
        return "Direct connection"
    
    if len(intro_path) <= 2:
        return "Direct connection"
    
    # Get the middle person (mutual connection)
    mutual = intro_path[1] if len(intro_path) > 1 else intro_path[0]
    return mutual.get('name', 'Mutual connection')


def _build_email_context(
    founder: Entity,
    investor: Entity,
    match_factors: Dict[str, float],
    match_score: float,
    intro_path: List[Dict],
    mutual_connections: List[Dict],
) -> Dict[str, str]:
    """Build context dictionary for email generation."""
    # Get mutual connection
    mutual_connection_name = "Your mutual connection"
    mutual_connection_role = ""
    
    if intro_path and len(intro_path) > 1:
        mutual = intro_path[1]
        mutual_connection_name = mutual.get('name', 'Your mutual connection')
        mutual_connection_role = mutual.get('role', '')
    elif mutual_connections:
        mutual = mutual_connections[0]
        mutual_connection_name = mutual.get('name', 'Your mutual connection')
        mutual_connection_role = mutual.get('role', '')
    
    # Format match reasons
    match_highlights = _select_match_highlights(match_factors)
    match_reasons = "\n".join(f"- {reason}" for reason in match_highlights)
    
    # Build context
    context = {
        "founder_name": founder.full_name,
        "founder_company": founder.company or "their company",
        "founder_position": founder.position or "Founder",
        "founder_sectors": ", ".join(founder.sector_focus) if founder.sector_focus else "Technology",
        "founder_stage": ", ".join(founder.stage_focus) if founder.stage_focus else "Early stage",
        "founder_location": founder.location or "N/A",
        
        "investor_name": investor.full_name,
        "investor_company": investor.company or "their firm",
        "investor_position": investor.position or "Investor",
        "investor_thesis": investor.investment_thesis or "Investment focus not specified",
        
        "mutual_connection_name": mutual_connection_name,
        "mutual_connection_role": mutual_connection_role,
        
        "match_score": f"{match_score:.0f}",
        "match_reasons": match_reasons,
        
        "sector_fit": ", ".join(investor.sector_focus) if investor.sector_focus else "Various sectors",
        "stage_fit": ", ".join(investor.stage_focus) if investor.stage_focus else "Various stages",
        "geography_fit": investor.location or "Multiple geographies",
    }
    
    return context


def generate_intro_email(
    founder: Entity,
    investor: Entity,
    match_factors: Dict[str, float],
    match_score: float,
    intro_path: List[Dict],
    mutual_connections: List[Dict],
    tone: str = "formal",
) -> Dict[str, str]:
    """
    Generate a warm introduction email.
    
    Args:
        founder: Founder entity
        investor: Investor entity
        match_factors: Match factor scores
        match_score: Overall match score
        intro_path: Introduction path nodes
        mutual_connections: List of mutual connections
        tone: Email tone (formal, casual, enthusiastic)
    
    Returns:
        Dict with 'subject' and 'body' keys
    """
    if not settings.openai_api_key:
        return {
            "subject": f"Introduction: {founder.full_name} → {investor.full_name}",
            "body": f"Dear {investor.full_name},\n\nI'd like to introduce you to {founder.full_name} from {founder.company}.\n\nBest regards"
        }
    
    # Build context
    context = _build_email_context(
        founder, investor, match_factors, match_score,
        intro_path, mutual_connections
    )
    
    # Select prompt based on tone
    prompt_template = FORMAL_EMAIL_PROMPT
    if tone.lower() == "casual":
        prompt_template = CASUAL_EMAIL_PROMPT
    elif tone.lower() == "enthusiastic":
        prompt_template = ENTHUSIASTIC_EMAIL_PROMPT
    
    # Format prompt with context
    prompt = prompt_template.format(**context)
    
    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": EMAIL_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,  # Higher temperature for natural variation
            max_tokens=800,
        )
        
        raw_content = response.choices[0].message.content.strip()

        # Default subject in case parsing fails
        default_subject = f"Introduction: {founder.full_name} → {investor.full_name}"

        # Extract JSON payload if model wraps it in code fences
        json_payload = raw_content
        if "```json" in raw_content:
            json_payload = raw_content.split("```json", 1)[1].split("```", 1)[0].strip()
        elif "```" in raw_content:
            json_payload = raw_content.split("```", 1)[1].split("```", 1)[0].strip()

        try:
            email_data = json.loads(json_payload)
        except json.JSONDecodeError:
            print("Warning: Failed to parse JSON email response. Returning raw content.")
            email_data = {
                "subject": default_subject,
                "body": raw_content,
            }

        return {
            "subject": email_data.get("subject", default_subject),
            "body": email_data.get("body", raw_content),
        }
        
    except Exception as e:
        print(f"Error generating email: {e}")
        # Fallback email
        return {
            "subject": f"Introduction: {founder.full_name} → {investor.full_name}",
            "body": f"Dear {investor.full_name},\n\nI hope this message finds you well. I wanted to reach out regarding {founder.full_name} from {founder.company}.\n\n"
                   f"Based on your investment focus and their work, I believe this could be a valuable connection. Would you be open to a brief introduction?\n\n"
                   f"Best regards"
        }


def generate_multiple_emails(
    founder: Entity,
    investor: Entity,
    match_factors: Dict[str, float],
    match_score: float,
    intro_path: List[Dict],
    mutual_connections: List[Dict],
    tones: Optional[List[str]] = None,
) -> Dict[str, str]:
    """
    Generate a dictionary of email drafts keyed by tone.

    The logic is intentionally straightforward: loop through the requested tones,
    call `generate_intro_email` once per tone, and keep only the email body because
    the UI currently displays just the draft text.
    """
    if tones is None:
        tones = ["formal", "casual", "enthusiastic"]

    email_drafts: Dict[str, str] = {}

    for tone in tones:
        email = generate_intro_email(
            founder=founder,
            investor=investor,
            match_factors=match_factors,
            match_score=match_score,
            intro_path=intro_path,
            mutual_connections=mutual_connections,
            tone=tone,
        )
        email_drafts[tone] = email["body"]

    return email_drafts
