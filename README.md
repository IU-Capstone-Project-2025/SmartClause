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
- **Chunked Civil Code Database**: Complete Russian Civil Code with 190,000+ rules and 413,000+ text chunks with embeddings
- **Semantic Search**: Vector-based similarity search using BAAI/bge-m3 embeddings on text chunks
- **Configurable Retrieval**: Multiple distance functions (cosine, L2, inner product)
- **Structured Metadata**: Articles organized by sections, chapters, and legal references with precise chunk positioning

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

### 4. Setup Database and Load Legal Dataset

#### Option A: Quick Setup (Recommended)
If you already have the processed datasets, use the unified script:

```bash
# Initialize database with new schema
docker-compose exec analyzer python scripts/init_db.py

# Upload everything to database
docker-compose exec analyzer python scripts/process_and_upload_datasets.py --upload --clear
```

#### Option B: Step-by-Step Setup
If you want more control over the process:

```bash
# 1. Initialize database
docker-compose exec analyzer python scripts/init_db.py

# 2. Generate embeddings only (optional - takes time)
docker-compose exec analyzer python scripts/process_and_upload_datasets.py --generate

# 3. Upload to database
docker-compose exec analyzer python scripts/process_and_upload_datasets.py --upload --clear
```

**Note**: The first run will download the BAAI/bge-m3 model (~2GB) and generate embeddings for 413,000+ text chunks, which may take 1-2 hours depending on your hardware.

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

## 📊 Database Structure

The new optimized database structure separates rules metadata from searchable chunks:

### Tables
- **`rules`**: Complete legal rules with metadata (190,000+ entries)
  - `rule_id`, `file`, `rule_number`, `rule_title`, `rule_text`
  - `section_title`, `chapter_title`, `start_char`, `end_char`, `text_length`

- **`rule_chunks`**: Text chunks with embeddings for semantic search (413,000+ entries)
  - `chunk_id`, `rule_id` (foreign key), `chunk_number`, `chunk_text`
  - `chunk_char_start`, `chunk_char_end`, `embedding` (1024-dimensional vector)

- **`analysis_results`**: Document analysis results storage

### Benefits
- **Better Granularity**: Search operates on meaningful text chunks rather than full articles
- **Improved Relevance**: More precise semantic matching with chunk-level embeddings
- **Efficient Storage**: Embeddings only stored for searchable chunks
- **Scalable Design**: Foreign key relationships maintain data integrity

## 📁 Dataset Files

The system uses two main datasets located in `analyzer/scripts/datasets/`:

- **`datasets/rules_dataset.csv`**: Complete legal rules metadata (33MB, 190,846 rules)
- **`datasets/chunks_dataset.csv`**: Text chunks for embedding (65MB, 413,453 chunks)
- **`datasets/chunks_with_embeddings.csv`**: Generated file with embeddings (auto-created)

These datasets are automatically detected and processed by the unified script.

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

### Dataset Processing Options

The unified script `process_and_upload_datasets.py` provides flexible options:

```bash
# Generate embeddings only (no database upload)
docker-compose exec analyzer python scripts/process_and_upload_datasets.py --generate

# Upload existing embeddings (if chunks_with_embeddings.csv exists)
docker-compose exec analyzer python scripts/process_and_upload_datasets.py --upload

# Full process: generate embeddings and upload
docker-compose exec analyzer python scripts/process_and_upload_datasets.py --generate --upload --clear

# Batch processing with custom batch size
docker-compose exec analyzer python scripts/process_and_upload_datasets.py --generate --upload --batch-size 50

# Non-interactive mode (skip confirmations)
docker-compose exec analyzer python scripts/process_and_upload_datasets.py --upload --clear --no-confirm
```

**Git LFS Troubleshooting**: If the embeddings file wasn't downloaded properly:
```bash
# Verify LFS installation
git lfs version

# Download LFS files manually
git lfs pull

# Check file size
ls -lh analyzer/scripts/chunks_with_embeddings.csv
```

## 📚 API Documentation

### Available Endpoints

#### Analyzer API (Port 8001)
- **GET /health**: Health check with database connectivity status
- **POST /api/v1/retrieve-chunk**: Semantic document chunk retrieval with configurable similarity functions
- **POST /api/v1/retrieve-rules**: Semantic retrieval of unique legal rules
- **POST /api/v1/analyze**: Legal document analysis with risk assessment
- **POST /api/v1/embed**: Text embedding generation
- **GET /api/v1/metrics/retrieval**: Embedding quality metrics
- **GET /docs**: Interactive API documentation

