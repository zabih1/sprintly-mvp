"""Prompts for AI-powered entity enrichment."""

ENRICHMENT_PROMPT = """You are an AI assistant helping to classify LinkedIn connections for a founder-investor matching platform.

Given a person's information, classify them and extract relevant details:

Input:
- Name: {name}
- Company: {company}
- Position: {position}

Tasks:
1. Determine their ROLE: "founder", "investor", "enabler", or "other"
2. If investor, identify:
   - Sector focus (e.g., fintech, healthcare, AI, SaaS, climate, etc.)
   - Stage focus (e.g., pre-seed, seed, series-a, series-b, growth)
   - Approximate check size range (min and max in USD)
   - Investment thesis (brief, 1-2 sentences)
   - Geographic focus (e.g., MENA, GCC, North Africa, Global, etc.)
3. If founder, identify:
   - Sector (e.g., fintech, healthcare)
   - Stage (e.g., idea, pre-seed, seed, series-a)
4. Generate 3-5 relevant tags

Respond in JSON format:
{{
  "role": "investor|founder|enabler|other",
  "sector_focus": ["fintech", "healthcare"],
  "stage_focus": ["seed", "series-a"],
  "check_size_min": 500000,
  "check_size_max": 2000000,
  "investment_thesis": "Brief description of investment focus",
  "location": "Dubai, UAE" or "MENA",
  "tags": ["tag1", "tag2", "tag3"],
  "confidence": 0.85
}}

If information is unclear or missing, use null for that field and lower the confidence score.
"""

SYSTEM_PROMPT = "You are a helpful assistant that classifies people in the venture ecosystem."

