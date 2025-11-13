"""Main FastAPI application with all endpoints."""
from __future__ import annotations

from typing import Optional

from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func
from sqlalchemy.orm import Session

# Import from core (database, models, config)
from app.core.database import get_db, init_db
from app.core.models import Entity

# Import from services (business logic)
from app.services.batch_processor import get_progress, process_linkedin_csv_fast
from app.services.email_generator import generate_multiple_emails
from app.services.graph_service import (
    calculate_connection_strength,
    get_intro_path,
    get_mutual_connections,
    get_network_stats,
)
from app.services.match_scorer import (
    calculate_match_factors,
    calculate_overall_match_score,
)
from app.services.neo4j_client import neo4j_client
from app.services.vector_search import hybrid_search

# Import schemas (for type validation)
from app.api.schemas.email import EmailGenerationResponse, EmailTone
from app.api.schemas.entity import EntityListResponse, EntityResponse
from app.api.schemas.intro import IntroPathResponse
from app.api.schemas.investor import InvestorListResponse, InvestorResponse
from app.api.schemas.search import MatchResult, SearchFilters, SearchResponse
from app.api.schemas.stats import NetworkStatsResponse
from app.api.schemas.upload import UploadResponse, UploadStats

# Initialize FastAPI app
app = FastAPI(
    title="Sprintly Investor Match MVP",
    description="AI-powered founder-investor matching with knowledge graph",
    version="1.0.0",
)

# CORS middleware - allow all origins for MVP
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
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
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "database": "connected",
        "neo4j": "connected" if neo4j_client.driver else "disconnected",
    }


@app.delete("/clear-all-data")
def clear_all_data(
    db: Session = Depends(get_db),
):
    """
    Delete all data from database and Neo4j graph.
    
    This will permanently delete:
    - All entities (founders, investors, enablers)
    - All connections
    - All match history
    - All Neo4j nodes and relationships
    """
    try:
        # Get counts before deletion
        from app.core.models import Connection, MatchHistory
        
        entity_count = db.query(Entity).count()
        connection_count = db.query(Connection).count()
        match_count = db.query(MatchHistory).count()
        
        print(f"Deleting {entity_count} entities, {connection_count} connections, {match_count} matches...")
        
        # Delete from PostgreSQL (order matters due to foreign keys)
        db.query(MatchHistory).delete()
        db.query(Connection).delete()
        db.query(Entity).delete()
        db.commit()
        
        print("✓ PostgreSQL data deleted")
        
        # Clear Neo4j graph
        try:
            neo4j_client.driver.execute_query(
                "MATCH (n) DETACH DELETE n"
            )
            print("✓ Neo4j graph cleared")
        except Exception as e:
            print(f"Warning: Could not clear Neo4j: {e}")
        
        return {
            "success": True,
            "message": "All data deleted successfully",
            "deleted": {
                "entities": entity_count,
                "connections": connection_count,
                "matches": match_count,
                "neo4j": "cleared"
            }
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear data: {str(e)}"
        )


