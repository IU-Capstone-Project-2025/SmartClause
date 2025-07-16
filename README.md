# SmartClause - AI-Powered Legal Document Analysis Platform

**🚀 MVP Ready!** SmartClause is a complete AI-powered legal document analysis platform focused on the Russian legal market. The platform leverages RAG (Retrieval-Augmented Generation) technology with legal vector databases to provide intelligent document analysis and interactive legal consultation capabilities. It includes secure user registration and authentication, allowing users to manage their documents in private spaces.

## 🎯 What You Can Do

**Ready to use out of the box:**
- **🔐 Secure User Authentication**: Register and log in to a secure account to protect your data.
- **📄 Upload and Analyze Documents**: Upload legal documents (up to 10MB) and get AI-powered risk analysis and recommendations.
- **💬 Interactive Legal Chat**: Ask questions about your documents and get AI-powered legal advice with conversation memory.
- **🔍 Semantic Legal Search**: Search through a comprehensive Civil Code database using natural language queries.
- **💻 Interactive Web Interface**: Complete workflow from document upload to analysis and consultation.
- **⚡ Real-time Processing**: Watch your documents being processed with live status updates.
- **🔗 REST API Access**: Full programmatic access to all analysis and chat capabilities.

## ✨ Key Features

### 🔐 User Authentication & Security
- **Secure Registration**: Create user accounts with encrypted password storage.
- **JWT-Based Authentication**: Secure authentication using JSON Web Tokens (JWT) stored in HTTP-only cookies.
- **Protected Endpoints**: Role-based access control for all sensitive operations.
- **Profile Management**: Users can view and update their profile information and change passwords.

### 📋 Document Analysis Pipeline
- **Smart Upload Interface**: Drag-and-drop document upload with progress tracking.
- **AI-Powered Analysis**: Legal document analysis for risks, compliance issues, and recommendations
- **Comprehensive Results**: Detailed analysis with causes, risks, and actionable recommendations
- **Multiple File Formats**: Support for text files and structured documents

### 💬 AI Legal Consultation
- **Intelligent Chat Interface**: Interactive legal assistant with conversation memory and context awareness
- **Document-Aware Responses**: AI answers incorporate analysis from your uploaded documents
- **Legal Context Integration**: Responses backed by relevant legal rules and document excerpts
- **Configurable Memory**: Adjustable conversation context window (1-50 messages)

### 📚 Legal Knowledge Base
- **Chunked Civil Code Database**: Complete Russian Civil Code with 190,000+ rules and 413,000+ text chunks with embeddings
- **Semantic Search**: Vector-based similarity search using BAAI/bge-m3 embeddings on text chunks
- **Configurable Retrieval**: Multiple distance functions (cosine, L2, inner product)
- **Structured Metadata**: Articles organized by sections, chapters, and legal references with precise chunk positioning

### 🛠️ Technology Stack
- **Frontend**: Vue.js 3 with modern UI components and routing
- **Backend**: Spring Boot REST API with Swagger documentation
- **AI Engine**: FastAPI microservice with LangChain and OpenRouter integration
- **Chat Service**: FastAPI microservice for intelligent legal consultation with memory management
- **Database**: PostgreSQL with pgvector extension for vector operations
- **LLM Integration**: Google Gemini 2.5 Flash via OpenRouter for analysis and chat generation
- **Embeddings**: BAAI/bge-m3 sentence transformer for semantic understanding
- **Deployment**: Docker Compose orchestration for easy setup

## 🚀 Quick Start

