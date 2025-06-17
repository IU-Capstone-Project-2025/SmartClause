# SmartClause

Smart Clause is an AI-powered legal document analysis platform focused on Russian legal market and legislation with a comprehensive chat-based document management system. The platform leverages RAG (Retrieval-Augmented Generation) technology with legal vector databases to provide intelligent document analysis and interactive consultation capabilities.

## Features

### Current Implementation
- **Document Retrieval**: Semantic search over legal document corpus using vector embeddings with configurable distance functions (cosine, L2, inner product)
- **Document Analysis**: AI-powered analysis of legal documents for risks and recommendations using OpenRouter LLM integration
- **Vector Database**: PostgreSQL with pgvector extension for efficient similarity search
- **Legal Rules Database**: Complete Civil Code dataset with pre-computed embeddings
- **REST API**: Full FastAPI implementation with comprehensive endpoints
- **File Upload Support**: Document analysis with file upload capabilities (up to 10MB)
- **Embedding Generation**: Real-time text embedding generation using BAAI/bge-m3 model

### API Endpoints
- **GET /health**: Health check with database connectivity status
- **POST /api/v1/retrieve**: Semantic document retrieval with configurable similarity functions
- **POST /api/v1/analyze**: Legal document analysis with risk assessment
- **POST /api/v1/embed**: Text embedding generation
- **GET /docs**: Interactive API documentation

## Architecture

The platform consists of multiple microservices:
- **Frontend**: Vue.js application for user interface
- **Backend**: FastAPI main application 
- **Analyzer**: RAG-based legal document analysis microservice (primary implementation)
- **Parser**: Civil Code dataset processing and extraction tools

### Technology Stack
- **FastAPI**: Modern Python web framework with async support
- **LangChain**: Framework for LLM applications and document processing
- **PostgreSQL + pgvector**: Vector database for semantic search
- **Sentence Transformers**: Text embedding generation (BAAI/bge-m3)
- **OpenRouter**: LLM API integration (OpenAI GPT-4o)
- **SQLAlchemy**: ORM for database operations
- **Pydantic**: Data validation and serialization
- **Docker**: Containerized deployment

## Prerequisites

- Docker
- Docker Compose

## Environment Setup

Before running the application, you need to configure environment variables for the analyzer microservice:

1. **Copy the environment template**:
   ```bash
   cp analyzer/env.example analyzer/.env
   ```

2. **Configure required environment variables** in `analyzer/.env`:
   
   **Required Configuration:**
   - `OPENROUTER_API_KEY`: Your OpenRouter API key for LLM integration
   
   **Database Configuration (pre-configured for Docker):**
   - `POSTGRES_DB=smartclause_analyzer`
   - `POSTGRES_USER=smartclause` 
   - `POSTGRES_PASSWORD=smartclause`
   - `DATABASE_URL=postgresql://smartclause:smartclause@postgres:5432/smartclause_analyzer`

   **Optional Configuration:**
   - `OPENROUTER_MODEL`: LLM model to use (default: `openai/gpt-4o`)
   - `EMBEDDING_MODEL`: Embedding model (default: `BAAI/bge-m3`)
   - `MAX_FILE_SIZE`: File upload size limit in bytes (default: 10MB)
   - `DEFAULT_K`: Default number of documents to retrieve in RAG (default: 5)
   - `MAX_K`: Maximum number of documents to retrieve (default: 20)

