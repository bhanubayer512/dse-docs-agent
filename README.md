# ph-rnd-dse-ai-docs
AI Driven Documentation Authoring MVP

## Setup
1. pip install -e '.[dev]'
2. Copy .env.example to .env and add AWS credentials
3. uvicorn api.main:app --reload

## CLI Usage
    python -m agents.doc_agent sample_code/example.py

## API Usage
    curl -X POST http://localhost:8000/generate -H 'Content-Type: application/json' -d '{"file_path": "sample_code/example.py"}'

## Health
    curl http://localhost:8000/health

## Stack
- Agent: Strands Agents SDK + Claude 3.5 Haiku via AWS Bedrock
- API: FastAPI + Uvicorn
- Python 3.11+