@app.post("/upload-fast", response_model=UploadResponse)
async def upload_connections_fast(
    file: UploadFile = File(...),
    skip_enrichment: bool = Query(False, description="Skip AI enrichment for instant import (add enrichment later)"),
    max_workers: int = Query(10, ge=1, le=20, description="Number of parallel workers for enrichment (1-20)"),
    db: Session = Depends(get_db),
):
    """
    FAST upload for large CSV files (1000+ connections) - RECOMMENDED!
    
    Optimizations:
    - Batch embedding generation (2000 at a time) - 50x faster
    - Parallel enrichment with ThreadPoolExecutor - 10x faster
    - Batch database operations - 5x faster
    - Progress tracking at /upload-progress
    
    Performance for 3000 connections:
    - With enrichment (skip_enrichment=false): ~5-10 minutes
    - Without enrichment (skip_enrichment=true): ~30-60 seconds
    
    Parameters:
    - skip_enrichment: Set to true for instant import, enrich later
    - max_workers: More workers = faster, but may hit API rate limits (default 10)
    
    Expected columns:
    - First Name, Last Name, URL, Email Address, Company, Position, Connected On
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")

    try:
        content = await file.read()
        stats = process_linkedin_csv_fast(
            content, 
            db, 
            owner_id=1,
            skip_enrichment=skip_enrichment,
            max_workers=max_workers,
        )
        
        message = "File processed successfully"
        if skip_enrichment:
            message += " (enrichment skipped - use /enrich-pending to add AI data later)"
        
        return UploadResponse(
            message=message,
            stats=UploadStats(**stats)
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fast processing failed: {str(e)}")


@app.get("/upload-progress")
def get_upload_progress():
    """
    Get current upload/processing progress.
    
    Use this endpoint while /upload-fast is running to track progress.
    
    Returns:
    - total: Total entities to process
    - processed: Entities processed so far
    - enriched: Entities enriched (AI analysis done)
    - embedded: Entities embedded (vector embeddings generated)
    - status: Current status (idle, processing, completed, error)
    - elapsed_seconds: Time elapsed since start
    - estimated_remaining_seconds: Estimated time remaining
    - errors: List of error messages (if any)
    """
    return get_progress()


@app.get("/entities", response_model=EntityListResponse)
def list_entities(
    role: Optional[str] = Query(None, description="Filter by role: investor, founder, enabler"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """List all entities with optional role filter."""
    query = db.query(Entity)
    
    if role and role.lower() != "all":
        query = query.filter(Entity.role == role.lower())
    
    entities = query.limit(limit).all()

    entity_responses = []
    for entity in entities:
        entity_responses.append(
            EntityResponse(
                id=entity.id,
                name=entity.full_name,
                email=entity.email,
                company=entity.company,
                position=entity.position,
                role=entity.role,
                sector_focus=entity.sector_focus,
                stage_focus=entity.stage_focus,
                location=entity.location,
                linkedin_url=entity.linkedin_url,
            )
        )

    return EntityListResponse(count=len(entity_responses), entities=entity_responses)


@app.get("/investors", response_model=InvestorListResponse)
def list_investors(
    sector: Optional[str] = Query(None, description="Filter by sector"),
    stage: Optional[str] = Query(None, description="Filter by stage"),
    location: Optional[str] = Query(None, description="Filter by location"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List investors with optional filters and comprehensive scoring."""
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
    
    investors = query.limit(limit).all()
    
    # Calculate match scores and factors for each investor
    scored_investors = []
    for inv in investors:
        match_factors = calculate_match_factors(inv, query="")
        overall_score = calculate_overall_match_score(inv, query="", similarity_score=0.8)
        
        # Get intro path
        intro_path = []
        try:
            intro_path_data = get_intro_path(1, inv.id, db)
            intro_path = []
            for node in intro_path_data:
                intro_path.append(
                    {
                        "id": node["id"],
                        "name": node["name"],
                        "company": node.get("company"),
                        "position": node.get("position"),
                        "role": node.get("role"),
                        "linkedin_url": node.get("linkedin_url"),
                    }
                )
        except Exception:
            pass
        
        scored_investors.append(
            InvestorResponse(
                id=inv.id,
                name=inv.full_name,
                company=inv.company,
                position=inv.position,
                linkedin_url=inv.linkedin_url,
                email=inv.email,
                role=inv.role,
                sector_focus=inv.sector_focus,
                stage_focus=inv.stage_focus,
                location=inv.location,
                check_size_min=inv.check_size_min,
                check_size_max=inv.check_size_max,
                investment_thesis=inv.investment_thesis,
                tags=inv.tags,
                score=overall_score,
                match_factors=match_factors,
                intro_path=intro_path,
                confidence_score=inv.confidence_score,
            )
        )
    
    scored_investors.sort(key=lambda x: x.score, reverse=True)
    
    return InvestorListResponse(count=len(scored_investors), investors=scored_investors)


