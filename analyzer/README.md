# SmartClause Analyzer Microservice

A RAG-based legal document analysis microservice built with FastAPI, LangChain, and PostgreSQL with pgvector.

## Features

- **Document Retrieval**: Semantic search over legal document corpus using vector embeddings
- **Document Analysis**: AI-powered analysis of legal documents for risks and recommendations
- **Vector Database**: PostgreSQL with pgvector for efficient similarity search
- **Scalable Architecture**: Microservice design for easy scaling and integration

## API Endpoints

### `/api/v1/retrieve` (POST)
Retrieve relevant documents based on query using RAG.

**Request:**
```json
{
  "query": "contract termination conditions",
  "k": 5
}
```

**Response:**
```json
{
  "results": [
    {
      "text": "Legal article text...",
      "embedding": [0.123, -0.456, ...]
    }
  ],
  "total_results": 5,
  "query": "contract termination conditions"
}
```

### `/api/v1/analyze` (POST)
Analyze a document file for legal risks and recommendations.

**Request:** Multipart form data
- `id`: Document identifier (string)
- `file`: Document file (upload)

**Response:**
```json
{
  "points": [
    {
      "cause": "Unclear termination conditions",
      "risk": "High risk of legal disputes",
      "recommendation": "Add detailed termination procedures"
    }
  ],
  "document_id": "doc123",
  "analysis_timestamp": "2024-01-01T00:00:00"
}
```

### `/health` (GET)
Health check endpoint for monitoring service status.

## Database Schema

The service uses PostgreSQL with pgvector extension and includes:

- `legal_rules`: Civil Code articles with embeddings
- `document_embeddings`: Document chunks for RAG retrieval
- `analysis_results`: Stored analysis results

## Technology Stack

- **FastAPI**: Modern Python web framework
- **LangChain**: Framework for LLM applications
- **PostgreSQL**: Database with pgvector extension
- **Sentence Transformers**: Text embedding generation
- **SQLAlchemy**: ORM for database operations
- **Pydantic**: Data validation and serialization

## Development Setup

1. **Prerequisites:**
   - Python 3.11+
   - Docker and Docker Compose
   - PostgreSQL with pgvector

2. **Environment Setup:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Docker Compose:**
   ```bash
   docker-compose up analyzer postgres
   ```

4. **Local Development:**
   ```bash
   cd analyzer
   pip install -r requirements.txt
   uvicorn app.main:app --reload --port 8001
   ```

## Architecture

```
analyzer/
├── app/
│   ├── api/           # FastAPI routes
│   ├── core/          # Configuration and database
│   ├── models/        # SQLAlchemy models
│   ├── schemas/       # Pydantic schemas
│   └── services/      # Business logic
├── scripts/           # Database initialization
└── tests/            # Test suite
```

## Dataset & Embeddings Management

The analyzer includes scripts to process the Civil Code dataset from the `parser` module and create embeddings for RAG functionality:

### Quick Start with Embeddings

```bash
# 1. Generate embeddings from dataset (first time only)
python scripts/manage_embeddings.py generate

# 2. Upload to PostgreSQL database
python scripts/manage_embeddings.py upload --clear-existing

# 3. Or run everything in one command
python scripts/manage_embeddings.py full --clear-existing
```

### Available Scripts

- **`scripts/generate_embeddings.py`** - Creates embeddings from legal rules dataset
- **`scripts/upload_embeddings.py`** - Uploads embeddings to PostgreSQL
- **`scripts/manage_embeddings.py`** - Convenient wrapper for all operations

See [`scripts/README.md`](scripts/README.md) for detailed documentation.

## Current Implementation Status

- ✅ Database schema with pgvector
- ✅ FastAPI application structure
- ✅ Mock API endpoints
- ✅ Embedding service setup
- ✅ **Dataset processing and embedding generation**
- ✅ **Vector database population scripts**
- 🔄 RAG implementation (transitioning from mock to real data)
- 🔄 LLM integration for analysis
- 🔄 Document processing pipeline

## Future Enhancements

1. **Real RAG Implementation**: Replace mock data with actual vector similarity search
2. **LLM Integration**: Add OpenAI/local LLM for document analysis
3. **Document Processing**: Support multiple file formats (PDF, DOCX, etc.)
4. **Advanced Analytics**: More sophisticated legal analysis algorithms
5. **Performance Optimization**: Caching, batch processing, async operations

## Testing

```bash
# Run tests
pytest

# Test API endpoints
curl -X POST "http://localhost:8001/api/v1/retrieve-json" \
  -H "Content-Type: application/json" \
  -d '{"query": "test query", "k": 3}'
```

## Monitoring

- Health endpoint: `GET /health`
- API documentation: `GET /docs`
- Alternative docs: `GET /redoc` 