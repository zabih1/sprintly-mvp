"""Optimized batch processing for large CSV imports using parallel processing and batching."""
from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import BinaryIO, Dict, List, Optional, Tuple

import pandas as pd
from sqlalchemy.orm import Session

from app.core.models import Connection, Entity
from app.services.csv_processor import parse_linkedin_csv
from app.services.enrichment import create_embedding_text, enrich_entity, generate_embedding
from app.services.neo4j_client import neo4j_client

# Global progress tracker
_progress = {
    "total": 0,
    "processed": 0,
    "enriched": 0,
    "embedded": 0,
    "status": "idle",
    "errors": [],
    "start_time": None,
}


def get_progress() -> Dict:
    """Get current processing progress."""
    progress = _progress.copy()
    if progress["start_time"]:
        elapsed = time.time() - progress["start_time"]
        progress["elapsed_seconds"] = round(elapsed, 1)
        if progress["processed"] > 0:
            rate = progress["processed"] / elapsed
            remaining = (progress["total"] - progress["processed"]) / rate if rate > 0 else 0
            progress["estimated_remaining_seconds"] = round(remaining, 1)
    return progress


def reset_progress(total: int):
    """Reset progress tracker."""
    _progress.update({
        "total": total,
        "processed": 0,
        "enriched": 0,
        "embedded": 0,
        "status": "processing",
        "errors": [],
        "start_time": time.time(),
    })


def update_progress(processed: int = 0, enriched: int = 0, embedded: int = 0, error: str = None):
    """Update progress counters."""
    if processed:
        _progress["processed"] += processed
    if enriched:
        _progress["enriched"] += enriched
    if embedded:
        _progress["embedded"] += embedded
    if error:
        _progress["errors"].append(error)


def batch_generate_embeddings(texts: List[str], batch_size: int = 2000) -> List[Optional[List[float]]]:
    """
    Generate embeddings in batches using OpenAI API.
    
    OpenAI supports up to 2048 inputs per request - this is MUCH faster than individual calls.
    For 3000 embeddings: ~30 seconds instead of 30+ minutes!
    """
    import openai
    from app.core.config import settings
    
    if not settings.openai_api_key:
        return [None] * len(texts)
    
    all_embeddings = []
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        try:
            print(f"Generating embeddings batch {i+1}-{min(i+batch_size, len(texts))} of {len(texts)}...")
            response = openai.embeddings.create(
                model="text-embedding-3-large",
                input=batch,
                dimensions=1536,
            )
            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)
            update_progress(embedded=len(batch))
            
        except Exception as e:
            print(f"Error in embedding batch {i}: {e}")
            # Fallback: try smaller batches or individual calls
            for text in batch:
                try:
                    resp = openai.embeddings.create(
                        model="text-embedding-3-large",
                        input=text,
                        dimensions=1536,
                    )
                    all_embeddings.append(resp.data[0].embedding)
                    update_progress(embedded=1)
                except:
                    all_embeddings.append(None)
                    update_progress(error=f"Failed embedding for text: {text[:50]}...")
    
    return all_embeddings


