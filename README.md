# SmartClause

Smart Clause is an AI-powered legal document analysis platform focused on Russian legal market and legislation with a comprehensive chat-based document management system. The platform leverages RAG (Retrieval-Augmented Generation) technology with legal vector databases to provide intelligent document analysis and interactive consultation capabilities.

## Architecture

The platform consists of multiple microservices:
- **Frontend**: Vue.js application for user interface
- **Backend**: FastAPI main application 
- **Analyzer**: RAG-based legal document analysis microservice
- **Parser**: Civil Code dataset processing and extraction tools

## Prerequisites

- Docker
- Docker Compose

## How to run

1.  Clone the repository.
2.  Open a terminal in the root directory of the project.
3.  Run the following command:

    ```sh
    docker-compose up --build -d
    ```

4.  The frontend will be available at [http://localhost:8080](http://localhost:8080).
5.  The backend will be available at [http://localhost:8000](http://localhost:8000).
6. The analyzer microservice will be available at [http://localhost:8001](http://localhost:8001).

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

See [`analyzer/scripts/README.md`](analyzer/scripts/README.md) for detailed documentation.