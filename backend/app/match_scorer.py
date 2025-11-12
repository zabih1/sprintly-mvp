"""Match scoring and ranking system for investor-founder matching."""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from .models import Entity


def calculate_sector_match(
    entity: Entity,
    query: str,
    query_tokens: set
) -> Tuple[float, bool]:
    """
    Calculate sector match score (0-100).
    
    Returns (score, has_match).
    """
    if not entity.sector_focus or not entity.sector_focus:
        return 0.0, False
    
    score = 0.0
    has_match = False
    
    # Check for exact matches in sectors
    for sector in entity.sector_focus:
        sector_lower = sector.lower()
        
        # Exact sector in query
        if sector_lower in query.lower():
            score = 100.0
            has_match = True
            break
        
        # Token matches
        sector_tokens = set(sector_lower.split())
        matching_tokens = query_tokens.intersection(sector_tokens)
        
        if matching_tokens:
            # Calculate score based on match ratio
            match_ratio = len(matching_tokens) / len(sector_tokens)
            token_score = 70 + (match_ratio * 30)  # 70-100 range
            score = max(score, token_score)
            has_match = True
    
    # Base score if has sectors but no query match
    if not has_match and entity.sector_focus:
        score = 60.0
        has_match = True
    
    return score, has_match


def calculate_stage_match(
    entity: Entity,
    query: str,
    query_tokens: set
) -> Tuple[float, bool]:
    """
    Calculate stage alignment score (0-100).
    
    Returns (score, has_match).
    """
    if not entity.stage_focus or not entity.stage_focus:
        return 0.0, False
    
    score = 0.0
    has_match = False
    
    # Common stage keywords
    stage_keywords = {
        'pre-seed': ['pre-seed', 'preseed', 'pre seed'],
        'seed': ['seed'],
        'series-a': ['series a', 'series-a', 'seriesa', 'series a'],
        'series-b': ['series b', 'series-b', 'seriesb', 'series b'],
        'growth': ['growth', 'late stage', 'late-stage']
    }
    
    query_lower = query.lower()
    
    for stage in entity.stage_focus:
        stage_lower = stage.lower()
        
        # Exact match
        if stage_lower in query_lower or query_lower in stage_lower:
            score = 100.0
            has_match = True
            break
        
        # Check synonyms
        for stage_type, keywords in stage_keywords.items():
            if any(kw in stage_lower for kw in keywords):
                if any(kw in query_lower for kw in keywords):
                    score = 95.0
                    has_match = True
                    break
        
        if has_match:
            break
        
        # Token matches
        stage_tokens = set(stage_lower.split())
        matching_tokens = query_tokens.intersection(stage_tokens)
        
        if matching_tokens:
            score = max(score, 75.0)
            has_match = True
    
    # Base score if has stages but no query match
    if not has_match and entity.stage_focus:
        score = 65.0
        has_match = True
    
    return score, has_match

def calculate_geography_match(
    entity: Entity,
    query: str,
    query_tokens: set
) -> Tuple[float, bool]:
    """
    Calculate geography fit score (0-100).
    
    Returns (score, has_match).
    """
    if not entity.location:
        return 0.0, False
    
    location_lower = entity.location.lower()
    query_lower = query.lower()
    
    # Geographic regions and their keywords
    geo_keywords = {
        'mena': ['mena', 'middle east', 'north africa'],
        'gcc': ['gcc', 'gulf', 'gulf cooperation council'],
        'dubai': ['dubai', 'uae', 'emirates'],
        'riyadh': ['riyadh', 'saudi', 'ksa', 'saudi arabia'],
        'egypt': ['egypt', 'cairo'],
        'us': ['usa', 'us', 'united states', 'america'],
        'uk': ['uk', 'united kingdom', 'london', 'britain'],
        'europe': ['europe', 'eu', 'european']
    }
    
    score = 0.0
    has_match = False
    
    # Exact location match
    if location_lower in query_lower or query_lower in location_lower:
        score = 100.0
        has_match = True
    else:
        # Check for regional matches
        for region, keywords in geo_keywords.items():
            location_match = any(kw in location_lower for kw in keywords)
            query_match = any(kw in query_lower for kw in keywords)
            
            if location_match and query_match:
                score = 95.0
                has_match = True
                break
        
        # Token matches
        if not has_match:
            location_tokens = set(location_lower.split())
            matching_tokens = query_tokens.intersection(location_tokens)
            
            if matching_tokens:
                score = 80.0
                has_match = True
    
    # Base score if has location but no query match
    if not has_match:
        score = 70.0
        has_match = True
    
    return score, has_match


def calculate_check_size_match(
    entity: Entity,
    query: str
) -> Tuple[float, bool]:
    """
    Calculate check size fit score (0-100).
    
    Returns (score, has_match).
    """
    if not entity.check_size_min and not entity.check_size_max:
        return 0.0, False
    
    # Look for check size indicators in query
    # For now, give a base score if check size is defined
    score = 75.0
    has_match = True
    
    # Could be enhanced to parse amounts from query
    # e.g., "500k seed round" -> check if investor's range matches
    
    return score, has_match


