# SmartClause Chat Microservice

A FastAPI-based chat microservice that provides intelligent legal assistance by integrating with the SmartClause analyzer and document analysis systems.

## Features

- **Intelligent Legal Chat**: AI-powered responses using legal context and document analysis
- **Memory Management**: Configurable conversation history with context windows
- **Legal Database Integration**: Retrieves relevant legal rules and document chunks
- **Space-based Conversations**: Separate chat sessions for different document spaces
- **JWT Authentication**: Token-based user authentication
- **Real-time Responses**: Async processing for fast response times
- **Multiple LLM Models**: Support for various AI models via OpenRouter

## API Endpoints

### Chat Messages
- `GET /api/v1/spaces/{space_id}/messages` - Get chat messages for a space
- `POST /api/v1/spaces/{space_id}/messages` - Send a message to chat

### Session Management
- `GET /api/v1/spaces/{space_id}/session` - Get chat session info
- `PUT /api/v1/spaces/{space_id}/session/memory` - Update memory length

### Health Check
- `GET /api/v1/health` - Service health status

## Environment Variables

Copy `env.example` to `.env` and configure:

```bash
# Database (simplified single URL)
DATABASE_URL=postgresql+asyncpg://user:password@postgres:5432/chatdb

# LLM Configuration
OPENROUTER_API_KEY=your_openrouter_api_key_here
LLM_MODEL=anthropic/claude-3.5-sonnet
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2000

# Service URLs
ANALYZER_BASE_URL=http://analyzer:8001/api/v1
```

### Available LLM Models

Choose from various models via `LLM_MODEL` environment variable:

**Recommended:**
- `anthropic/claude-3.5-sonnet` - Best quality, legal reasoning
- `anthropic/claude-3-haiku` - Faster, cheaper alternative

**OpenAI:**
- `openai/gpt-4o` - Latest GPT-4 model
- `openai/gpt-3.5-turbo` - Cost-effective option

**Others:**
- `google/gemini-pro` - Google's latest model
- `meta-llama/llama-3.1-70b-instruct` - Open source option

## Setup

### Docker Compose (Recommended)
```bash
# From project root
docker-compose up chat
```

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp env.example .env
# Edit .env with your configuration

# Run the service
uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
```

## Usage Example

### Send a Message
```bash
curl -X POST "http://localhost:8002/api/v1/spaces/{space_id}/messages" \
  -H "Authorization: Bearer your_token" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "What are the key risks in this employment contract?",
    "type": "user"
  }'
```

### Get Messages
```bash
curl -X GET "http://localhost:8002/api/v1/spaces/{space_id}/messages?limit=10&offset=0" \
  -H "Authorization: Bearer your_token"
```

## Architecture

The chat service integrates with:

1. **Analyzer Service** (`/retrieve-rules`, `/retrieve-chunk`) - Legal context retrieval
2. **PostgreSQL Database** - Message and session storage
3. **OpenRouter API** - LLM-powered response generation
4. **Backend Service** - User authentication and space management

## Memory Management

The chat service maintains conversation context with configurable memory:

- **Default Memory**: 10 messages
- **Maximum Memory**: 20 messages (configurable)
- **Context Window**: Recent messages + legal context + document analysis

## Response Generation Process

1. **User Message**: Receive and validate user input
2. **Context Retrieval**: Get relevant legal rules and document chunks
3. **Memory Loading**: Load recent conversation history
4. **LLM Generation**: Generate response using context and history
5. **Response Storage**: Save both user and assistant messages

## Database Schema

### chat_messages
- `id` (UUID) - Message identifier
- `space_id` (UUID) - Associated space
- `user_id` (String) - User identifier  
- `content` (Text) - Message content
- `type` (Enum) - 'user' or 'assistant'
- `metadata` (JSON) - Document references and context
- `sequence_number` (Integer) - Message ordering
- `timestamp` (DateTime) - Creation time

### chat_sessions  
- `id` (UUID) - Session identifier
- `space_id` (UUID) - Associated space (unique)
- `user_id` (String) - User identifier
- `memory_length` (Integer) - Context window size
- `created_at`, `updated_at` (DateTime) - Timestamps

## Configuration

### Database Configuration
Simple single URL format:
```bash
DATABASE_URL=postgresql+asyncpg://user:password@host:port/database
```

### LLM Configuration
Fine-tune AI responses:
```bash
LLM_MODEL=anthropic/claude-3.5-sonnet  # Model choice
LLM_TEMPERATURE=0.7                    # Creativity (0.0-1.0)
LLM_MAX_TOKENS=2000                    # Response length limit
```

## Error Handling

- **Authentication Errors**: 401 Unauthorized
- **Validation Errors**: 400 Bad Request  
- **Service Errors**: 500 Internal Server Error
- **Fallback Responses**: When LLM/analyzer unavailable

## Monitoring

Check service health at `/api/v1/health`:
- Database connectivity
- Analyzer service status
- Overall service health

## Development

### Adding New Features
1. Update models in `app/models/database.py`
2. Add schemas in `app/schemas/`
3. Implement services in `app/services/`
4. Add routes in `app/api/routes.py`

### Testing
```bash
# Run tests (when implemented)
pytest tests/

# Manual API testing
curl http://localhost:8002/api/v1/health
```

## Deployment

The service is designed for containerized deployment with:
- Docker multi-stage builds
- Health checks
- Graceful shutdown
- Volume mounts for development

## License

Part of the SmartClause legal document analysis platform. 