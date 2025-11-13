"""Graph analysis service for relationship discovery."""
from __future__ import annotations

from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.core.models import Entity
from app.services.neo4j_client import neo4j_client


def get_intro_path(
    source_id: int,
    target_id: int,
    db: Session,
) -> List[Dict]:
    """Get introduction path from source to target entity."""
    path_nodes = neo4j_client.find_intro_path(source_id, target_id, max_depth=3)
    
    if not path_nodes:
        return []

    # Enrich with full entity data from PostgreSQL
    entity_ids = [node["entity_id"] for node in path_nodes]
    entities = db.query(Entity).filter(Entity.id.in_(entity_ids)).all()
    entity_map = {e.id: e for e in entities}

    enriched_path = []
    for node in path_nodes:
        entity_id = node["entity_id"]
        entity = entity_map.get(entity_id)
        if entity:
            enriched_path.append({
                "id": entity.id,
                "name": entity.full_name,
                "company": entity.company,
                "position": entity.position,
                "role": entity.role,
                "linkedin_url": entity.linkedin_url,
            })

    return enriched_path


def get_mutual_connections(
    source_id: int,
    target_id: int,
    db: Session,
) -> List[Dict]:
    """Get mutual connections between two entities."""
    mutual_nodes = neo4j_client.get_mutual_connections(source_id, target_id)
    
    if not mutual_nodes:
        return []

    # Enrich with full entity data
    entity_ids = [node["entity_id"] for node in mutual_nodes]
    entities = db.query(Entity).filter(Entity.id.in_(entity_ids)).all()
    entity_map = {e.id: e for e in entities}

    mutual_connections = []
    for node in mutual_nodes:
        entity_id = node["entity_id"]
        entity = entity_map.get(entity_id)
        if entity:
            mutual_connections.append({
                "id": entity.id,
                "name": entity.full_name,
                "company": entity.company,
                "position": entity.position,
                "role": entity.role,
            })

    return mutual_connections


def calculate_connection_strength(
    source_id: int,
    target_id: int,
    db: Session,
) -> float:
    """
    Calculate connection strength based on:
    - Direct connection: 1.0
    - 2nd degree (1 hop): 0.7
    - 3rd degree (2 hops): 0.4
    - No connection: 0.0
    """
    path = neo4j_client.find_intro_path(source_id, target_id, max_depth=3)
    
    if not path:
        return 0.0
    
    hops = len(path) - 1
    
    if hops == 0:
        return 1.0  # Same person
    elif hops == 1:
        return 1.0  # Direct connection
    elif hops == 2:
        return 0.7  # 2nd degree
    elif hops == 3:
        return 0.4  # 3rd degree
    else:
        return 0.1  # Further degrees


def get_network_stats(db: Session) -> Dict:
    """Get overall network statistics."""
    total = db.query(Entity).count()
    investors = db.query(Entity).filter(Entity.role == "investor").count()
    founders = db.query(Entity).filter(Entity.role == "founder").count()
    enablers = db.query(Entity).filter(Entity.role == "enabler").count()
    others = total - investors - founders - enablers

    return {
        "total_entities": total,
        "investors": investors,
        "founders": founders,
        "enablers": enablers,
        "others": others,
    }

