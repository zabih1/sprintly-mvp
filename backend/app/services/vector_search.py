"""Vector similarity search using pgvector."""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.services.enrichment import generate_embedding
from app.services.match_scorer import rank_matches
from app.core.models import Entity


def search_similar_entities(
    query: str,
    db: Session,
    role_filter: Optional[str] = None,
    sector_filter: Optional[str] = None,
    stage_filter: Optional[str] = None,
    location_filter: Optional[str] = None,
    limit: int = 10,
) -> List[Tuple[Entity, float]]:
    """
    Search for entities similar to the query using vector similarity.
    
    Returns list of (Entity, distance) tuples sorted by similarity.
    """
    # Generate embedding for query
    query_embedding = generate_embedding(query)
    if not query_embedding:
        return []

    # Build base query
    query_obj = db.query(
        Entity,
        Entity.embedding.cosine_distance(query_embedding).label("distance")
    ).filter(
        Entity.embedding.isnot(None)
    )

    # Apply filters
    if role_filter and role_filter.lower() != "all":
        query_obj = query_obj.filter(Entity.role == role_filter.lower())

    if sector_filter and sector_filter.lower() != "all":
        query_obj = query_obj.filter(
            func.array_to_string(Entity.sector_focus, ',').ilike(f'%{sector_filter}%')
        )

    if stage_filter and stage_filter.lower() != "all":
        query_obj = query_obj.filter(
            func.array_to_string(Entity.stage_focus, ',').ilike(f'%{stage_filter}%')
        )

    if location_filter and location_filter.lower() != "all":
        query_obj = query_obj.filter(
            Entity.location.ilike(f'%{location_filter}%')
        )

    # Order by similarity and limit
    results = query_obj.order_by(text("distance ASC")).limit(limit).all()

    return [(entity, distance) for entity, distance in results]


def find_investors_by_criteria(
    db: Session,
    sector: Optional[str] = None,
    stage: Optional[str] = None,
    location: Optional[str] = None,
    min_check_size: Optional[int] = None,
    max_check_size: Optional[int] = None,
    limit: int = 20,
) -> List[Entity]:
    """Find investors matching specific criteria."""
    query = db.query(Entity).filter(Entity.role == "investor")

    if sector:
        query = query.filter(
            func.array_to_string(Entity.sector_focus, ',').ilike(f'%{sector}%')
        )

    if stage:
        query = query.filter(
            func.array_to_string(Entity.stage_focus, ',').ilike(f'%{stage}%')
        )

    if location:
        query = query.filter(Entity.location.ilike(f'%{location}%'))

    if min_check_size:
        query = query.filter(
            (Entity.check_size_min <= min_check_size) | (Entity.check_size_min.is_(None))
        )

    if max_check_size:
        query = query.filter(
            (Entity.check_size_max >= max_check_size) | (Entity.check_size_max.is_(None))
        )

    return query.limit(limit).all()


def hybrid_search(
    query: str,
    db: Session,
    role_filter: Optional[str] = None,
    sector_filter: Optional[str] = None,
    stage_filter: Optional[str] = None,
    location_filter: Optional[str] = None,
    limit: int = 10,
) -> List[Dict]:
    """
    Hybrid search combining vector similarity and keyword matching.
    
    Returns list of dicts with comprehensive match scoring and factors.
    """
    # Get vector similarity results
    vector_results = search_similar_entities(
        query=query,
        db=db,
        role_filter=role_filter,
        sector_filter=sector_filter,
        stage_filter=stage_filter,
        location_filter=location_filter,
        limit=limit * 2,  # Get more candidates
    )

    # Build initial results with reasons
    initial_results = []
    query_lower = query.lower()
    query_tokens = set(query_lower.split())

    for entity, distance in vector_results:
        similarity_score = 1.0 - distance  # Convert distance to similarity
        reasons = []

        # Identify match reasons
        if entity.sector_focus:
            for sector in entity.sector_focus:
                if any(token in sector.lower() for token in query_tokens):
                    reasons.append(f"Sector focus: {sector}")

        if entity.stage_focus:
            for stage in entity.stage_focus:
                if any(token in stage.lower() for token in query_tokens):
                    reasons.append(f"Stage: {stage}")

        if entity.location:
            if any(token in entity.location.lower() for token in query_tokens):
                reasons.append(f"Location: {entity.location}")

        # Add investment thesis to reasons if available
        if entity.investment_thesis and len(reasons) < 3:
            reasons.append(f"Thesis: {entity.investment_thesis[:100]}...")

        # Add company info
        if entity.company and len(reasons) < 4:
            reasons.append(f"Company: {entity.company}")

        initial_results.append((entity, similarity_score, reasons[:4]))

    # Use match scorer to calculate comprehensive scores and rank
    ranked_results = rank_matches(initial_results, query)

    return ranked_results[:limit]