#### Backend API (Port 8000)
- **POST /api/v1/get_analysis**: Document upload and analysis orchestration
- **GET /api/v1/health**: Service health check

### API Usage Examples

#### Retrieval
```bash
curl -X POST "http://localhost:8001/api/v1/retrieve-rules" \
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

#### Retrieval Metrics
```bash
curl -X GET "http://localhost:8001/api/v1/metrics/retrieval"
```

## 🔍 Legal Dataset Details

The platform includes a comprehensive chunked Civil Code dataset:
- **190,846 legal rules** with complete metadata
- **413,453 text chunks** with optimized 800-character chunks and 500-character overlap
- **BAAI/bge-m3 embeddings** (1024-dimensional) for high-quality semantic understanding
- **Structured relationships** between rules and their constituent chunks
- **Memory-optimized processing** with batch generation and streaming

### Dataset Processing Pipeline
1. **Rules Extraction**: Legal articles parsed from source documents
2. **Text Chunking**: Rules split into overlapping chunks for better semantic coverage
3. **Embedding Generation**: Each chunk encoded using BAAI/bge-m3 model
4. **Database Upload**: Rules and chunks stored with proper foreign key relationships

## 🚧 Troubleshooting

### Common Issues

**Memory Issues During Embedding Generation:**
```bash
# Use smaller batch sizes
docker-compose exec analyzer python scripts/process_and_upload_datasets.py --generate --batch-size 10

# Monitor memory usage
docker stats
```

**Database Connection Issues:**
```bash
# Check database container status
docker-compose ps postgres

# Restart database
docker-compose restart postgres

# Check logs
docker-compose logs postgres
```

**Missing Dataset Files:**
```bash
# Verify files are in place
docker-compose exec analyzer ls -la scripts/datasets/*.csv

# Copy files if missing (from host)
docker cp parser/dataset/dataset_codes_rf.csv $(docker-compose ps -q analyzer):/app/scripts/datasets/rules_dataset.csv
docker cp experiments/dataset_codes_rf_chunking_800chunksize_500overlap.csv $(docker-compose ps -q analyzer):/app/scripts/datasets/chunks_dataset.csv
```

### Performance Optimization

**For faster embedding generation:**
- Increase batch size: `--batch-size 200` (if you have enough memory)
- Use GPU if available (requires CUDA-enabled Docker setup)
- Pre-generate embeddings on a more powerful machine and transfer the `chunks_with_embeddings.csv` file

**For production deployment:**
- Use external PostgreSQL with more memory
- Implement connection pooling
- Add Redis for caching frequently accessed chunks

## 📊 MVP Implementation Status

### ✅ Completed and Ready
- **Full Web Application** with complete UI workflow
- **Document Upload & Analysis** with file processing pipeline
- **Chunked Vector Database** with 413,000+ text chunks and embeddings
- **Semantic Search** with configurable similarity functions on document level
- **REST API** with comprehensive endpoints and Swagger documentation
- **Docker Deployment** with full service orchestration
- **Real-time Processing** with status updates and progress tracking
- **Error Handling** with comprehensive validation and user feedback
- **Unified Data Processing** with flexible embedding generation and upload

### 🎯 Future Enhancements
- **User Management**: Authentication and personalized document history
- **Advanced Analytics**: Legal precedent analysis and case law integration
- **Deployment**: Production-ready configuration with monitoring and scaling
- **Chat-based document management system**: Interactive legal consultation interface

## 🚀 Ready for Production

This MVP provides a solid foundation for a legal tech platform with:
- **Scalable Architecture**: Microservices ready for horizontal scaling
- **Production APIs**: Comprehensive error handling and validation
- **Legal Domain Expertise**: Purpose-built for Russian legal document analysis with chunk-level precision
- **Modern Tech Stack**: Latest frameworks and AI integration patterns
- **Docker Deployment**: Consistent environments across development and production
- **Optimized Vector Search**: Chunk-based retrieval for improved relevance and performance

**Start analyzing legal documents today!** Upload your first document at [http://localhost:8080](http://localhost:8080) after following the Quick Start guide.

For detailed analyzer-specific documentation, see [`analyzer/README.md`](analyzer/README.md).