"""CSV processing and entity creation."""
from __future__ import annotations

import io
import sys
from datetime import datetime
from typing import BinaryIO, Dict, List

import pandas as pd
from sqlalchemy.orm import Session

from .enrichment import create_embedding_text, enrich_entity, generate_embedding
from .models import Connection, Entity
from .neo4j_client import neo4j_client


def parse_linkedin_csv(file_content: bytes) -> pd.DataFrame:
    """Parse LinkedIn connections CSV file."""
    try:
        # Try multiple parsing strategies
        df = None
        last_error = None
        
        # Strategy 1: Standard CSV with various encodings
        for encoding in ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'iso-8859-1']:
            try:
                df = pd.read_csv(
                    io.BytesIO(file_content),
                    encoding=encoding,
                    on_bad_lines='skip',  # Skip problematic lines
                    engine='python'  # Use python engine for more flexibility
                )
                break
            except:
                continue
        
        # Strategy 2: Try with explicit delimiter and quoting
        if df is None or df.empty:
            for encoding in ['utf-8', 'utf-8-sig', 'latin-1']:
                try:
                    df = pd.read_csv(
                        io.BytesIO(file_content),
                        encoding=encoding,
                        sep=',',
                        quotechar='"',
                        on_bad_lines='skip',
                        engine='python',
                        skipinitialspace=True
                    )
                    break
                except:
                    last_error = str(sys.exc_info()[1])
                    continue
        
        if df is None or df.empty:
            raise ValueError(
                f"Could not parse CSV file. Last error: {last_error}\n\n"
                f"Common issues:\n"
                f"1. File has extra header rows - ensure column names are on line 1\n"
                f"2. File uses different delimiter (semicolon instead of comma)\n"
                f"3. File has wrong encoding\n\n"
                f"Please use the sample_connections.csv as a template."
            )
        
        # Clean up: remove completely empty rows
        df = df.dropna(how='all')
        
        # Remove any rows where all values are empty strings
        df = df[~df.apply(lambda x: x.astype(str).str.strip().eq('').all(), axis=1)]
        
        # Strip whitespace from column names
        df.columns = df.columns.str.strip()
        
        # Expected columns from LinkedIn export
        expected_cols = {
            'First Name', 'Last Name', 'URL', 'Email Address', 
            'Company', 'Position', 'Connected On'
        }
        
        # Check if we have the required columns
        actual_cols = set(df.columns)
        missing_cols = expected_cols - actual_cols
        
        if missing_cols:
            # Provide helpful error message
            raise ValueError(
                f"CSV is missing required columns: {missing_cols}\n\n"
                f"Found columns: {list(df.columns)}\n\n"
                f"Expected format (exact column names):\n"
                f"First Name,Last Name,URL,Email Address,Company,Position,Connected On\n\n"
                f"If your CSV has different column names, please rename them to match.\n"
                f"Use backend/sample_connections.csv as a reference."
            )
        
        # Check if we have any data rows
        if len(df) == 0:
            raise ValueError(
                "CSV file has no data rows. Please ensure your file contains connection data."
            )
        
        # Replace NaN values with None for proper JSON serialization
        df = df.replace({pd.NA: None, pd.NaT: None})
        df = df.where(pd.notnull(df), None)
        
        return df
        
    except ValueError as e:
        # Re-raise ValueError with our custom message
        raise ValueError(str(e))
    except Exception as e:
        raise ValueError(
            f"Failed to parse CSV: {str(e)}\n\n"
            f"Common solutions:\n"
            f"1. Open CSV in Excel/Google Sheets and check formatting\n"
            f"2. Ensure first line has column headers\n"
            f"3. Remove any extra rows before headers\n"
            f"4. Save as 'CSV UTF-8' format\n"
            f"5. Try uploading backend/sample_connections.csv to test\n\n"
            f"For help: Run 'python validate_csv.py your_file.csv' from backend folder"
        )