def calculate_match_factors(
    entity: Entity,
    query: str = ""
) -> Dict[str, float]:
    """
    Calculate all match factors for an entity.
    
    Returns dict with factor names and scores (0-100).
    """
    query_lower = query.lower()
    query_tokens = set(query_lower.split())
    
    factors = {}
    
    # Sector match
    sector_score, has_sector = calculate_sector_match(entity, query, query_tokens)
    if has_sector:
        factors['sector'] = round(sector_score, 1)
    
    # Stage alignment
    stage_score, has_stage = calculate_stage_match(entity, query, query_tokens)
    if has_stage:
        factors['stage'] = round(stage_score, 1)
    
    # Geography fit
    geo_score, has_geo = calculate_geography_match(entity, query, query_tokens)
    if has_geo:
        factors['geography'] = round(geo_score, 1)
    
    # Check size fit
    check_score, has_check = calculate_check_size_match(entity, query)
    if has_check:
        factors['checkSize'] = round(check_score, 1)
    
    return factors


def calculate_overall_match_score(
    entity: Entity,
    query: str = "",
    similarity_score: float = 0.0
) -> float:
    """
    Calculate overall match score (0-100).
    
    Combines:
    - Vector similarity score (base)
    - Individual factor scores (weighted per requirements)
    
    Requirements-aligned weights (Section 6.5):
    - Sector Match: 35%
    - Stage Alignment: 20%
    - Geography Fit: 15%
    - Check Size: 10%
    - Traction Signals: 10%
    - Graph Proximity: 10%
    """
    # Convert similarity to percentage (0-1 -> 0-100)
    base_score = similarity_score * 100
    
    # Get factor scores
    factors = calculate_match_factors(entity, query)
    
    if not factors:
        return round(base_score, 1)
    
    # Weight factors per requirements (Section 6.5)
    factor_weights = {
        'sector': 0.35,          # 35% weight (Sector Match)
        'stage': 0.20,           # 20% weight (Stage Alignment)
        'geography': 0.15,       # 15% weight (Geography Fit)
        'checkSize': 0.10,       # 10% weight (Check Size)
        'traction': 0.10,        # 10% weight (Traction Signals - base score for MVP)
        'graph_proximity': 0.10  # 10% weight (Graph Proximity - base score for MVP)
    }
    # Add default scores for traction and graph proximity (MVP baseline)
    if 'traction' not in factors:
        factors['traction'] = 70.0  # Base traction score for MVP
    if 'graph_proximity' not in factors:
        factors['graph_proximity'] = 75.0  # Base graph proximity score for MVP
    
    # Calculate weighted factor score
    weighted_factor_score = 0.0
    total_weight = 0.0
    
    for factor_name, score in factors.items():
        weight = factor_weights.get(factor_name, 0.0)
        weighted_factor_score += score * weight
        total_weight += weight
    
    if total_weight > 0:
        factor_score = weighted_factor_score / total_weight
    else:
        factor_score = 0.0
    
    # Combine base similarity (40%) + factors (60%)
    final_score = (base_score * 0.4) + (factor_score * 0.6)
    
    # Ensure score is in valid range
    final_score = max(0.0, min(100.0, final_score))
    
    return round(final_score, 1)


def rank_matches(
    entities_with_scores: List[Tuple[Entity, float, List[str]]],
    query: str = ""
) -> List[Dict]:
    """
    Rank and enrich match results with comprehensive scoring.
    
    Args:
        entities_with_scores: List of (Entity, similarity_score, reasons) tuples
        query: Search query string
    
    Returns:
        List of dicts with entity data, scores, and factors
    """
    ranked_matches = []
    
    for entity, similarity_score, reasons in entities_with_scores:
        # Calculate overall match score
        overall_score = calculate_overall_match_score(entity, query, similarity_score)
        
        # Calculate individual factors
        match_factors = calculate_match_factors(entity, query)
        
        # Build match data
        match_data = {
            'id': entity.id,
            'name': entity.full_name or f"{entity.first_name} {entity.last_name}",
            'company': entity.company,
            'position': entity.position,
            'linkedin_url': entity.linkedin_url,
            'email': entity.email,
            'role': entity.role,
            'sector_focus': entity.sector_focus,
            'stage_focus': entity.stage_focus,
            'location': entity.location,
            'check_size_min': entity.check_size_min,
            'check_size_max': entity.check_size_max,
            'investment_thesis': entity.investment_thesis,
            'tags': entity.tags,
            'score': overall_score,
            'similarity_score': round(similarity_score, 3),
            'match_factors': match_factors,
            'reasons': reasons,
            'confidence_score': entity.confidence_score
        }
        
        ranked_matches.append(match_data)
    
    # Sort by overall score (descending)
    ranked_matches.sort(key=lambda x: x['score'], reverse=True)
    
    return ranked_matches