### Prerequisites
- **Docker and Docker Compose** (required)
- **Python 3.8+** (for dataset download script)
- **OpenRouter API Key** ([Get one here](https://openrouter.ai/))
- **Internet Connection** (for downloading datasets from Hugging Face)

### 1. Clone Repository

```bash
# Clone the repository
git clone https://github.com/your-username/SmartClause.git
cd SmartClause
```

### 2. Download Required Datasets
```bash
# Download datasets from Hugging Face Hub (~1.2GB total)
python analyzer/scripts/download_datasets.py

# Or force re-download if files exist
python analyzer/scripts/download_datasets.py --force
```

**📊 Dataset Information:**
- **Source:** [Hugging Face Hub - narly/russian-codexes-bge-m3](https://huggingface.co/datasets/narly/russian-codexes-bge-m3)
- **Content:** Russian legal codes with BGE-M3 embeddings
- **Size:** Download script automatically detects current file sizes

### 3. Configure Environment

```bash
# Copy environment templates for both services
cp analyzer/env.example analyzer/.env
cp chat/env.example chat/.env

# Edit both .env files and add your OpenRouter API key
# Replace 'your_openrouter_api_key_here' with actual key
```

**Required configuration in `analyzer/.env`:**
```bash
OPENROUTER_API_KEY=your_actual_api_key_here
JWT_SECRET=your_jwt_secret_here
```

**Required configuration in `chat/.env`:**
```bash
OPENROUTER_API_KEY=your_actual_api_key_here
JWT_SECRET=your_jwt_secret_here
```

### 4. Launch the Platform

```bash
# Build and start all services (first launch may take 10-15 minutes)
docker-compose up --build -d

# Monitor the startup process
docker-compose logs -f
```

**Note**: The first launch will download the BAAI/bge-m3 model (~2GB) and may take some time.

### 5. Initialize Database and Load Legal Dataset

**Option A: Quick Setup (Recommended)**
```bash
# Load the complete legal dataset (413k+ chunks with embeddings)
docker-compose exec analyzer python scripts/process_and_upload_datasets.py --upload --clear

# For systems with limited RAM, use smaller chunk sizes:
docker-compose exec analyzer python scripts/process_and_upload_datasets.py --upload --clear --csv-chunk-size 50
```

**Option B: Generate Embeddings from Scratch**
Only if you don't have the pre-generated embeddings file:
```bash
# Generate embeddings (takes 1-2 hours)
docker-compose exec analyzer python scripts/process_and_upload_datasets.py --generate

# Upload to database
docker-compose exec analyzer python scripts/process_and_upload_datasets.py --upload --clear
```

### 6. Access the Application

Once setup is complete, access these URLs:

- **🌐 Web Application**: [http://localhost:8080](http://localhost:8080) - Main user interface
- **📋 Backend API**: [http://localhost:8000](http://localhost:8000) - Main API Gateway
- **🔍 AI Analysis API**: [http://localhost:8001](http://localhost:8001) - RAG and analysis API
- **💬 Chat API**: [http://localhost:8002](http://localhost:8002) - Legal consultation API
- **📚 API Documentation**: 
  - [http://localhost:8000/swagger-ui/index.html](http://localhost:8000/swagger-ui/index.html) - Backend API docs
  - [http://localhost:8001/docs](http://localhost:8001/docs) - Analysis API docs
  - [http://localhost:8002/docs](http://localhost:8002/docs) - Chat API docs

**🎉 You're ready to analyze legal documents!**

## 🖥️ System Architecture

The platform provides a complete web interface with three main screens:

1. **Upload Screen**: Drag-and-drop interface for document upload
2. **Processing Screen**: Real-time processing status with progress indicators  
3. **Results Screen**: Comprehensive analysis results with risks and recommendations

### Service Architecture
- **Frontend** (Port 8080): Vue.js SPA with upload, processing, results, and chat interfaces
- **Backend** (Port 8000): Spring Boot API Gateway handling document management and chat proxy
- **Analyzer** (Port 8001): FastAPI microservice with RAG pipeline and LLM integration
- **Chat** (Port 8002): FastAPI microservice for legal consultation with conversation memory
- **Database** (Port 5432): PostgreSQL with pgvector for vector similarity search and chat history

## 📊 Database Structure

The optimized database structure separates rules metadata from searchable chunks:

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

The system uses datasets downloaded from [Hugging Face Hub](https://huggingface.co/datasets/narly/russian-codexes-bge-m3) and stored in the project root `datasets/` directory:

- **`rules_dataset.csv`**: Complete legal rules metadata (190,846 rules)
- **`chunks_dataset.csv`**: Text chunks for embedding (413,453 chunks)  
- **`chunks_with_embeddings.csv`**: Pre-generated BGE-M3 embeddings (413,453 vectors)

**🚀 Easy Download**: Files are automatically downloaded using the provided script:
```bash
python analyzer/scripts/download_datasets.py
```

**📊 Dataset Details:**
- **Source Repository**: [narly/russian-codexes-bge-m3](https://huggingface.co/datasets/narly/russian-codexes-bge-m3)
- **Embedding Model**: BAAI/bge-m3 (1024 dimensions)
- **Content**: Russian Civil Codes parsed and chunked for semantic search

## 📚 API Documentation

Comprehensive API documentation is available in the `docs/` folder:

- **[API Overview](docs/README.md)**: Complete guide to all services and endpoints
- **[Backend API](docs/backend-api.md)**: Main Spring Boot API Gateway documentation
- **[Analyzer API](docs/analyzer-api.md)**: AI analysis and retrieval service
- **[Chat API](docs/chat-api.md)**: Legal consultation and conversation management
- **[Authentication Guide](docs/authentication.md)**: JWT implementation and security
- **[Getting Started](docs/getting-started.md)**: Quick start guide for developers
- **[Error Handling](docs/error-handling.md)**: Comprehensive error scenarios and recovery

Interactive API documentation is also available via Swagger UI:
- **Backend API**: [http://localhost:8000/swagger-ui/index.html](http://localhost:8000/swagger-ui/index.html)
- **Analyzer API**: [http://localhost:8001/docs](http://localhost:8001/docs)
- **Chat API**: [http://localhost:8002/docs](http://localhost:8002/docs)

## 🔧 Configuration

### Environment Variables

The environment files support these key configuration options:

#### Analyzer Service (`analyzer/.env`)
```bash
# Required
OPENROUTER_API_KEY=your_openrouter_api_key_here
JWT_SECRET=your_jwt_secret_here

# Model Configuration
OPENROUTER_MODEL=google/gemini-2.5-flash-lite-preview-06-17
EMBEDDING_MODEL=BAAI/bge-m3
EMBEDDING_DIMENSION=1024

# Performance Settings
MAX_FILE_SIZE=10485760              # 10MB file upload limit
DEFAULT_K=5                         # Default retrieval count
MAX_K=20                           # Maximum retrieval count
LLM_TIMEOUT=90                     # LLM API timeout (seconds)
MAX_RETRIES=3                      # Retry attempts
```

#### Chat Service (`chat/.env`)
```bash
# Required
OPENROUTER_API_KEY=your_openrouter_api_key_here
JWT_SECRET=your_jwt_secret_here

# LLM Configuration
LLM_MODEL=google/gemini-2.5-flash-lite-preview-06-17
LLM_TEMPERATURE=0.7                 # Response creativity (0.0-1.0)
LLM_MAX_TOKENS=2000                # Maximum response length

# Chat Settings
MAX_MEMORY_MESSAGES=20             # Maximum conversation context
DEFAULT_MEMORY_MESSAGES=10         # Default conversation context
```

### Dataset Processing Options

The unified script `process_and_upload_datasets.py` provides flexible options:

```bash
# Upload existing embeddings (recommended)
docker-compose exec analyzer python scripts/process_and_upload_datasets.py --upload --clear

# Generate embeddings from scratch (takes ~1 hour)
docker-compose exec analyzer python scripts/process_and_upload_datasets.py --generate --upload --clear

# For systems with limited RAM
docker-compose exec analyzer python scripts/process_and_upload_datasets.py --upload --clear --csv-chunk-size 50
```

## 🚧 Troubleshooting

### Common Issues

#### Dataset Download Problems
```bash
# Re-download all datasets
python analyzer/scripts/download_datasets.py --force

# Check if datasets exist and verify sizes
ls -lh datasets/

# The script will show actual file sizes when run
# Sizes are automatically detected from remote files

# If download fails, check internet connection and try again
curl -I https://huggingface.co/datasets/narly/russian-codexes-bge-m3/resolve/main/rules_dataset.csv
```

#### Memory Issues During Embedding Generation
```bash
# Use smaller batch sizes
docker-compose exec analyzer python scripts/process_and_upload_datasets.py --generate --batch-size 10

# Monitor memory usage during upload
docker stats

# For very low-memory systems, use even smaller settings
docker-compose exec analyzer python scripts/process_and_upload_datasets.py --upload --clear --csv-chunk-size 250 --batch-size 25

# For embedding generation on low-memory systems, use smaller batch sizes
docker-compose exec analyzer python scripts/process_and_upload_datasets.py --generate --batch-size 10
```

#### Database Connection Issues
```bash
# Check database container status
docker-compose ps postgres

# View database logs
docker-compose logs postgres

# Restart database service
docker-compose restart postgres

# Reset database completely
docker-compose down -v
docker-compose up postgres -d
```

#### Service Startup Issues
```bash
# Check all service logs
docker-compose logs

# Check specific service
docker-compose logs analyzer
docker-compose logs chat
docker-compose logs backend

# Rebuild containers if needed
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

#### Chat Service Issues
```bash
# Check chat service health
curl http://localhost:8002/api/v1/health

# Check chat service via backend gateway
curl http://localhost:8000/api/health

# Verify chat environment configuration
docker-compose exec chat env | grep OPENROUTER

# Check chat database connectivity
docker-compose logs chat | grep -i database

# Restart chat service
docker-compose restart chat
```

#### Missing Dataset Files
```bash
# Verify dataset files exist
ls -la datasets/

# If files are missing, download them:
python analyzer/scripts/download_datasets.py

# Verify download completed successfully
ls -lh datasets/chunks_with_embeddings.csv

# Should show the embeddings file with substantial size
```

#### API Key Issues
```bash
# Verify environment file exists
ls -la analyzer/.env

# Check if API key is properly set
docker-compose exec analyzer env | grep OPENROUTER

# Test API key directly
curl -H "Authorization: Bearer YOUR_API_KEY" https://openrouter.ai/api/v1/models
```

### Performance Optimization

**For faster embedding generation:**
- Use larger batch sizes: `--batch-size 200` (if you have sufficient memory)
- Use a machine with more CPU cores and RAM
- For production: Use GPU-enabled Docker setup with CUDA

**For production deployment:**
- Use external PostgreSQL with more memory and SSD storage
- Implement Redis for caching frequently accessed chunks
- Use a CDN for static assets
- Enable gzip compression
- Set up horizontal scaling with load balancers

## 🔍 Legal Dataset Details

The platform includes a comprehensive chunked Civil Code dataset:

- **190,846 legal rules** with complete metadata and hierarchical structure
- **413,453 text chunks** with optimized 800-character chunks and 500-character overlap
- **BAAI/bge-m3 embeddings** (1024-dimensional) for high-quality semantic understanding
- **Structured relationships** between rules and their constituent chunks
- **Memory-optimized processing** with batch generation and streaming upload

### Dataset Processing Pipeline
1. **Rules Extraction**: Legal articles parsed from source documents with metadata
2. **Text Chunking**: Rules split into overlapping chunks for comprehensive semantic coverage
3. **Embedding Generation**: Each chunk encoded using BAAI/bge-m3 model with batch processing
4. **Database Upload**: Rules and chunks stored with proper foreign key relationships and indexing

## 🎯 Project Status

### ✅ Current Features
- **🔐 User Authentication**: Complete JWT-based authentication system with secure registration and login
- **🌐 Web Application**: Full-featured Vue.js interface with upload, processing, results, and chat screens
- **📄 Document Analysis**: AI-powered legal document analysis with risk assessment and recommendations
- **💬 Interactive Chat**: Legal consultation with conversation memory and document-aware responses
- **🔍 Semantic Search**: Vector-based search through 413,000+ legal text chunks with BGE-M3 embeddings
- **🏗️ Microservices Architecture**: Spring Boot backend, FastAPI analyzer and chat services
- **🗄️ Vector Database**: PostgreSQL with pgvector extension for similarity search
- **🐳 Docker Deployment**: Complete containerization with Docker Compose orchestration
- **📚 Comprehensive Documentation**: Complete API docs and setup guides

### 🔍 Legal Knowledge Base
- **190,846 legal rules** from Russian Civil Code with complete metadata
- **413,453 text chunks** with BAAI/bge-m3 embeddings for semantic search
- **Structured relationships** between rules and chunks for precise retrieval
- **Optimized chunking** with 800-character chunks and 500-character overlap

### 🛠️ Technology Highlights
- **AI Integration**: Google Gemini 2.5 Flash via OpenRouter for analysis and chat
- **Vector Embeddings**: BAAI/bge-m3 sentence transformers (1024 dimensions)
- **Scalable Architecture**: RESTful microservices with API gateway pattern
- **Production Ready**: Comprehensive error handling, validation, and security measures

**🚀 Ready to Use**: Follow the Quick Start guide to set up your local instance and start analyzing legal documents at [http://localhost:8080](http://localhost:8080)!