def parallel_enrich_entities(
    entities_info: List[Dict],
    max_workers: int = 10,
    rate_limit_delay: float = 0.1
) -> List[Dict]:
    """
    Enrich entities in parallel using ThreadPoolExecutor.
    
    Uses threading to parallelize API calls while respecting rate limits.
    For 3000 entities: ~5-10 minutes instead of 30+ minutes!
    
    Args:
        entities_info: List of dicts with 'name', 'company', 'position'
        max_workers: Number of parallel threads (default 10)
        rate_limit_delay: Delay between requests to avoid rate limits
    """
    results = [None] * len(entities_info)
    
    def enrich_with_index(idx: int, info: Dict) -> Tuple[int, Dict]:
        """Enrich entity and return with its index."""
        try:
            # Add small delay to avoid rate limits
            time.sleep(rate_limit_delay * (idx % max_workers))
            enrichment = enrich_entity(info['name'], info['company'], info['position'])
            update_progress(enriched=1)
            return idx, enrichment
        except Exception as e:
            print(f"Error enriching {info['name']}: {e}")
            update_progress(error=f"Failed enrichment for {info['name']}: {str(e)[:100]}")
            return idx, {
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
    
    print(f"Starting parallel enrichment with {max_workers} workers...")
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        futures = {
            executor.submit(enrich_with_index, idx, info): idx
            for idx, info in enumerate(entities_info)
        }
        
        # Collect results as they complete
        for future in as_completed(futures):
            try:
                idx, enrichment = future.result()
                results[idx] = enrichment
                
                # Progress update every 100 entities
                if (idx + 1) % 100 == 0:
                    print(f"Enriched {_progress['enriched']}/{len(entities_info)} entities...")
            except Exception as e:
                print(f"Future failed: {e}")
    
    return results


def process_linkedin_csv_fast(
    file_content: bytes,
    db: Session,
    owner_id: int = 1,
    skip_enrichment: bool = False,
    max_workers: int = 10,
) -> Dict[str, int]:
    """
    Fast CSV processing with batch operations and parallel processing.
    
    Optimizations:
    1. Batch embedding generation (2000 at a time)
    2. Parallel enrichment with ThreadPoolExecutor
    3. Batch database commits (every 100 rows)
    4. Progress tracking
    5. Optional skip enrichment for instant import
    
    Performance:
    - With enrichment: ~5-10 minutes for 3000 rows
    - Without enrichment: ~30-60 seconds for 3000 rows
    """
    print("=" * 60)
    print("FAST CSV PROCESSING START")
    print("=" * 60)
    
    # Parse CSV
    print("Parsing CSV...")
    df = parse_linkedin_csv(file_content)
    total_rows = len(df)
    print(f"Found {total_rows} connections")
    
    reset_progress(total_rows)
    
    stats = {
        "total": total_rows,
        "created": 0,
        "skipped": 0,
        "errors": 0,
    }
    
    # Helper function to safely extract string values
    def safe_str(value):
        if value is None or pd.isna(value):
            return None
        val = str(value).strip()
        if val.lower() in ['nan', 'none', '']:
            return None
        return val
    
    # Step 1: Extract basic info and check for duplicates
    print("\nStep 1: Extracting entity information...")
    entities_to_process = []
    existing_entities = {}
    
    for idx, row in df.iterrows():
        first_name = safe_str(row.get('First Name', '')) or ''
        last_name = safe_str(row.get('Last Name', '')) or ''
        full_name = f"{first_name} {last_name}".strip()
        email = safe_str(row.get('Email Address'))
        linkedin_url = safe_str(row.get('URL'))
        company = safe_str(row.get('Company'))
        position = safe_str(row.get('Position'))
        
        # Check if entity already exists
        existing = None
        if email:
            existing = db.query(Entity).filter(Entity.email == email).first()
        if not existing and linkedin_url:
            existing = db.query(Entity).filter(Entity.linkedin_url == linkedin_url).first()
        
        if existing:
            existing_entities[idx] = existing
            stats["skipped"] += 1
        else:
            entities_to_process.append({
                "idx": idx,
                "first_name": first_name,
                "last_name": last_name,
                "full_name": full_name,
                "email": email,
                "linkedin_url": linkedin_url,
                "company": company,
                "position": position,
                "row": row,
            })
    
    print(f"Found {len(existing_entities)} existing entities")
    print(f"Need to process {len(entities_to_process)} new entities")
    
    if len(entities_to_process) == 0:
        print("No new entities to process!")
        _progress["status"] = "completed"
        return stats
    
    # Step 2: Parallel enrichment (if not skipped)
    if skip_enrichment:
        print("\nStep 2: SKIPPING enrichment (fast mode)")
        enrichments = [{
            "role": "other",
            "sector_focus": [],
            "stage_focus": [],
            "check_size_min": None,
            "check_size_max": None,
            "investment_thesis": None,
            "location": None,
            "tags": [],
            "confidence": 0.0,
        }] * len(entities_to_process)
    else:
        print(f"\nStep 2: Parallel enrichment with {max_workers} workers...")
        entities_info = [
            {
                "name": e["full_name"],
                "company": e["company"],
                "position": e["position"],
            }
            for e in entities_to_process
        ]
        enrichments = parallel_enrich_entities(entities_info, max_workers=max_workers)
    
    # Step 3: Create embedding texts and batch generate embeddings
    if skip_enrichment:
        print("\nStep 3: SKIPPING embeddings (fast mode)")
        embeddings = [None] * len(entities_to_process)
    else:
        print("\nStep 3: Batch embedding generation...")
        embedding_texts = []
        for entity, enrichment in zip(entities_to_process, enrichments):
            entity_dict = {
                "full_name": entity["full_name"],
                "company": entity["company"],
                "position": entity["position"],
                "role": enrichment.get("role"),
                "sector_focus": enrichment.get("sector_focus", []),
                "stage_focus": enrichment.get("stage_focus", []),
                "investment_thesis": enrichment.get("investment_thesis"),
                "location": enrichment.get("location"),
            }
            embedding_texts.append(create_embedding_text(entity_dict))
        
        embeddings = batch_generate_embeddings(embedding_texts)
    
    # Step 4: Batch create entities and connections
    print("\nStep 4: Creating entities and connections...")
    new_entities = []
    connections_to_create = []
    neo4j_entities = []
    neo4j_connections = []
    
    BATCH_SIZE = 100
    
    for entity_data, enrichment, embedding in zip(entities_to_process, enrichments, embeddings):
        # Parse connection date
        connected_on = None
        connected_str = safe_str(entity_data["row"].get('Connected On'))
        if connected_str:
            try:
                connected_on = pd.to_datetime(connected_str)
            except:
                pass
        
        # Convert row to dict for raw_data
        raw_data = {}
        for key, value in entity_data["row"].to_dict().items():
            if pd.isna(value):
                raw_data[key] = None
            else:
                raw_data[key] = value
        
        # Create entity
        entity = Entity(
            first_name=entity_data["first_name"],
            last_name=entity_data["last_name"],
            full_name=entity_data["full_name"],
            email=entity_data["email"],
            linkedin_url=entity_data["linkedin_url"],
            company=entity_data["company"],
            position=entity_data["position"],
            connected_on=connected_on,
            role=enrichment.get("role"),
            sector_focus=enrichment.get("sector_focus", []),
            stage_focus=enrichment.get("stage_focus", []),
            location=enrichment.get("location"),
            check_size_min=enrichment.get("check_size_min"),
            check_size_max=enrichment.get("check_size_max"),
            investment_thesis=enrichment.get("investment_thesis"),
            tags=enrichment.get("tags", []),
            embedding=embedding,
            confidence_score=enrichment.get("confidence", 0.0),
            enriched_at=datetime.utcnow() if not skip_enrichment else None,
            raw_data=raw_data,
        )
        
        # Use db.add() instead of appending to list
        # This ensures SQLAlchemy tracks the object and assigns ID after flush
        db.add(entity)
        new_entities.append(entity)
        
        # Commit in batches
        if len(new_entities) % BATCH_SIZE == 0:
            # Flush to get IDs assigned
            db.flush()
            
            # Now IDs are available - collect for Neo4j and create connections
            for e in new_entities:
                neo4j_entities.append({
                    "entity_id": e.id,
                    "name": e.full_name,
                    "role": e.role,
                    "company": e.company,
                    "email": e.email or "",
                    "linkedin_url": e.linkedin_url or "",
                    "position": e.position or "",
                })
                neo4j_connections.append({
                    "source_id": owner_id,
                    "target_id": e.id,
                })
                
                # Create connection in PostgreSQL
                connection = Connection(
                    source_id=owner_id,
                    target_id=e.id,
                    relationship_type="CONNECTED_TO",
                    strength=1.0,
                )
                db.add(connection)
            
            db.commit()
            stats["created"] += len(new_entities)
            update_progress(processed=len(new_entities))
            print(f"Committed batch: {stats['created']}/{len(entities_to_process)} entities")
            new_entities = []
    
    # Final batch commit
    if new_entities:
        # Flush to get IDs assigned
        db.flush()
        
        for e in new_entities:
            neo4j_entities.append({
                "entity_id": e.id,
                "name": e.full_name,
                "role": e.role,
                "company": e.company,
                "email": e.email or "",
                "linkedin_url": e.linkedin_url or "",
                "position": e.position or "",
            })
            neo4j_connections.append({
                "source_id": owner_id,
                "target_id": e.id,
            })
            
            connection = Connection(
                source_id=owner_id,
                target_id=e.id,
                relationship_type="CONNECTED_TO",
                strength=1.0,
            )
            db.add(connection)
        
        db.commit()
        stats["created"] += len(new_entities)
        update_progress(processed=len(new_entities))
        print(f"Final commit: {stats['created']} total entities created")
    
    # Step 5: Batch create Neo4j nodes and relationships
    print("\nStep 5: Creating Neo4j graph...")
    try:
        for neo4j_entity in neo4j_entities:
            neo4j_client.create_entity_node(
                entity_id=neo4j_entity["entity_id"],
                name=neo4j_entity["name"],
                role=neo4j_entity["role"],
                company=neo4j_entity["company"],
                properties={
                    "email": neo4j_entity["email"],
                    "linkedin_url": neo4j_entity["linkedin_url"],
                    "position": neo4j_entity["position"],
                },
            )
        
        for neo4j_conn in neo4j_connections:
            neo4j_client.create_connection(
                source_id=neo4j_conn["source_id"],
                target_id=neo4j_conn["target_id"],
                relationship_type="CONNECTED_TO",
                strength=1.0,
            )
        
        print(f"Created {len(neo4j_entities)} nodes and {len(neo4j_connections)} relationships in Neo4j")
    except Exception as e:
        print(f"Warning: Neo4j operations failed: {e}")
        update_progress(error=f"Neo4j error: {str(e)}")
    
    _progress["status"] = "completed"
    
    print("\n" + "=" * 60)
    print("PROCESSING COMPLETE")
    print(f"Total: {stats['total']}")
    print(f"Created: {stats['created']}")
    print(f"Skipped: {stats['skipped']}")
    print(f"Errors: {len(_progress['errors'])}")
    if _progress["start_time"]:
        elapsed = time.time() - _progress["start_time"]
        print(f"Time: {elapsed:.1f} seconds")
        print(f"Rate: {stats['created']/elapsed:.1f} entities/second")
    print("=" * 60)
    
    return stats

