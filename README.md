# Sprintly MVP

Founder-investor matching platform powered by AI and graph database.

## Project Structure

```
sprintly-mvp/
├── README.md
├── requirements.txt
└── backend/
    ├── app/
    │   ├── __init__.py
    │   ├── main.py
    │   ├── api/
    │   │   ├── __init__.py
    │   │   └── schemas/
    │   │       ├── __init__.py
    │   │       ├── common.py
    │   │       ├── email.py
    │   │       ├── entity.py
    │   │       ├── intro.py
    │   │       ├── investor.py
    │   │       ├── search.py
    │   │       ├── stats.py
    │   │       └── upload.py
    │   ├── core/
    │   │   ├── __init__.py
    │   │   ├── config.py
    │   │   ├── database.py
    │   │   └── models.py
    │   └── services/
    │       ├── __init__.py
    │       ├── batch_processor.py
    │       ├── csv_processor.py
    │       ├── email_generator.py
    │       ├── enrichment.py
    │       ├── graph_service.py
    │       ├── match_scorer.py
    │       ├── neo4j_client.py
    │       ├── vector_search.py
    │       └── prompts/
    │           ├── __init__.py
    │           ├── email_prompts.py
    │           └── enrichment_prompts.py
    ├── notebooks/
    │   ├── clear_database.ipynb
    │   └── sample_connections.csv
    ├── test_matching_engine.py
    └── validate_csv.py
```

## Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd sprintly-mvp
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   - Copy `backend/env.example.txt` to `backend/.env`
   - Add your API keys and configuration

5. **Run the backend**
   
   **Option A: Using the startup script (Recommended for large files)**
   ```bash
   cd backend
   python run_server.py
   ```
   Or on Windows:
   ```bash
   cd backend
   run_server.bat
   ```
   
   **Option B: Direct uvicorn command**
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```

6. **Run the frontend**
   ```bash
   cd frontend
   python serve.py
   ```

## Features

- **LinkedIn connection import (CSV)** - Supports large files up to 2GB
- **AI-powered entity enrichment** - Automated role detection and classification
- **Graph database (Neo4j)** - Relationship mapping and intro path discovery
- **Vector search** - Intelligent semantic matching
- **Founder-investor compatibility scoring** - Multi-factor matching algorithm
- **Batch processing** - Fast parallel processing for large datasets (10,000+ connections)
- **Comprehensive logging** - Detailed structured logging for all operations (see [LOGGING_IMPLEMENTATION.md](LOGGING_IMPLEMENTATION.md))

## Technologies

- **Backend**: FastAPI, Python
- **Database**: Neo4j (graph), PostgreSQL, Vector search
- **AI**: OpenAI (embeddings, classification)

## File Upload Configuration

The system supports large CSV file uploads up to **2GB** in size:

- **Maximum file size**: 2GB (configurable in `backend/app/core/config.py`)
- **Recommended format**: CSV with LinkedIn export format
- **Batch processing**: Optimized for files with 10,000+ connections
- **Memory efficient**: Processes files in chunks to handle large datasets

To change the upload limit, modify the `max_upload_size` setting in `backend/app/core/config.py`:

```python
# Upload settings
max_upload_size: int = 2 * 1024 * 1024 * 1024  # 2GB (adjust as needed)
```

For very large files (100MB+), it's recommended to use the `/upload-fast` endpoint with `skip_enrichment=true` for faster initial import, then enrich the data later.

## Logging and Monitoring

The application includes comprehensive structured logging for all operations:
- **File ingestion** and CSV processing
- **LLM enrichment** (OpenAI API calls)
- **Embedding generation**
- **Database operations** (PostgreSQL & Neo4j)
- **Email generation**
- **Vector search** operations

### Log Locations
- **Console**: Color-coded output during development
- **File**: `backend/logs/sprintly_YYYYMMDD.log` (automatic daily rotation)

### Viewing Logs
```bash
# View real-time logs
tail -f backend/logs/sprintly_20251114.log

# View errors only
grep "ERROR" backend/logs/sprintly_20251114.log

# Monitor processing progress
grep "Progress:" backend/logs/sprintly_20251114.log
```

For detailed information on logging, see [LOGGING_IMPLEMENTATION.md](LOGGING_IMPLEMENTATION.md).

## License

[Add your license here]

