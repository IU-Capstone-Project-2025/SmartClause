# Chat Service API

The Chat Service provides AI-powered legal assistance through conversational interactions. Built with Python FastAPI, it offers intelligent chat capabilities with document context awareness, legal rule integration, and conversation memory management.

**Base URL**: `http://localhost:8002`

## Table of Contents

- [Authentication](#authentication)
- [Chat Messages](#chat-messages)
- [Session Management](#session-management)
- [Health Check](#health-check)
- [Usage Examples](#usage-examples)

## Authentication

All endpoints require authentication via Bearer token or login cookie. The chat service validates tokens with the backend service and maintains user-specific conversation contexts.

**Authentication Methods:**
- `Authorization: Bearer <token>` header
- `smartclause_token` HTTP-only cookie (preferred)

## Chat Messages

### GET /api/v1/spaces/{space_id}/messages

Retrieve chat messages for a specific space with pagination support.

**Authentication:** Required

**Path Parameters:**
- `space_id` (string): UUID of the space

**Query Parameters:**
- `limit` (integer, optional): Maximum messages to retrieve (1-100, default: 50)
- `offset` (integer, optional): Number of messages to skip (default: 0)

**Request Example:**
```bash
curl -X GET "http://localhost:8002/api/v1/spaces/123e4567-e89b-12d3-a456-426614174000/messages?limit=20&offset=0" \
  -H "Authorization: Bearer <token>"
```

**Response (200):**
```json
{
  "messages": [
    {
      "id": "msg-uuid-1",
      "content": "What are the main risks in the uploaded employment contract?",
      "type": "user",
      "timestamp": "2025-01-01T10:00:00.000Z",
      "metadata": {
        "document_references": [],
        "retrieval_context": null,
        "analysis_context": null
      }
    },
    {
      "id": "msg-uuid-2",
      "content": "Based on my analysis of the employment contract, I've identified 3 main legal risks:\n\n1. **Termination Clause Risk**: The contract lacks specific termination procedures...\n2. **Intellectual Property Concerns**: IP ownership rights are not clearly defined...\n3. **Compensation Structure**: The payment terms exceed industry standards...",
      "type": "assistant",
      "timestamp": "2025-01-01T10:00:30.000Z",
      "metadata": {
        "document_references": [
          {
            "document_id": "doc-uuid-123",
            "relevance_score": 0.95,
            "document_name": "employment_contract.pdf"
          }
        ],
        "retrieval_context": {
          "retrieved_rules": 5,
          "top_similarity": 0.87,
          "search_query": "employment contract termination intellectual property"
        },
        "analysis_context": {
          "analysis_points": 3,
          "risk_level": "medium",
          "processing_time": 2.45
        }
      }
    }
  ],
  "total_count": 15,
  "has_more": true
}
```

### POST /api/v1/spaces/{space_id}/messages

Send a message to the chat and receive an AI-generated response.

**Authentication:** Required

**Path Parameters:**
- `space_id` (string): UUID of the space

**Request Body:**
```json
{
  "content": "Can you explain the liability limitations in clause 8 of the contract?",
  "type": "user"
}
```

**Request Example:**
```bash
curl -X POST "http://localhost:8002/api/v1/spaces/123e4567-e89b-12d3-a456-426614174000/messages" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "What should I negotiate in this service agreement?",
    "type": "user"
  }'
```

**Response (200):**
```json
{
  "message": {
    "id": "msg-uuid-3",
    "content": "Based on the service agreement you've uploaded, here are the key areas I recommend focusing on during negotiations:\n\n**1. Payment Terms**\n- Current: 45-day payment terms\n- Recommendation: Negotiate to 15-30 days\n- Risk: Extended terms can impact cash flow\n\n**2. Liability Limitations**\n- Current: Broad liability exclusions\n- Recommendation: Add mutual liability caps\n- Consider professional indemnity requirements\n\n**3. Termination Rights**\n- Current: Limited termination for convenience\n- Recommendation: Add 30-day termination clause\n- Include data return provisions\n\nWould you like me to elaborate on any of these points?",
    "type": "assistant",
    "timestamp": "2025-01-01T10:05:00.000Z",
    "metadata": {
      "document_references": [
        {
          "document_id": "doc-uuid-456",
          "relevance_score": 0.92,
          "document_name": "service_agreement.pdf",
          "referenced_clauses": ["payment_terms", "liability", "termination"]
        }
      ],
      "retrieval_context": {
        "retrieved_rules": 7,
        "top_similarity": 0.89,
        "search_query": "service agreement payment liability termination negotiation",
        "legal_precedents": 3
      },
      "analysis_context": {
        "analysis_points": 3,
        "risk_level": "medium-high",
        "confidence_score": 0.88,
        "processing_time": 3.12,
        "llm_model": "gpt-4"
      }
    }
  }
}
```

**AI Response Features:**
- **Document-Aware**: References specific uploaded documents
- **Legal Context**: Incorporates relevant legal rules and precedents
- **Risk Assessment**: Provides risk evaluation and recommendations
- **Structured Output**: Well-organized, actionable advice
- **Follow-up Ready**: Designed for continued conversation

## Session Management

### GET /api/v1/spaces/{space_id}/session

Get chat session configuration and metadata.

**Authentication:** Required

**Path Parameters:**
- `space_id` (string): UUID of the space

**Response (200):**
```json
{
  "session_id": "session-uuid-123",
  "space_id": "123e4567-e89b-12d3-a456-426614174000",
  "memory_length": 10,
  "created_at": "2025-01-01T09:00:00.000Z",
  "updated_at": "2025-01-01T10:05:00.000Z"
}
```

**Session Properties:**
- `session_id`: Unique identifier for the chat session
- `space_id`: Associated space UUID
- `memory_length`: Number of messages kept in conversation context
- `created_at`: Session creation timestamp
- `updated_at`: Last activity timestamp

### PUT /api/v1/spaces/{space_id}/session/memory

Update chat memory configuration to control conversation context length.

**Authentication:** Required

**Path Parameters:**
- `space_id` (string): UUID of the space

**Request Body:**
```json
{
  "memory_length": 15
}
```

**Parameters:**
- `memory_length` (integer): Number of messages to keep in context (1-50)

**Response (200):**
```json
{
  "session_id": "session-uuid-123",
  "space_id": "123e4567-e89b-12d3-a456-426614174000",
  "memory_length": 15,
  "created_at": "2025-01-01T09:00:00.000Z",
  "updated_at": "2025-01-01T10:10:00.000Z"
}
```

**Memory Length Guidelines:**
- **Short (1-5)**: Quick Q&A, minimal context
- **Medium (6-15)**: Balanced conversation flow
- **Long (16-50)**: Extended analysis discussions

## Health Check

### GET /api/v1/health

Check chat service health and connected services status.

**Authentication:** Not required

**Response (200):**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database_connected": true,
  "analyzer_connected": true,
  "backend_connected": true
}
```

**Status Values:**
- `healthy`: All services operational
- `degraded`: Partial functionality available
- `unhealthy`: Service issues detected

**Connected Services:**
- `database_connected`: PostgreSQL connection status
- `analyzer_connected`: Analyzer service availability
- `backend_connected`: Backend service connectivity

## Message Metadata Details

### Document References

When the AI references documents in responses, metadata includes:

```json
{
  "document_references": [
    {
      "document_id": "doc-uuid",
      "relevance_score": 0.95,
      "document_name": "contract.pdf",
      "referenced_clauses": ["termination", "payment"],
      "page_numbers": [2, 5],
      "confidence": "high"
    }
  ]
}
```

### Retrieval Context

Information about legal rule retrieval:

```json
{
  "retrieval_context": {
    "retrieved_rules": 7,
    "top_similarity": 0.89,
    "search_query": "employment termination notice period",
    "legal_precedents": 3,
    "jurisdiction": "civil_law",
    "rule_categories": ["employment", "contracts"]
  }
}
```

### Analysis Context

AI processing metadata:

```json
{
  "analysis_context": {
    "analysis_points": 3,
    "risk_level": "medium",
    "confidence_score": 0.88,
    "processing_time": 2.45,
    "llm_model": "gpt-4",
    "tokens_used": 1250,
    "reasoning_steps": 4
  }
}
```

## Error Handling

### Common Error Responses

#### 400 Bad Request
```json
{
  "detail": "Message content cannot be empty"
}
```

#### 401 Unauthorized
```json
{
  "detail": "Authentication required"
}
```

#### 404 Not Found
```json
{
  "detail": "Space not found or access denied"
}
```

#### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "memory_length"],
      "msg": "Memory length must be between 1 and 50 messages",
      "type": "value_error"
    }
  ]
}
```

#### 500 Internal Server Error
```json
{
  "detail": "Internal server error while processing message"
}
```

#### 503 Service Unavailable
```json
{
  "detail": "Analyzer service unavailable"
}
```

## Usage Examples

### Basic Chat Conversation

```python
import requests
import json

# Authentication
headers = {"Authorization": "Bearer <token>"}
space_id = "123e4567-e89b-12d3-a456-426614174000"

# Send a message
message_data = {
    "content": "What are the key risks in this contract?",
    "type": "user"
}

response = requests.post(
    f"http://localhost:8002/api/v1/spaces/{space_id}/messages",
    headers=headers,
    json=message_data
)

ai_response = response.json()
print("AI Response:", ai_response["message"]["content"])

# Get conversation history
history_response = requests.get(
    f"http://localhost:8002/api/v1/spaces/{space_id}/messages?limit=10",
    headers=headers
)

messages = history_response.json()["messages"]
print(f"Found {len(messages)} messages in conversation")
```

### Document-Specific Analysis

```python
# Ask about specific document aspects
questions = [
    "Summarize the main obligations for each party",
    "What are the termination conditions?",
    "Are there any unusual clauses I should be concerned about?",
    "What would you recommend negotiating?"
]

for question in questions:
    message_data = {
        "content": question,
        "type": "user"
    }
    
    response = requests.post(
        f"http://localhost:8002/api/v1/spaces/{space_id}/messages",
        headers=headers,
        json=message_data
    )
    
    ai_message = response.json()["message"]
    print(f"\nQ: {question}")
    print(f"A: {ai_message['content'][:200]}...")
    
    # Check which documents were referenced
    doc_refs = ai_message["metadata"]["document_references"]
    if doc_refs:
        print(f"Referenced documents: {[ref['document_name'] for ref in doc_refs]}")
```

### Session Configuration

```python
# Configure memory length for detailed analysis
memory_config = {"memory_length": 20}

session_response = requests.put(
    f"http://localhost:8002/api/v1/spaces/{space_id}/session/memory",
    headers=headers,
    json=memory_config
)

session_info = session_response.json()
print(f"Updated memory length to {session_info['memory_length']} messages")

# Get current session info
session_info_response = requests.get(
    f"http://localhost:8002/api/v1/spaces/{space_id}/session",
    headers=headers
)

session = session_info_response.json()
print(f"Session ID: {session['session_id']}")
print(f"Created: {session['created_at']}")
print(f"Last updated: {session['updated_at']}")
```

### Advanced Conversation Flow

```python
def chat_with_ai(space_id, user_message, headers):
    """Send message and return AI response with metadata"""
    message_data = {
        "content": user_message,
        "type": "user"
    }
    
    response = requests.post(
        f"http://localhost:8002/api/v1/spaces/{space_id}/messages",
        headers=headers,
        json=message_data
    )
    
    return response.json()["message"]

# Multi-turn conversation
conversation = [
    "What are the main risks in this employment contract?",
    "Can you elaborate on the intellectual property concerns?",
    "What specific language would you recommend for the IP clause?",
    "How does this compare to industry standards?"
]

for turn, message in enumerate(conversation, 1):
    print(f"\n--- Turn {turn} ---")
    print(f"User: {message}")
    
    ai_response = chat_with_ai(space_id, message, headers)
    print(f"AI: {ai_response['content'][:300]}...")
    
    # Show referenced documents and confidence
    metadata = ai_response["metadata"]
    if metadata.get("document_references"):
        docs = [ref["document_name"] for ref in metadata["document_references"]]
        print(f"Documents referenced: {docs}")
    
    if metadata.get("analysis_context", {}).get("confidence_score"):
        confidence = metadata["analysis_context"]["confidence_score"]
        print(f"AI Confidence: {confidence:.2f}")
```

## Integration Patterns

### With Document Upload Workflow

```python
# 1. Upload document via backend
# 2. Wait for analysis completion
# 3. Start chat conversation about the document

def analyze_and_chat_workflow(file_path, space_id):
    # Upload document (via backend API)
    with open(file_path, "rb") as f:
        upload_response = requests.post(
            f"http://localhost:8000/api/spaces/{space_id}/documents",
            headers=headers,
            files={"file": f}
        )
    
    document_id = upload_response.json()["id"]
    print(f"Uploaded document: {document_id}")
    
    # Start chat conversation
    ai_response = chat_with_ai(
        space_id, 
        "I just uploaded a new contract. Can you analyze it for potential risks?",
        headers
    )
    
    return ai_response

# Usage
response = analyze_and_chat_workflow("contract.pdf", space_id)
print("AI Analysis:", response["content"])
```

---

*For authentication details, see the [Authentication Guide](./authentication.md)*  
*For document management, see the [Backend API Documentation](./backend-api.md)* 