@app.get("/search", response_model=SearchResponse)
def search_investors(
    q: str = Query(..., description="Search query (e.g., 'fintech seed MENA')"),
    role: Optional[str] = Query("investor", description="Role filter"),
    sector: Optional[str] = Query(None, description="Sector filter"),
    stage: Optional[str] = Query(None, description="Stage filter"),
    location: Optional[str] = Query(None, description="Location filter"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Search for investors using hybrid vector + keyword search."""
    results = hybrid_search(
        query=q,
        db=db,
        role_filter=role,
        sector_filter=sector,
        stage_filter=stage,
        location_filter=location,
        limit=limit,
    )
    
    # Enrich with intro paths and enhanced reasons
    matches = []
    for match_data in results:
        intro_path = []
        connection_strength = 0.0
        mutual_count = 0
        
        try:
            intro_path_data = get_intro_path(1, match_data['id'], db)
            mutual_data = get_mutual_connections(1, match_data['id'], db)
            mutual_count = len(mutual_data)
            
            intro_path = []
            for node in intro_path_data:
                intro_path.append(
                    {
                        "id": node["id"],
                        "name": node["name"],
                        "company": node.get("company"),
                        "position": node.get("position"),
                        "role": node.get("role"),
                        "linkedin_url": node.get("linkedin_url"),
                    }
                )
            connection_strength = calculate_connection_strength(1, match_data['id'], db)
        except Exception:
            pass
        
        # Enhance reasons with natural language explanations
        enhanced_reasons = []
        match_factors = match_data.get('match_factors', {})
        
        # Sector match
        if match_factors.get('sector', 0) >= 70:
            if match_data.get('sector_focus'):
                sectors = ', '.join(match_data['sector_focus'][:2])
                enhanced_reasons.append(f"✓ Invests in {sectors}")
        
        # Stage match
        if match_factors.get('stage', 0) >= 65:
            if match_data.get('stage_focus'):
                stages = ', '.join(match_data['stage_focus'][:2])
                enhanced_reasons.append(f"✓ Targets {stages} stage companies")
        
        # Geography match
        if match_factors.get('geography', 0) >= 70:
            if match_data.get('location'):
                enhanced_reasons.append(f"✓ Active in {match_data['location']}")
        
        # Mutual connections
        if mutual_count > 0:
            conn_word = "connection" if mutual_count == 1 else "connections"
            enhanced_reasons.append(f"✓ {mutual_count} mutual {conn_word}")
        
        # Check size fit
        if match_data.get('check_size_min') and match_data.get('check_size_max'):
            min_k = match_data['check_size_min'] // 1000
            max_m = match_data['check_size_max'] / 1000000
            enhanced_reasons.append(f"✓ Check size: ${min_k}K-${max_m:.1f}M")
        
        # Use enhanced reasons if available, fallback to original
        if enhanced_reasons:
            match_data['reasons'] = enhanced_reasons
        
        match_data['intro_path'] = intro_path
        match_data['connection_strength'] = connection_strength
        
        matches.append(MatchResult(**match_data))
    
    return SearchResponse(
        query=q,
        filters=SearchFilters(
            role=role,
            sector=sector,
            stage=stage,
            location=location,
        ),
        count=len(matches),
        matches=matches,
    )


@app.get("/intro-path/{target_id}", response_model=IntroPathResponse)
def get_introduction_path(
    target_id: int,
    source_id: int = Query(1, description="Source entity ID (default: owner)"),
    db: Session = Depends(get_db),
):
    """Get introduction path from source to target entity."""
    path_data = get_intro_path(source_id, target_id, db)
    mutual_data = get_mutual_connections(source_id, target_id, db)
    strength = calculate_connection_strength(source_id, target_id, db)
    
    intro_path = []
    for node in path_data:
        intro_path.append(
            {
                "id": node["id"],
                "name": node["name"],
                "company": node.get("company"),
                "position": node.get("position"),
                "role": node.get("role"),
                "linkedin_url": node.get("linkedin_url"),
            }
        )

    mutual_connections = []
    for node in mutual_data:
        mutual_connections.append(
            {
                "id": node["id"],
                "name": node["name"],
                "company": node.get("company"),
                "position": node.get("position"),
                "role": node.get("role"),
            }
        )
    
    return IntroPathResponse(
        source_id=source_id,
        target_id=target_id,
        intro_path=intro_path,
        mutual_connections=mutual_connections,
        connection_strength=strength,
    )


@app.get("/stats", response_model=NetworkStatsResponse)
def get_stats(db: Session = Depends(get_db)):
    """Get network statistics."""
    stats = get_network_stats(db)
    return NetworkStatsResponse(**stats)


@app.post("/generate-intro-email/{target_id}", response_model=EmailGenerationResponse)
def generate_intro_email(
    target_id: int,
    source_id: int = Query(1, description="Source entity ID (default: owner/founder)"),
    tones: Optional[str] = Query(
        "formal,casual,enthusiastic",
        description="Comma-separated tones: formal, casual, enthusiastic"
    ),
    db: Session = Depends(get_db),
):
    """
    Generate warm introduction email(s) from founder to investor.
    
    Creates personalized introduction emails based on:
    - Introduction path through mutual connections
    - Match factors (sector, stage, geography)
    - Entity profiles and backgrounds
    
    Returns multiple email variants in different tones.
    """
    # Step 1: fetch the founder (source) and investor (target) records.
    founder = db.query(Entity).filter(Entity.id == source_id).first()
    if not founder:
        raise HTTPException(status_code=404, detail="Founder not found")
    
    investor = db.query(Entity).filter(Entity.id == target_id).first()
    if not investor:
        raise HTTPException(status_code=404, detail="Investor not found")
    
    # Step 2: basic guard rail to ensure the target is actually an investor.
    if investor.role != "investor":
        raise HTTPException(
            status_code=400,
            detail=f"Target entity is not an investor (role: {investor.role})"
        )
    
    # Step 3: turn the comma-separated tone list into a clean Python list.
    tone_list = [t.strip().lower() for t in tones.split(",")]
    valid_tones = ["formal", "casual", "enthusiastic"]
    tone_list = [t for t in tone_list if t in valid_tones]
    
    if not tone_list:
        tone_list = ["formal"]
    
    # Step 4: collect relationship context (intro path + mutual connections).
    intro_path_data = []
    mutual_data = []
    connection_strength = 0.0
    
    try:
        intro_path_data = get_intro_path(source_id, target_id, db)
        mutual_data = get_mutual_connections(source_id, target_id, db)
        connection_strength = calculate_connection_strength(source_id, target_id, db)
    except Exception as e:
        print(f"Warning: Could not get intro path: {e}")
    
    # Step 5: calculate match factors so the copy references real strengths.
    match_factors = calculate_match_factors(investor, query="")
    match_score = calculate_overall_match_score(
        investor,
        query="",
        similarity_score=0.8  # Default similarity
    )
    
    # Step 6: generate the email drafts.
    emails_dict = generate_multiple_emails(
        founder=founder,
        investor=investor,
        match_factors=match_factors,
        match_score=match_score,
        intro_path=intro_path_data,
        mutual_connections=mutual_data,
        tones=tone_list
    )
    
    # Step 7: pick the most useful mutual contact for display.
    intro_via = "Direct connection"
    if intro_path_data and len(intro_path_data) > 1:
        intro_via = intro_path_data[1].get('name', 'Mutual connection')
    elif mutual_data:
        intro_via = mutual_data[0].get('name', 'Mutual connection')
    
    return EmailGenerationResponse(
        target_investor=f"{investor.full_name}, {investor.company}",
        intro_via=intro_via,
        match_score=match_score,
        emails=emails_dict
    )
