# SmartClause API Documentation

Welcome to the SmartClause API documentation. SmartClause is a comprehensive legal document analysis platform that uses AI to identify risks, provide recommendations, and offer interactive legal assistance.

## Architecture Overview

SmartClause is built with a microservices architecture consisting of:

- **Backend Service** (Java/Spring Boot) - Main API gateway and business logic
- **Analyzer Service** (Python/FastAPI) - Document analysis and legal retrieval
- **Chat Service** (Python/FastAPI) - AI-powered legal chat assistance
- **Frontend** (Vue.js) - Web interface

## API Services Documentation

### [Backend Service API](./backend-api.md)
- Authentication and user management
- Document and space management  
- Analysis orchestration
- Health monitoring
- **Base URL**: `http://localhost:8000`

### [Analyzer Service API](./analyzer-api.md)
- Document analysis and risk assessment
- Legal rule retrieval
- Text embedding generation
- PDF export functionality
- **Base URL**: `http://localhost:8001`

### [Chat Service API](./chat-api.md) 
- Interactive legal assistance
- Conversation management
- Session configuration
- **Base URL**: `http://localhost:8002`

## Quick Start Guides

- [Authentication Guide](./authentication.md) - JWT-based authentication system
- [Getting Started](./getting-started.md) - Basic usage and setup
- [Error Handling](./error-handling.md) - Common errors and troubleshooting

## Authentication

All APIs use JWT-based authentication. Tokens can be provided via:
- HTTP-only cookies (`smartclause_token`)
- Authorization header (`Bearer <token>`)

Some endpoints support public access for demo purposes.

## Rate Limiting

The platform implements rate limiting based on user authentication status:
- **Authenticated users**: Higher limits for document analysis and chat
- **Anonymous users**: Limited access for public demo

## Support

For additional support or questions:
- Review the individual service documentation
- Check the [error handling guide](./error-handling.md)
- Refer to the main [project README](../README.md)

---

*Last updated: January 2025* 