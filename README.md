# SmartClause - AI-Powered Legal Document Analysis Platform

**🚀 MVP Ready!** SmartClause is a complete AI-powered legal document analysis platform focused on the Russian legal market. The platform leverages RAG (Retrieval-Augmented Generation) technology with legal vector databases to provide intelligent document analysis and interactive consultation capabilities.

## 🎯 What You Can Do

**Ready to use out of the box:**
- **Upload and Analyze Documents**: Upload legal documents (up to 10MB) and get AI-powered risk analysis and recommendations
- **Semantic Legal Search**: Search through a comprehensive Civil Code database using natural language queries
- **Interactive Web Interface**: Complete workflow from document upload to detailed analysis results
- **Real-time Processing**: Watch your documents being processed with live status updates
- **REST API Access**: Full programmatic access to all analysis capabilities

## ✨ Key Features

### Document Analysis Pipeline
- **Smart Upload Interface**: Drag-and-drop document upload with progress tracking
- **AI-Powered Analysis**: Legal document analysis for risks, compliance issues, and recommendations
- **Comprehensive Results**: Detailed analysis with causes, risks, and actionable recommendations
- **Multiple File Formats**: Support for text files and structured documents

### Legal Knowledge Base
- **Civil Code Database**: Complete Russian Civil Code with 4,400+ articles and embeddings
- **Semantic Search**: Vector-based similarity search using BAAI/bge-m3 embeddings
- **Configurable Retrieval**: Multiple distance functions (cosine, L2, inner product)
- **Structured Metadata**: Articles organized by sections, chapters, and legal references

