"""AI-powered enrichment using OpenAI for entity classification and tagging."""
from __future__ import annotations

import json
from typing import Dict, List, Optional

import openai

from app.core.config import settings
from app.core.logging_config import get_logger, log_api_call, log_error_with_context
from app.services.prompts import ENRICHMENT_PROMPT, SYSTEM_PROMPT

# Initialize OpenAI client
openai.api_key = settings.openai_api_key

logger = get_logger(__name__)


def generate_embedding(text: str) -> Optional[List[float]]:
    """Generate embedding vector for text using OpenAI."""
    if not settings.openai_api_key:
        logger.warning("No OpenAI API key configured - skipping embedding generation")
        return None

    try:
        response = openai.embeddings.create(
            model="text-embedding-3-large",
            input=text,
            dimensions=1536,
        )
        log_api_call(logger, "OpenAI", "embeddings.create",
                    model="text-embedding-3-large", text_length=len(text), status="success")
        return response.data[0].embedding
    except Exception as e:
        log_error_with_context(logger, e, "Generate embedding", text_length=len(text))
        return None


def enrich_entity(
    name: str,
    company: Optional[str],
    position: Optional[str],
) -> Dict:
    """Enrich entity using LLM to extract investor/founder attributes."""
    if not settings.openai_api_key:
        logger.warning("No OpenAI API key configured - skipping enrichment")
        return {
            "role": "other",
            "sector_focus": [],
            "stage_focus": [],
            "check_size_min": None,
            "check_size_max": None,
            "investment_thesis": None,
            "location": None,
            "tags": [],
            "confidence": 0.0,
        }

    try:
        prompt = ENRICHMENT_PROMPT.format(
            name=name,
            company=company or "Unknown",
            position=position or "Unknown",
        )

        logger.debug(f"Enriching entity | Name: {name} | Company: {company} | Position: {position}")
        
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=500,
        )
        
        log_api_call(logger, "OpenAI", "chat.completions.create",
                    model="gpt-4o-mini", entity=name, status="success")
        
        content = response.choices[0].message.content
        # Try to parse JSON from the response
        # Sometimes the model wraps it in markdown code blocks
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        data = json.loads(content)
        logger.debug(f"Entity enriched | Name: {name} | Role: {data.get('role', 'unknown')}")
        return data

    except Exception as e:
        log_error_with_context(logger, e, "Enrich entity", name=name, company=company, position=position)
        return {
            "role": "other",
            "sector_focus": [],
            "stage_focus": [],
            "check_size_min": None,
            "check_size_max": None,
            "investment_thesis": None,
            "location": None,
            "tags": [],
            "confidence": 0.0,
        }


def create_embedding_text(entity_dict: Dict) -> str:
    """Create a text representation for embedding generation."""
    parts = []
    
    if entity_dict.get("full_name"):
        parts.append(f"Name: {entity_dict['full_name']}")
    
    if entity_dict.get("company"):
        parts.append(f"Company: {entity_dict['company']}")
    
    if entity_dict.get("position"):
        parts.append(f"Position: {entity_dict['position']}")
    
    if entity_dict.get("role"):
        parts.append(f"Role: {entity_dict['role']}")
    
    if entity_dict.get("sector_focus"):
        parts.append(f"Sectors: {', '.join(entity_dict['sector_focus'])}")
    
    if entity_dict.get("stage_focus"):
        parts.append(f"Stages: {', '.join(entity_dict['stage_focus'])}")
    
    if entity_dict.get("investment_thesis"):
        parts.append(f"Thesis: {entity_dict['investment_thesis']}")
    
    if entity_dict.get("location"):
        parts.append(f"Location: {entity_dict['location']}")
    
    return " | ".join(parts)

