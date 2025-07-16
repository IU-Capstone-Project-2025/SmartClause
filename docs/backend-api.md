# Backend Service API

The Backend Service is the main API gateway for SmartClause, built with Java Spring Boot. It handles authentication, document management, space management, and orchestrates communication with other microservices.

**Base URL**: `http://localhost:8000`

## Table of Contents

- [Authentication Endpoints](#authentication-endpoints)
- [Document Management](#document-management)
- [Space Management](#space-management)
- [Chat Gateway](#chat-gateway)
- [Analysis Endpoints](#analysis-endpoints)
- [Health & Monitoring](#health--monitoring)
- [Rate Limiting](#rate-limiting)

## Authentication Endpoints

### POST /api/auth/register

Register a new user account.

**Request Body:**
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "securepassword123",
  "first_name": "John",
  "last_name": "Doe"
}
```

**Response (201):**
```json
{
  "message": "User registered successfully",
  "user": {
    "id": "user-uuid",
    "username": "john_doe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "full_name": "John Doe",
    "role": "USER",
    "is_email_verified": false,
    "created_at": "2025-01-01T10:00:00",
    "last_login_at": null
  },
  "email_verification_required": true
}
```

### POST /api/auth/login

Authenticate user and receive JWT token in HTTP-only cookie.

**Request Body:**
```json
{
  "username_or_email": "john@example.com",
  "password": "securepassword123"
}
```

**Response (200):**
```json
{
  "access_token": "jwt-token-here",
  "token_type": "Bearer",
  "expires_in": 86400,
  "user": {
    "id": "user-uuid",
    "username": "john_doe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "full_name": "John Doe",
    "role": "USER",
    "is_email_verified": true,
    "created_at": "2025-01-01T10:00:00",
    "last_login_at": "2025-01-01T11:00:00"
  }
}
```

**Sets Cookie:** `smartclause_token` (HTTP-only, secure)

### GET /api/auth/profile

Get current user profile information.

**Headers:**
- `Authorization: Bearer <token>` (optional, will try cookies first)

**Response (200):**
```json
{
  "id": "user-uuid",
  "username": "john_doe",
  "email": "john@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "full_name": "John Doe",
  "role": "USER",
  "is_email_verified": true,
  "created_at": "2025-01-01T10:00:00",
  "last_login_at": "2025-01-01T11:00:00"
}
```

### PUT /api/auth/profile

Update user profile information.

**Headers:**
- `Authorization: Bearer <token>` (optional, will try cookies first)

**Request Body:**
```json
{
  "username": "john_doe_updated",
  "email": "john.updated@example.com",
  "first_name": "John",
  "last_name": "Doe Updated"
}
```

**Response (200):**
```json
{
  "id": "user-uuid",
  "username": "john_doe_updated",
  "email": "john.updated@example.com",
  "first_name": "John",
  "last_name": "Doe Updated",
  "full_name": "John Doe Updated",
  "role": "USER",
  "is_email_verified": true,
  "created_at": "2025-01-01T10:00:00",
  "last_login_at": "2025-01-01T11:00:00"
}
```

### DELETE /api/auth/account

Deactivate current user account.

**Headers:**
- `Authorization: Bearer <token>` (optional, will try cookies first)

**Response (200):**
```json
{
  "message": "Account deactivated successfully"
}
```

## Space Management

### GET /api/spaces

Get all spaces for the authenticated user.

**Headers:**
- `Authorization: Bearer <token>` (optional, will try cookies first)

**Response (200):**
```json
{
  "spaces": [
    {
      "id": "space-uuid",
      "name": "Legal Contracts Review",
      "description": "Space for contract analysis",
      "created_at": "2025-01-01T10:00:00",
      "documents_count": 5,
      "status": "active"
    }
  ]
}
```

### POST /api/spaces

Create a new document space.

**Headers:**
- `Authorization: Bearer <token>` (optional, will try cookies first)

**Request Body:**
```json
{
  "name": "New Legal Review Space",
  "description": "Space for analyzing employment contracts"
}
```

**Response (201):**
```json
{
  "space": {
    "id": "space-uuid",
    "name": "New Legal Review Space",
    "description": "Space for analyzing employment contracts",
    "created_at": "2025-01-01T10:00:00"
  }
}
```

### GET /api/spaces/{spaceId}

Get detailed information for a specific space.

**Headers:**
- `Authorization: Bearer <token>` (optional, will try cookies first)

**Response (200):**
```json
{
  "id": "space-uuid",
  "name": "Legal Contracts Review",
  "description": "Space for contract analysis",
  "created_at": "2025-01-01T10:00:00",
  "documents": [
    {
      "id": "doc-uuid",
      "name": "employment_contract.pdf",
      "status": "analyzed",
      "analysis_summary": "Contract contains 3 potential risks"
    }
  ]
}
```

### PUT /api/spaces/{spaceId}

Update space details.

**Headers:**
- `Authorization: Bearer <token>` (optional, will try cookies first)

**Request Body:**
```json
{
  "name": "Updated Space Name",
  "description": "Updated description"
}
```

**Response (200):**
```json
{
  "id": "space-uuid",
  "name": "Updated Space Name",
  "description": "Updated description",
  "created_at": "2025-01-01T10:00:00"
}
```

### DELETE /api/spaces/{spaceId}

Delete a space and all its documents.

**Headers:**
- `Authorization: Bearer <token>` (optional, will try cookies first)

**Response (200):**
```json
{
  "message": "Space deleted successfully"
}
```

## Document Management

### POST /api/spaces/{spaceId}/documents

Upload a document to a specific space.

**Headers:**
- `Authorization: Bearer <token>` (optional, will try cookies first)
- `Content-Type: multipart/form-data`

**Request Body (form-data):**
- `file`: Document file (PDF, DOCX, TXT)

**Response (201):**
```json
{
  "id": "doc-uuid",
  "name": "contract.pdf",
  "size": 1024000,
  "type": "application/pdf",
  "status": "uploaded",
  "uploaded_at": "2025-01-01T10:00:00"
}
```

### GET /api/spaces/{spaceId}/documents

Get all documents in a specific space.

**Headers:**
- `Authorization: Bearer <token>` (optional, will try cookies first)

**Response (200):**
```json
{
  "documents": [
    {
      "id": "doc-uuid",
      "name": "contract.pdf",
      "status": "analyzed",
      "analysis_summary": "Document contains 2 high-risk clauses"
    }
  ]
}
```

### GET /api/documents/{documentId}

Get detailed information for a specific document.

**Headers:**
- `Authorization: Bearer <token>` (optional, will try cookies first)

**Response (200):**
```json
{
  "id": "doc-uuid",
  "name": "contract.pdf",
  "content": "base64-encoded-content"
}
```

### DELETE /api/documents/{documentId}

Delete a specific document.

**Headers:**
- `Authorization: Bearer <token>` (optional, will try cookies first)

**Response (200):**
```json
{
  "message": "Document deleted successfully"
}
```

### GET /api/documents/{documentId}/analysis

Get analysis results for a document.

**Headers:**
- `Authorization: Bearer <token>` (optional, will try cookies first)

**Response (200):**
```json
{
  "document_points": [
    {
      "point_number": "1",
      "point_content": "The employee shall work 40 hours per week",
      "point_type": "numbered_clause",
      "analysis_points": [
        {
          "cause": "Standard working hours clause",
          "risk": "No overtime compensation mentioned",
          "recommendation": "Add clear overtime policy"
        }
      ]
    }
  ],
  "document_id": "doc-uuid",
  "document_metadata": {
    "word_count": 1500,
    "page_count": 3
  },
  "total_points": 1,
  "analysis_timestamp": "2025-01-01T10:00:00"
}
```

### POST /api/documents/{documentId}/reanalyze

Trigger re-analysis of a document.

**Headers:**
- `Authorization: Bearer <token>` (optional, will try cookies first)

**Response (200):**
```json
{
  "message": "Document re-analysis started",
  "analysis_id": "analysis-uuid"
}
```

### GET /api/documents/{documentId}/analysis/export

Export analysis results as PDF.

**Headers:**
- `Authorization: Bearer <token>` (optional, will try cookies first)

**Response (200):**
- Content-Type: `application/pdf`
- Content-Disposition: `attachment; filename=analysis_{documentId}.pdf`
- Binary PDF content

## Chat Gateway

### GET /api/spaces/{spaceId}/messages

Get chat messages for a space with pagination.

**Headers:**
- `Authorization: Bearer <token>` (optional, will try cookies first)

**Query Parameters:**
- `limit` (optional): Maximum messages to retrieve (default: 50, max: 100)
- `offset` (optional): Number of messages to skip (default: 0)

**Response (200):**
```json
{
  "messages": [
    {
      "id": "msg-uuid",
      "content": "What are the risks in this employment contract?",
      "type": "user",
      "timestamp": "2025-01-01T10:00:00",
      "metadata": {
        "document_references": [],
        "retrieval_context": null,
        "analysis_context": null
      }
    },
    {
      "id": "msg-uuid-2",
      "content": "Based on the analysis, I found 3 potential risks...",
      "type": "assistant",
      "timestamp": "2025-01-01T10:01:00",
      "metadata": {
        "document_references": [
          {
            "document_id": "doc-uuid",
            "relevance_score": 0.95
          }
        ],
        "retrieval_context": {
          "retrieved_rules": 5
        },
        "analysis_context": {
          "analysis_points": 3
        }
      }
    }
  ],
  "total_count": 25,
  "has_more": true
}
```

### POST /api/spaces/{spaceId}/messages

Send a message to space chat.

**Headers:**
- `Authorization: Bearer <token>` (optional, will try cookies first)

**Request Body:**
```json
{
  "content": "What are the main risks in the uploaded contract?"
}
```

**Response (200):**
```json
{
  "message": {
    "id": "msg-uuid",
    "content": "Based on my analysis of the contract, I identified 3 main risks...",
    "type": "assistant",
    "timestamp": "2025-01-01T10:01:00",
    "metadata": {
      "document_references": [
        {
          "document_id": "doc-uuid",
          "relevance_score": 0.95
        }
      ],
      "retrieval_context": {
        "retrieved_rules": 5
      },
      "analysis_context": {
        "analysis_points": 3
      }
    }
  }
}
```

## Analysis Endpoints

### POST /api/v1/get_analysis

Analyze a document (supports both authenticated and public access).

**Headers:**
- `Authorization: Bearer <token>` (optional for public demo access)

**Request Body (form-data):**
- `id`: Document identifier
- `bytes`: Document file (multipart/form-data)

**Response (200):**
```json
{
  "document_points": [
    {
      "point_number": "1",
      "point_content": "Payment terms: Net 30 days",
      "point_type": "numbered_clause",
      "analysis_points": [
        {
          "cause": "Extended payment terms",
          "risk": "Cash flow impact for service provider",
          "recommendation": "Consider shorter payment terms or early payment discount"
        }
      ]
    }
  ],
  "document_id": "temp-analysis-id",
  "document_metadata": {
    "word_count": 850,
    "page_count": 2
  },
  "total_points": 5,
  "analysis_timestamp": "2025-01-01T10:00:00"
}
```

## Health & Monitoring

### GET /api/v1/health

Check service health and connected microservices.

**Response (200):**
```json
{
  "status": "UP",
  "service": "SmartClause API",
  "timestamp": "2025-01-01T10:00:00",
  "chat_service": {
    "status": "healthy",
    "database_connected": true,
    "analyzer_connected": true
  }
}
```

## Rate Limiting

### GET /api/v1/rate-limit/status

Get current rate limit status for the requesting user.

**Headers:**
- `Authorization: Bearer <token>` (optional)

**Response (200):**
```json
{
  "userType": "authenticated",
  "userIdentifier": "user-12345...",
  "usage": {
    "minute": 5,
    "hour": 45,
    "day": 120
  },
  "remaining": {
    "minute": 55,
    "hour": 455,
    "day": 880
  }
}
```

### DELETE /api/v1/rate-limit/clear

Clear rate limit for current user (useful for testing).

**Headers:**
- `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "message": "Rate limit cleared successfully",
  "userIdentifier": "user-12345..."
}
```

## Error Responses

All endpoints may return these common error responses:

### 400 Bad Request
```json
{
  "error": "Invalid request data",
  "details": "Specific validation error message"
}
```

### 401 Unauthorized
```json
{
  "error": "Authentication required"
}
```

### 403 Forbidden
```json
{
  "error": "Access denied"
}
```

### 404 Not Found
```json
{
  "error": "Resource not found"
}
```

### 409 Conflict
```json
{
  "error": "Username or email already exists"
}
```

### 413 Payload Too Large
```json
{
  "error": "File size exceeds maximum allowed size"
}
```

### 429 Too Many Requests
```json
{
  "error": "Rate limit exceeded",
  "retry_after": 3600
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal server error",
  "message": "Detailed error message"
}
```

---

*For more information about authentication, see the [Authentication Guide](./authentication.md)* 