### Technology Stack
- **Frontend**: Vue.js 3 with modern UI components and routing
- **Backend**: Spring Boot REST API with Swagger documentation
- **AI Engine**: FastAPI microservice with LangChain and OpenRouter integration
- **Database**: PostgreSQL with pgvector extension for vector operations
- **LLM Integration**: OpenAI GPT-4o via OpenRouter for analysis generation
- **Embeddings**: BAAI/bge-m3 sentence transformer for semantic understanding
- **Deployment**: Docker Compose orchestration for easy setup

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Git LFS (Large File Storage) for handling the embeddings dataset
- OpenRouter API key ([Get one here](https://openrouter.ai/))

### 1. Clone and Setup
```bash
# Install Git LFS (if not already installed)
# macOS: brew install git-lfs
# Ubuntu: sudo apt install git-lfs
# Windows: Download from https://git-lfs.github.io/

# Initialize Git LFS
git lfs install

# Clone the repository (LFS will automatically download large files)
git clone <repository-url>
cd SmartClause

# Copy environment template
cp analyzer/env.example analyzer/.env
```

### 2. Configure Environment
Edit `analyzer/.env` and add your OpenRouter API key (ask team leader for the key):
```bash
OPENROUTER_API_KEY=your_api_key_here
```

### 3. Launch the Platform
The first launch will take a while to download the embeddings model.
```bash
docker-compose up --build -d
```

### 4. Setup Vector Database
After the services are running, set up the vector database. This script uploads the pre-computed legal article embeddings (>200MB, automatically downloaded via Git LFS) to PostgreSQL.
```bash
docker-compose exec analyzer python scripts/manage_embeddings.py upload --clear-existing
```

**Note**: The embeddings file (`legal_rules_with_embeddings.csv`) is stored using Git LFS and should be automatically downloaded when you clone the repository. If you encounter issues, ensure Git LFS is properly installed and run `git lfs pull`.

### 5. Access the Application
- **🌐 Web Application**: [http://localhost:8080](http://localhost:8080)
- **📋 Backend API**: [http://localhost:8000](http://localhost:8000)
- **🔍 AI Analysis API**: [http://localhost:8001](http://localhost:8001)
- **📚 API Documentation**: [http://localhost:8001/docs](http://localhost:8001/docs)

**You're ready to analyze legal documents!** 🎉

## 🖥️ User Interface

The platform provides a complete web interface with three main screens:

1. **Upload Screen**: Drag-and-drop interface for document upload
2. **Processing Screen**: Real-time processing status with progress indicators  
3. **Results Screen**: Comprehensive analysis results with risks and recommendations

### Service Architecture
- **Frontend** (Port 8080): Vue.js SPA with upload, processing, and results interfaces
- **Backend** (Port 8000): Spring Boot API handling document uploads and orchestration
- **Analyzer** (Port 8001): FastAPI microservice with RAG pipeline and LLM integration
- **Database** (Port 5432): PostgreSQL with pgvector for vector similarity search

## 📊 MVP Implementation Status

### ✅ Completed and Ready
- **Full Web Application** with complete UI workflow
- **Document Upload & Analysis** with file processing pipeline
- **AI-Powered Analysis** using OpenAI GPT-4o for legal document review
- **Vector Database** with 4,400+ Civil Code articles and embeddings
- **Semantic Search** with configurable similarity functions
- **REST API** with comprehensive endpoints and Swagger documentation
- **Docker Deployment** with full service orchestration
- **Real-time Processing** with status updates and progress tracking
- **Error Handling** with comprehensive validation and user feedback

### 🎯 Future Enhancements
- **User Management**: Authentication and personalized document history
- **Advanced Analytics**: Legal precedent analysis and case law integration
- **Performance Optimization**: Caching and batch processing capabilities
- **Deployment**: Production-ready configuration with monitoring and scaling
- **Chat-based document management system**: Interactive legal consultation interface

## 🚀 Ready for Production

This MVP provides a solid foundation for a legal tech platform with:
- **Scalable Architecture**: Microservices ready for horizontal scaling
- **Production APIs**: Comprehensive error handling and validation
- **Legal Domain Expertise**: Purpose-built for Russian legal document analysis
- **Modern Tech Stack**: Latest frameworks and AI integration patterns
- **Docker Deployment**: Consistent environments across development and production

**Start analyzing legal documents today!** Upload your first document at [http://localhost:8080](http://localhost:8080) after following the Quick Start guide.

## 🔧 Advanced Configuration

### Environment Variables
The `analyzer/.env` file contains the following configuration options:

**Required:**
- `OPENROUTER_API_KEY`: Your OpenRouter API key for LLM integration

**Database (pre-configured for Docker):**
- `POSTGRES_DB=smartclause_analyzer`
- `POSTGRES_USER=smartclause` 
- `POSTGRES_PASSWORD=smartclause`
- `DATABASE_URL=postgresql://smartclause:smartclause@postgres:5432/smartclause_analyzer`

**Optional:**
- `OPENROUTER_MODEL`: LLM model to use (default: `openai/gpt-4o`)
- `EMBEDDING_MODEL`: Embedding model (default: `BAAI/bge-m3`)
- `MAX_FILE_SIZE`: File upload size limit in bytes (default: 10MB)
- `DEFAULT_K`: Default number of documents to retrieve in RAG (default: 5)
- `MAX_K`: Maximum number of documents to retrieve (default: 20)

### Vector Database Management
Use `docker-compose exec` to run management commands inside the `analyzer` container.
```bash
# Upload pre-computed embeddings to database (recommended)
docker-compose exec analyzer python scripts/manage_embeddings.py upload --clear-existing

# Generate embeddings from scratch (only if needed - takes 45-60 minutes)
docker-compose exec analyzer python scripts/manage_embeddings.py generate

# Full setup (generate + upload)
docker-compose exec analyzer python scripts/manage_embeddings.py full --clear-existing
```

**Note for Apple Silicon users**: The embedding generation script has been optimized for MPS memory management. If you still encounter memory issues while generating embeddings, use:
```bash
# Force CPU usage (slower but stable)
docker-compose exec analyzer python scripts/manage_embeddings.py generate --force-cpu

# Ultra-conservative mode for memory-constrained systems
docker-compose exec analyzer python scripts/manage_embeddings.py generate --force-cpu --batch-size 1
```

**Git LFS Troubleshooting**: If the embeddings file wasn't downloaded properly:
```bash
# Verify LFS installation
git lfs version

# Download LFS files manually
git lfs pull

# Check file size (should be ~212MB)
ls -lh analyzer/scripts/legal_rules_with_embeddings.csv
```

## 📚 API Documentation

### Available Endpoints

#### Analyzer API (Port 8001)
- **GET /health**: Health check with database connectivity status
- **POST /api/v1/retrieve**: Semantic document retrieval with configurable similarity functions
- **POST /api/v1/analyze**: Legal document analysis with risk assessment
- **POST /api/v1/embed**: Text embedding generation
- **GET /docs**: Interactive API documentation

#### Backend API (Port 8000)
- **POST /api/v1/get_analysis**: Document upload and analysis orchestration
- **GET /api/v1/health**: Service health check

### API Usage Examples

#### Document Retrieval
```bash
curl -X POST "http://localhost:8001/api/v1/retrieve" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "contract termination conditions",
    "k": 5,
    "distance_function": "cosine"
  }'
```

#### Document Analysis
```bash
curl -X POST "http://localhost:8001/api/v1/analyze" \
  -F "id=my_contract_123" \
  -F "file=@contract.txt"
```

#### Text Embedding
```bash
curl -X POST "http://localhost:8001/api/v1/embed" \
  -H "Content-Type: application/json" \
  -d '{"text": "Your text to embed"}'
```

## 🔍 Legal Dataset

The platform includes a comprehensive Civil Code dataset:
- **4,400+ legal articles** with pre-computed embeddings
- **212MB embeddings file** stored via Git LFS for efficient distribution
- **Structured metadata** (sections, chapters, article numbers)
- **BAAI/bge-m3 embeddings** for high-quality semantic understanding
- **Memory-optimized generation** with streaming processing for Apple Silicon compatibility

For detailed analyzer-specific documentation, see [`analyzer/README.md`](analyzer/README.md).