3. **Get your OpenRouter API key**:
   - Sign up at [OpenRouter](https://openrouter.ai/)
   - Generate an API key
   - Add it to your `analyzer/.env` file

## How to run

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd SmartClause
   ```

2. Set up environment variables (see Environment Setup section above)

3. Run the application:
   ```bash
   docker-compose up --build -d
   ```

4. **Access the services**:
   - **Frontend**: [http://localhost:8080](http://localhost:8080)
   - **Backend**: [http://localhost:8000](http://localhost:8000)
   - **Analyzer API**: [http://localhost:8001](http://localhost:8001)
   - **API Documentation**: [http://localhost:8001/docs](http://localhost:8001/docs)

**Note**: The PostgreSQL database with pgvector will be automatically started as part of the Docker Compose setup. After the containers are running, proceed to the Vector Database Setup section below.

## Vector Database Setup

The analyzer microservice uses PostgreSQL with pgvector for semantic search over legal documents. **Make sure Docker containers are running first** (see "How to run" section above). You have two options to set up the vector database:

### Option 1: Use Pre-computed Embeddings (Recommended)
If embeddings are already available in the repository (see `analyzer/scripts/legal_rules_with_embeddings.csv`):

```bash
cd analyzer
# Set up environment variables
export POSTGRES_DB=smartclause_analyzer
export POSTGRES_USER=smartclause
export POSTGRES_PASSWORD=smartclause

# Upload pre-computed embeddings to database
python scripts/manage_embeddings.py upload --clear-existing
```

### Option 2: Generate Embeddings Locally
If you need to generate embeddings from scratch:

```bash
cd analyzer
# Generate embeddings 
python scripts/manage_embeddings.py generate

# Upload to database
python scripts/manage_embeddings.py upload --clear-existing

# Or run both steps together
python scripts/manage_embeddings.py full --clear-existing
```

**Note for Apple Silicon users**: If you encounter memory issues, use:
```bash
python scripts/manage_embeddings.py generate --force-cpu
```

### Available Embedding Scripts
- **`scripts/manage_embeddings.py`**: Convenient wrapper for all embedding operations
- **`scripts/generate_embeddings.py`**: Creates embeddings from legal rules dataset  
- **`scripts/upload_embeddings.py`**: Uploads embeddings to PostgreSQL
- **`scripts/init.sql`**: Database schema initialization

See [`analyzer/scripts/README.md`](analyzer/scripts/README.md) for detailed documentation.

## API Usage Examples

### Document Retrieval
```bash
curl -X POST "http://localhost:8001/api/v1/retrieve" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "contract termination conditions",
    "k": 5,
    "distance_function": "cosine"
  }'
```

### Document Analysis
```bash
curl -X POST "http://localhost:8001/api/v1/analyze" \
  -F "id=my_contract_123" \
  -F "file=@contract.txt"
```

### Text Embedding
```bash
curl -X POST "http://localhost:8001/api/v1/embed" \
  -H "Content-Type: application/json" \
  -d '{"text": "Your text to embed"}'
```

## Current Implementation Status

### ✅ Completed Features
- **Database schema** with pgvector extension
- **FastAPI application** with full REST API
- **Real RAG implementation** with vector similarity search
- **LLM integration** via OpenRouter (OpenAI GPT-4o)
- **Embedding service** with BAAI/bge-m3 model
- **Document processing** pipeline with file upload support
- **Legal dataset processing** with 44MB+ Civil Code embeddings
- **Vector database** population and management scripts
- **API documentation** with interactive Swagger UI
- **Health monitoring** endpoints
- **Comprehensive test suite**

### 🔄 In Progress
- **Frontend integration** with analyzer microservice
- **Advanced document formats** (PDF, DOCX processing)
- **Performance optimization** (caching, batch processing)

### 🎯 Future Enhancements
1. **Enhanced Document Processing**: Support for complex document formats
2. **Advanced Analytics**: More sophisticated legal analysis algorithms  
3. **User Management**: Authentication and user-specific document storage
4. **Real-time Chat**: Interactive legal consultation interface
5. **Performance Optimization**: Caching, async processing, model optimization
6. **Deployment**: Production-ready configuration and monitoring

## Development

### Local Development Setup
```bash
cd analyzer
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

### Testing
```bash
cd analyzer
pytest tests/
```

### Database Management
```bash
# Check database status
python scripts/manage_embeddings.py status

# Clear and rebuild embeddings
python scripts/manage_embeddings.py full --clear-existing
```

## Legal Dataset

The platform includes a comprehensive Civil Code dataset with:
- **4,400+ legal articles** with embeddings
- **44MB+ vector database** for semantic search
- **Pre-computed embeddings** using BAAI/bge-m3 model
- **Structured metadata** (sections, chapters, article numbers)

## Monitoring and Health

- **Health Check**: `GET /health` - Database connectivity and service status
- **API Documentation**: `GET /docs` - Interactive Swagger UI
- **Metrics**: Database connection status, embedding dimensions, response times

For detailed analyzer-specific documentation, see [`analyzer/README.md`](analyzer/README.md).