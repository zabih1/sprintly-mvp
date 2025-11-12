"""Main FastAPI application."""
from __future__ import annotations

from typing import Dict, List, Optional

from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .config import settings
from .csv_processor import process_linkedin_csv
from .database import get_db, init_db
from .graph_service import (
    calculate_connection_strength,
    get_intro_path,
    get_mutual_connections,
    get_network_stats,
)
from .match_scorer import calculate_match_factors, calculate_overall_match_score
from .models import Entity
from .neo4j_client import neo4j_client
from .vector_search import hybrid_search

# Initialize FastAPI app
app = FastAPI(
    title="Sprintly Investor Match MVP",
    description="AI-powered founder-investor matching with knowledge graph",
    version="1.0.0",
)

# CORS middleware - allow all origins for MVP (including file:// protocol)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins including file://
    allow_credentials=False,  # Must be False when allow_origins is "*"
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    try:
        init_db()
        print("✓ Database initialized successfully")
    except Exception as e:
        print(f"✗ Database initialization failed: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    neo4j_client.close()


@app.get("/health")
def health_check() -> Dict:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "database": "connected",
        "neo4j": "connected" if neo4j_client.driver else "disconnected",
    }


@app.post("/upload")
async def upload_connections(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> Dict:
    """
    Upload LinkedIn connections CSV file.
    
    Expected columns:
    - First Name
    - Last Name
    - URL (LinkedIn profile URL)
    - Email Address
    - Company
    - Position
    - Connected On
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")

    try:
        # Read file content
        content = await file.read()
        
        # Process CSV
        stats = process_linkedin_csv(content, db, owner_id=1)
        
        return {
            "message": "File processed successfully",
            "stats": stats,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@app.get("/entities")
def list_entities(
    role: Optional[str] = Query(None, description="Filter by role: investor, founder, enabler"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> Dict:
    """List all entities with optional role filter."""
    query = db.query(Entity)
    
    if role and role.lower() != "all":
        query = query.filter(Entity.role == role.lower())
    
    entities = query.limit(limit).all()
    
    return {
        "count": len(entities),
        "entities": [
            {
                "id": e.id,
                "name": e.full_name,
                "email": e.email,
                "company": e.company,
                "position": e.position,
                "role": e.role,
                "sector_focus": e.sector_focus,
                "stage_focus": e.stage_focus,
                "location": e.location,
                "linkedin_url": e.linkedin_url,
            }
            for e in entities
        ],
    }


@app.get("/investors")
def list_investors(
    sector: Optional[str] = Query(None, description="Filter by sector"),
    stage: Optional[str] = Query(None, description="Filter by stage"),
    location: Optional[str] = Query(None, description="Filter by location"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> Dict:
    """List investors with optional filters and comprehensive scoring."""
    query = db.query(Entity).filter(Entity.role == "investor")
    
    if sector:
        from sqlalchemy import func
        query = query.filter(
            func.array_to_string(Entity.sector_focus, ',').ilike(f'%{sector}%')
        )
    
    if stage:
        from sqlalchemy import func
        query = query.filter(
            func.array_to_string(Entity.stage_focus, ',').ilike(f'%{stage}%')
        )
    
    if location:
        query = query.filter(Entity.location.ilike(f'%{location}%'))
    
    investors = query.limit(limit).all()
    
    # Calculate match scores and factors for each investor
    scored_investors = []
    for inv in investors:
        # Calculate match factors
        match_factors = calculate_match_factors(inv, query="")
        
        # Calculate overall score (without query, use default scoring)
        overall_score = calculate_overall_match_score(inv, query="", similarity_score=0.8)
        
        # Get intro path
        intro_path = []
        try:
            intro_path = get_intro_path(1, inv.id, db)
        except:
            pass
        
        scored_investors.append({
            "id": inv.id,
            "name": inv.full_name,
            "company": inv.company,
            "position": inv.position,
            "linkedin_url": inv.linkedin_url,
            "email": inv.email,
            "role": inv.role,
            "sector_focus": inv.sector_focus,
            "stage_focus": inv.stage_focus,
            "location": inv.location,
            "check_size_min": inv.check_size_min,
            "check_size_max": inv.check_size_max,
            "investment_thesis": inv.investment_thesis,
            "tags": inv.tags,
            "score": overall_score,
            "match_factors": match_factors,
            "intro_path": intro_path,
            "confidence_score": inv.confidence_score,
        })
    
    # Sort by score descending
    scored_investors.sort(key=lambda x: x['score'], reverse=True)
    
    return {
        "count": len(scored_investors),
        "investors": scored_investors,
    }


@app.get("/search")
def search_investors(
    q: str = Query(..., description="Search query (e.g., 'fintech seed MENA')"),
    role: Optional[str] = Query("investor", description="Role filter"),
    sector: Optional[str] = Query(None, description="Sector filter"),
    stage: Optional[str] = Query(None, description="Stage filter"),
    location: Optional[str] = Query(None, description="Location filter"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
) -> Dict:
    """
    Search for investors using hybrid vector + keyword search with comprehensive scoring.
    """
    # Get ranked matches with comprehensive scoring from Python
    results = hybrid_search(
        query=q,
        db=db,
        role_filter=role,
        sector_filter=sector,
        stage_filter=stage,
        location_filter=location,
        limit=limit,
    )
    
    # Enrich with intro paths
    matches = []
    for match_data in results:
        # Calculate intro path if available
        intro_path = []
        connection_strength = 0.0
        
        try:
            # Assuming owner_id = 1 (the user who uploaded connections)
            intro_path = get_intro_path(1, match_data['id'], db)
            connection_strength = calculate_connection_strength(1, match_data['id'], db)
        except:
            pass
        
        # Add intro path to match data
        match_data['intro_path'] = intro_path
        match_data['connection_strength'] = connection_strength
        matches.append(match_data)
    
    return {
        "query": q,
        "filters": {
            "role": role,
            "sector": sector,
            "stage": stage,
            "location": location,
        },
        "count": len(matches),
        "matches": matches,
    }


@app.get("/intro-path/{target_id}")
def get_introduction_path(
    target_id: int,
    source_id: int = Query(1, description="Source entity ID (default: owner)"),
    db: Session = Depends(get_db),
) -> Dict:
    """Get introduction path from source to target entity."""
    path = get_intro_path(source_id, target_id, db)
    mutual = get_mutual_connections(source_id, target_id, db)
    strength = calculate_connection_strength(source_id, target_id, db)
    
    return {
        "source_id": source_id,
        "target_id": target_id,
        "intro_path": path,
        "mutual_connections": mutual,
        "connection_strength": strength,
    }


@app.get("/stats")
def get_stats(db: Session = Depends(get_db)) -> Dict:
    """Get network statistics."""
    return get_network_stats(db)


@app.delete("/entities/{entity_id}")
def delete_entity(
    entity_id: int,
    db: Session = Depends(get_db),
) -> Dict:
    """Delete an entity."""
    entity = db.query(Entity).filter(Entity.id == entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    db.delete(entity)
    db.commit()
    
    return {"message": "Entity deleted successfully"}


@app.post("/clear-data")
def clear_all_data(
    confirm: str = Query(..., description="Type 'DELETE' to confirm"),
    db: Session = Depends(get_db),
) -> Dict:
    """Clear all data from database and graph (use with caution!)."""
    if confirm != "DELETE":
        raise HTTPException(status_code=400, detail="Confirmation required")
    
    # Clear PostgreSQL
    db.query(Entity).delete()
    db.commit()
    
    # Clear Neo4j
    neo4j_client.clear_graph()
    
    return {"message": "All data cleared successfully"}


def _score_to_label(score: float) -> str:
    """Convert score to human-readable label."""
    if score >= 80:
        return "Excellent match"
    elif score >= 65:
        return "Good match"
    elif score >= 50:
        return "Potential match"
    else:
        return "Consider"
