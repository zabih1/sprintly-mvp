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

- LinkedIn connection import (CSV)
- AI-powered entity enrichment
- Graph database (Neo4j) for relationship mapping
- Vector search for intelligent matching
- Founder-investor compatibility scoring

## Technologies

- **Backend**: FastAPI, Python
- **Database**: Neo4j (graph), Vector search
- **AI**: OpenAI (embeddings, classification)

## License

[Add your license here]

