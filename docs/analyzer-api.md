# Analyzer Service API

The Analyzer Service handles document analysis, legal rule retrieval, text embedding generation, and PDF export functionality. Built with Python FastAPI, it provides AI-powered legal document analysis using RAG (Retrieval-Augmented Generation) techniques.

**Base URL**: `http://localhost:8001`

## Table of Contents

- [Authentication](#authentication)
- [Document Analysis](#document-analysis)
- [Legal Rule Retrieval](#legal-rule-retrieval)
- [Text Embedding](#text-embedding)
- [PDF Export](#pdf-export)
- [Metrics & Monitoring](#metrics--monitoring)
- [Health Check](#health-check)

## Authentication

All endpoints require authentication via Bearer token or login cookie. The analyzer service validates tokens with the backend service.

**Authentication Methods:**
- `Authorization: Bearer <token>` header
- `smartclause_token` HTTP-only cookie

## Document Analysis

### POST /analyze

Analyze a document for legal risks and recommendations using AI-powered RAG.

**Authentication:** Required

**Content-Type:** `multipart/form-data`

**Request Parameters:**
- `id` (form field): Document identifier
- `file` (file upload): Document file (PDF, DOCX, TXT)

**Request Example:**
```bash
curl -X POST "http://localhost:8001/analyze" \
  -H "Authorization: Bearer <token>" \
  -F "id=contract-123" \
  -F "file=@contract.pdf"
```

**Response (200):**
```json
{
  "document_points": [
    {
      "point_number": "1",
      "point_content": "The Contractor agrees to provide services for a period of 12 months starting from the effective date.",
      "point_type": "numbered_clause",
      "analysis_points": [
        {
          "cause": "Fixed term contract without renewal clause",
          "risk": "Contract termination uncertainty and potential service disruption",
          "recommendation": "Add automatic renewal clause or clear termination procedures"
        }
      ]
    },
    {
      "point_number": "2",
      "point_content": "Payment shall be made within 45 days of invoice receipt.",
      "point_type": "numbered_clause",
      "analysis_points": [
        {
          "cause": "Extended payment terms beyond industry standard",
          "risk": "Cash flow issues and potential late payment disputes",
          "recommendation": "Negotiate shorter payment terms (15-30 days) or add late payment penalties"
        }
      ]
    }
  ],
  "document_id": "contract-123",
  "document_metadata": {
    "word_count": 1250,
    "page_count": 3,
    "title": "Service Agreement",
    "length": 8450
  },
  "total_points": 8,
  "analysis_timestamp": "2025-01-01T10:00:00.000Z"
}
```

**Error Responses:**
- `400`: Invalid request parameters or file format
- `401`: Authentication required
- `413`: File size exceeds maximum limit
- `500`: Analysis processing error

## Legal Rule Retrieval

### POST /retrieve-chunk

Retrieve relevant legal text chunks using hybrid BM25+vector+RRF search.

**Authentication:** Required

**Request Body:**
```json
{
  "query": "employment contract termination procedures",
  "k": 5,
  "distance_function": "cosine"
}
```

**Parameters:**
- `query` (string): Search query for legal rule retrieval
- `k` (integer): Number of chunks to retrieve (1-20, default: 5)
- `distance_function` (string): Distance function ("cosine", "l2", "inner_product", default: "cosine")

**Response (200):**
```json
{
  "results": [
    {
      "text": "Article 123. Employment contracts may be terminated by either party with 30 days written notice...",
      "embedding": [0.123, -0.456, 0.789, ...], // 768-dimensional vector
      "metadata": {
        "file_name": "civil_code.pdf",
        "rule_number": 123,
        "rule_title": "Employment Contract Termination",
        "section_title": "Labor Relations",
        "chapter_title": "Employment Law",
        "start_char": 1250,
        "end_char": 1580,
        "text_length": 330
      },
      "similarity_score": 0.8945
    }
  ],
  "total_results": 5,
  "query": "employment contract termination procedures",
  "distance_function": "cosine"
}
```

### POST /retrieve-rules

Retrieve unique legal rules (full articles) using hybrid search with deduplication.

**Authentication:** Required

**Request Body:**
```json
{
  "query": "intellectual property ownership in contracts",
  "k": 3,
  "distance_function": "cosine"
}
```

**Response (200):**
```json
{
  "results": [
    {
      "text": "Article 456. Intellectual property rights created during the course of employment shall belong to the employer unless otherwise specified in the contract...",
      "embedding": [0.234, -0.567, 0.891, ...],
      "metadata": {
        "file_name": "intellectual_property_law.pdf",
        "rule_number": 456,
        "rule_title": "IP Rights in Employment",
        "section_title": "Intellectual Property",
        "chapter_title": "Property Rights",
        "start_char": 2100,
        "end_char": 2650,
        "text_length": 550
      },
      "similarity_score": 0.9123
    }
  ],
  "total_results": 3,
  "query": "intellectual property ownership in contracts",
  "distance_function": "cosine"
}
```

## Text Embedding

### POST /embed

Generate vector embeddings for input text using sentence transformer models.

**Authentication:** Required

**Request Body:**
```json
{
  "text": "This contract establishes the terms and conditions for the provision of legal services."
}
```

**Response (200):**
```json
{
  "text": "This contract establishes the terms and conditions for the provision of legal services.",
  "embedding": [0.123, -0.456, 0.789, 0.234, ...], // 768-dimensional vector
  "dimension": 768
}
```

**Error Responses:**
- `400`: Invalid or empty text input
- `401`: Authentication required
- `500`: Embedding generation error

## PDF Export

### GET /export/{document_id}/pdf

Export analysis results as a formatted PDF report.

**Authentication:** Required

**Path Parameters:**
- `document_id` (string): Document identifier

**Request Example:**
```bash
curl -X GET "http://localhost:8001/export/contract-123/pdf" \
  -H "Authorization: Bearer <token>" \
  -o analysis_report.pdf
```

**Response (200):**
- **Content-Type:** `application/pdf`
- **Content-Disposition:** `attachment; filename=analysis_contract-123.pdf`
- Binary PDF content containing formatted analysis report

**PDF Report Contents:**
- Document metadata and summary
- Point-by-point analysis results
- Risk assessment matrix
- Recommendations summary
- Legal context references

**Error Responses:**
- `401`: Authentication required
- `404`: Document or analysis not found
- `500`: PDF generation error

## Metrics & Monitoring

### GET /metrics/retrieval

Compute intrinsic retrieval metrics for embeddings quality assessment.

**Authentication:** Required

**Response (200):**
```json
{
  "total_variance": 245.67,
  "silhouette_score": 0.732,
  "eid": 312.45,
  "dr": 0.593
}
```

**Metrics Explanation:**
- `total_variance`: Total variance across all embedding dimensions
- `silhouette_score`: Silhouette score for document clusters (higher = better)
- `eid`: Effective Intrinsic Dimensionality
- `dr`: Dimensionality Redundancy (0-1, lower = less redundant)

## Health Check

### GET /health

Check analyzer service health and database connectivity.

**Authentication:** Not required

**Response (200):**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database_connected": true
}
```

**Status Values:**
- `healthy`: Service operational, database connected
- `unhealthy`: Service or database issues
- `degraded`: Partial functionality available

## Request/Response Schema Details

### Distance Functions

Available distance functions for similarity search:

| Function | Description | Use Case |
|----------|-------------|----------|
| `cosine` | Cosine similarity (default) | General semantic similarity |
| `l2` | Euclidean distance | Geometric similarity |
| `inner_product` | Dot product | High-dimensional spaces |

### Document Point Types

Analysis categorizes document content into these types:

| Type | Description |
|------|-------------|
| `numbered_clause` | Numbered sections (1., 2., Article 5) |
| `bullet_point` | Bulleted items |
| `paragraph` | General paragraphs |

### File Format Support

Supported document formats:
- **PDF** (.pdf) - Recommended for best OCR results
- **Word Documents** (.docx, .doc)
- **Plain Text** (.txt)
- **Rich Text** (.rtf)

**File Size Limits:**
- Maximum file size: 50MB
- Maximum processing time: 5 minutes per document

### Rate Limiting

The analyzer service implements rate limiting:

**Authenticated Users:**
- 100 requests per minute
- 1000 requests per hour
- 5000 requests per day

**System/Service Tokens:**
- Higher limits for inter-service communication

## Error Handling

### Common Error Responses

#### 400 Bad Request
```json
{
  "detail": "Invalid distance function: must be one of ['cosine', 'l2', 'inner_product']"
}
```

#### 401 Unauthorized
```json
{
  "detail": "Authentication required"
}
```

#### 413 Request Entity Too Large
```json
{
  "detail": "File size exceeds maximum allowed size of 52428800 bytes"
}
```

#### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "k"],
      "msg": "ensure this value is less than or equal to 20",
      "type": "value_error.number.not_le",
      "ctx": {"limit_value": 20}
    }
  ]
}
```

#### 500 Internal Server Error
```json
{
  "detail": "Internal server error during document analysis"
}
```

## Usage Examples

### Complete Document Analysis Workflow

```python
import requests
import json

# 1. Authenticate (get token from backend)
auth_response = requests.post("http://localhost:8000/api/auth/login", json={
    "username_or_email": "user@example.com",
    "password": "password"
})
token = auth_response.json()["access_token"]

headers = {"Authorization": f"Bearer {token}"}

# 2. Analyze document
with open("contract.pdf", "rb") as f:
    files = {"file": f}
    data = {"id": "contract-analysis-001"}
    
    analysis_response = requests.post(
        "http://localhost:8001/analyze",
        headers=headers,
        files=files,
        data=data
    )

analysis_result = analysis_response.json()
print(f"Found {analysis_result['total_points']} analysis points")

# 3. Export PDF report
pdf_response = requests.get(
    f"http://localhost:8001/export/contract-analysis-001/pdf",
    headers=headers
)

with open("analysis_report.pdf", "wb") as f:
    f.write(pdf_response.content)
```

### Legal Rule Search

```python
# Search for relevant legal rules
search_request = {
    "query": "force majeure clauses in commercial contracts",
    "k": 10,
    "distance_function": "cosine"
}

rules_response = requests.post(
    "http://localhost:8001/retrieve-rules",
    headers=headers,
    json=search_request
)

rules = rules_response.json()
for rule in rules["results"]:
    print(f"Rule {rule['metadata']['rule_number']}: {rule['metadata']['rule_title']}")
    print(f"Similarity: {rule['similarity_score']:.3f}")
    print(f"Text: {rule['text'][:200]}...")
    print()
```

### Text Embedding Generation

```python
# Generate embeddings for custom text
embed_request = {
    "text": "The parties agree to resolve disputes through binding arbitration."
}

embed_response = requests.post(
    "http://localhost:8001/embed",
    headers=headers,
    json=embed_request
)

embedding = embed_response.json()
print(f"Generated {embedding['dimension']}-dimensional embedding")
print(f"First 5 values: {embedding['embedding'][:5]}")
```

---

*For authentication details, see the [Authentication Guide](./authentication.md)* 