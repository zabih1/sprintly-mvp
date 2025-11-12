"""SQLAlchemy models for PostgreSQL database."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, DateTime, Float, Integer, String, Text, JSON, Index
from sqlalchemy.dialects.postgresql import ARRAY

from .database import Base


class Entity(Base):
    """Core entity table storing people (founders, investors, enablers)."""

    __tablename__ = "entities"

    id = Column(Integer, primary_key=True, index=True)
    
    # Basic info from LinkedIn
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    full_name = Column(String(200), nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=True, index=True)
    linkedin_url = Column(String(500), unique=True, nullable=True, index=True)
    company = Column(String(255), nullable=True, index=True)
    position = Column(String(255), nullable=True)
    connected_on = Column(DateTime, nullable=True)
    
    # Enriched fields (from LLM)
    role = Column(String(50), nullable=True, index=True)  # founder, investor, enabler
    sector_focus = Column(ARRAY(String), nullable=True)  # ["fintech", "healthcare"]
    stage_focus = Column(ARRAY(String), nullable=True)  # ["seed", "series-a"]
    location = Column(String(255), nullable=True, index=True)
    check_size_min = Column(Integer, nullable=True)  # in USD
    check_size_max = Column(Integer, nullable=True)  # in USD
    investment_thesis = Column(Text, nullable=True)
    tags = Column(ARRAY(String), nullable=True)
    
    # Vector embedding (1536 dimensions for text-embedding-3-large)
    embedding = Column(Vector(1536), nullable=True)
    
    # Metadata
    confidence_score = Column(Float, nullable=True)  # 0-1
    enriched_at = Column(DateTime, nullable=True)
    raw_data = Column(JSON, nullable=True)  # Store original CSV row
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Create index on vector column for similarity search
    __table_args__ = (
        Index(
            'idx_entity_embedding',
            'embedding',
            postgresql_using='hnsw',
            postgresql_with={'m': 16, 'ef_construction': 64},
            postgresql_ops={'embedding': 'vector_cosine_ops'}
        ),
    )


class Connection(Base):
    """Edges table storing relationships between entities."""

    __tablename__ = "connections"

    id = Column(Integer, primary_key=True, index=True)
    
    # Source and target entities
    source_id = Column(Integer, nullable=False, index=True)
    target_id = Column(Integer, nullable=False, index=True)
    
    # Relationship metadata
    relationship_type = Column(String(50), nullable=True)  # mutual, introduced_by, etc.
    strength = Column(Float, nullable=True)  # 0-1, calculated from interactions
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('idx_source_target', 'source_id', 'target_id'),
    )


class MatchHistory(Base):
    """Track match results and feedback for continuous improvement."""

    __tablename__ = "match_history"

    id = Column(Integer, primary_key=True, index=True)
    
    # Query info
    query_text = Column(Text, nullable=False)
    filters = Column(JSON, nullable=True)
    
    # Match results
    investor_id = Column(Integer, nullable=False, index=True)
    score = Column(Float, nullable=False)
    rank = Column(Integer, nullable=False)
    reasons = Column(JSON, nullable=True)
    
    # User feedback
    clicked = Column(Integer, default=0)  # Was this result clicked?
    contacted = Column(Integer, default=0)  # Did user reach out?
    feedback = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('idx_query_investor', 'query_text', 'investor_id'),
    )