def process_connection_row(row: pd.Series, db: Session, owner_id: int = 1) -> Entity:
    """Process a single row from LinkedIn connections CSV."""
    # Helper function to safely extract string values
    def safe_str(value):
        if value is None or pd.isna(value):
            return None
        val = str(value).strip()
        if val.lower() in ['nan', 'none', '']:
            return None
        return val
    
    # Extract basic info
    first_name = safe_str(row.get('First Name', '')) or ''
    last_name = safe_str(row.get('Last Name', '')) or ''
    full_name = f"{first_name} {last_name}".strip()
    email = safe_str(row.get('Email Address'))
    linkedin_url = safe_str(row.get('URL'))
    company = safe_str(row.get('Company'))
    position = safe_str(row.get('Position'))
    
    # Parse connection date
    connected_on = None
    connected_str = safe_str(row.get('Connected On'))
    if connected_str:
        try:
            connected_on = pd.to_datetime(connected_str)
        except:
            pass

    # Check if entity already exists
    existing = None
    if email:
        existing = db.query(Entity).filter(Entity.email == email).first()
    if not existing and linkedin_url:
        existing = db.query(Entity).filter(Entity.linkedin_url == linkedin_url).first()

    if existing:
        return existing

    # Enrich with AI
    enrichment_data = enrich_entity(full_name, company, position)
    
    # Create entity dict for embedding
    entity_dict = {
        "full_name": full_name,
        "company": company,
        "position": position,
        "role": enrichment_data.get("role"),
        "sector_focus": enrichment_data.get("sector_focus", []),
        "stage_focus": enrichment_data.get("stage_focus", []),
        "investment_thesis": enrichment_data.get("investment_thesis"),
        "location": enrichment_data.get("location"),
    }
    
    # Generate embedding
    embedding_text = create_embedding_text(entity_dict)
    embedding = generate_embedding(embedding_text)

    # Convert row to dict and clean NaN values for JSON storage
    raw_data = {}
    for key, value in row.to_dict().items():
        if pd.isna(value):
            raw_data[key] = None
        else:
            raw_data[key] = value
    
    # Create entity
    entity = Entity(
        first_name=first_name,
        last_name=last_name,
        full_name=full_name,
        email=email,
        linkedin_url=linkedin_url,
        company=company,
        position=position,
        connected_on=connected_on,
        role=enrichment_data.get("role"),
        sector_focus=enrichment_data.get("sector_focus", []),
        stage_focus=enrichment_data.get("stage_focus", []),
        location=enrichment_data.get("location"),
        check_size_min=enrichment_data.get("check_size_min"),
        check_size_max=enrichment_data.get("check_size_max"),
        investment_thesis=enrichment_data.get("investment_thesis"),
        tags=enrichment_data.get("tags", []),
        embedding=embedding,
        confidence_score=enrichment_data.get("confidence", 0.0),
        enriched_at=datetime.utcnow(),
        raw_data=raw_data,
    )

    db.add(entity)
    db.flush()  # Get the ID

    # Add to Neo4j
    neo4j_client.create_entity_node(
        entity_id=entity.id,
        name=full_name,
        role=entity.role,
        company=company,
        properties={
            "email": email or "",
            "linkedin_url": linkedin_url or "",
            "position": position or "",
        },
    )

    # Create connection from owner to this entity
    connection = Connection(
        source_id=owner_id,
        target_id=entity.id,
        relationship_type="CONNECTED_TO",
        strength=1.0,
    )
    db.add(connection)

    # Add connection to Neo4j
    neo4j_client.create_connection(
        source_id=owner_id,
        target_id=entity.id,
        relationship_type="CONNECTED_TO",
        strength=1.0,
    )

    return entity


def process_linkedin_csv(
    file_content: bytes,
    db: Session,
    owner_id: int = 1,
) -> Dict[str, int]:
    """Process LinkedIn connections CSV and create entities."""
    df = parse_linkedin_csv(file_content)
    
    stats = {
        "total": len(df),
        "created": 0,
        "skipped": 0,
        "errors": 0,
    }

    for idx, row in df.iterrows():
        try:
            entity = process_connection_row(row, db, owner_id)
            if entity:
                stats["created"] += 1
            else:
                stats["skipped"] += 1
        except Exception as e:
            print(f"Error processing row {idx}: {e}")
            stats["errors"] += 1

    db.commit()
    return stats

