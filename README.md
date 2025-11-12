# Sprintly MVP

Founder-investor matching platform powered by AI and graph database.

## Project Structure



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
- **Frontend**: HTML, JavaScript

## License

[Add your license here]

