import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, JSON
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql.type_api import TypeEngine
import io
import sys
import os 
from unittest.mock import patch, MagicMock

api_key = os.getenv('OPENROUTER_API_KEY')
if not api_key:
    os.environ['OPENROUTER_API_KEY'] = 'test-dummy-key-for-testing'
    print("Using dummy API key for testing")
else:
    print("Using API key from environment")

def patch_jsonb_for_sqlite():
    """Simple patch to replace JSONB with JSON for SQLite"""
    from sqlalchemy.dialects.sqlite.base import SQLiteTypeCompiler
    
    # Add visit_JSONB method to SQLite type compiler
    def visit_JSONB(self, type_, **kw):
        return self.visit_JSON(type_, **kw)
    
    # Monkey patch the method
    SQLiteTypeCompiler.visit_JSONB = visit_JSONB

patch_jsonb_for_sqlite()

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.main import app
from app.core.database import get_db, Base
from app.core.config import settings

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

def setup_successful_auth_mocks(mock_httpx_get, mock_httpx_post, mock_requests_get, mock_requests_post):
    """Настройка успешной авторизации для всех HTTP-клиентов"""
    mock_auth_response = MagicMock()
    mock_auth_response.status_code = 200
    mock_auth_response.json.return_value = {
        "user_id": "test-user-123",
        "username": "test-user",
        "valid": True
    }
    
    mock_requests_post.return_value = mock_auth_response
    mock_requests_get.return_value = mock_auth_response
    mock_httpx_post.return_value = mock_auth_response
    mock_httpx_get.return_value = mock_auth_response

client = TestClient(app)

# Test headers with authentication
TEST_HEADERS = {
    "Authorization": "Bearer test-token",
    "X-User-ID": "test-user-123",
    "X-API-Key": "test-api-key"
}


def test_root_endpoint():
    """Test the root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "SmartClause Analyzer API"
    assert data["version"] == settings.api_version
    assert data["status"] == "running"


def test_health_endpoint():
    """Test the health check endpoint"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "version" in data
    assert "database_connected" in data


@patch('requests.post')
@patch('requests.get')
@patch('httpx.post')
@patch('httpx.get')
def test_retrieve_endpoint(mock_httpx_get, mock_httpx_post, mock_requests_get, mock_requests_post):
    """Test the retrieve-chunk endpoint with mock data"""
    
    setup_successful_auth_mocks(mock_httpx_get, mock_httpx_post, mock_requests_get, mock_requests_post)
    
    request_data = {
        "query": "contract termination",
        "k": 3
    }
    
    response = client.post("/api/v1/retrieve-chunk", json=request_data, headers=TEST_HEADERS)
    assert response.status_code == 200
    
    data = response.json()
    assert "results" in data
    assert "total_results" in data
    assert "query" in data
    assert data["query"] == request_data["query"]
    assert len(data["results"]) <= request_data["k"]
    
    # Check structure of results
    if data["results"]:
        result = data["results"][0]
        assert "text" in result
        assert "embedding" in result
        assert isinstance(result["embedding"], list)


@patch('requests.post')
@patch('requests.get')
@patch('httpx.post')
@patch('httpx.get')
def test_retrieve_endpoint_validation(mock_httpx_get, mock_httpx_post, mock_requests_get, mock_requests_post):
    """Test retrieve-chunk endpoint input validation"""
    
    setup_successful_auth_mocks(mock_httpx_get, mock_httpx_post, mock_requests_get, mock_requests_post)
    
    # Test empty query
    response = client.post("/api/v1/retrieve-chunk", json={"query": "", "k": 5}, headers=TEST_HEADERS)
    assert response.status_code == 422
    
    # Test k too large
    response = client.post("/api/v1/retrieve-chunk", json={"query": "test", "k": 50}, headers=TEST_HEADERS)
    assert response.status_code == 422


@patch('requests.post')
@patch('requests.get')
@patch('httpx.post')
@patch('httpx.get')
def test_retrieve_rules_endpoint(mock_httpx_get, mock_httpx_post, mock_requests_get, mock_requests_post):
    """Test the retrieve-rules endpoint with mock data"""
    
    setup_successful_auth_mocks(mock_httpx_get, mock_httpx_post, mock_requests_get, mock_requests_post)
    
    request_data = {
        "query": "contract termination",
        "k": 3
    }
    
    response = client.post("/api/v1/retrieve-rules", json=request_data, headers=TEST_HEADERS)
    assert response.status_code == 200
    
    data = response.json()
    assert "results" in data
    assert "total_results" in data
    assert "query" in data
    assert data["query"] == request_data["query"]
    assert len(data["results"]) <= request_data["k"]
    
    # Check structure of results
    if data["results"]:
        result = data["results"][0]
        assert "text" in result
        assert "embedding" in result
        assert "metadata" in result
        assert isinstance(result["embedding"], list)
        
        # Check metadata structure
        metadata = result["metadata"]
        assert "rule_title" in metadata
        assert "rule_number" in metadata
        assert "file_name" in metadata


@patch('requests.post')
@patch('requests.get')
@patch('httpx.post')
@patch('httpx.get')
def test_analyze_endpoint(mock_httpx_get, mock_httpx_post, mock_requests_get, mock_requests_post):
    """Test the analyze endpoint with mock document"""
    
    setup_successful_auth_mocks(mock_httpx_get, mock_httpx_post, mock_requests_get, mock_requests_post)
    
    # Create a test document
    test_content = "This is a test contract with termination clauses."
    test_file = io.BytesIO(test_content.encode('utf-8'))
    
    files = {"file": ("test.txt", test_file, "text/plain")}
    data = {"id": "test_doc_123"}
    
    response = client.post("/api/v1/analyze", files=files, data=data, headers=TEST_HEADERS)
    assert response.status_code == 200
    
    result = response.json()
    assert "points" in result
    assert "document_id" in result
    assert "analysis_timestamp" in result
    assert result["document_id"] == "test_doc_123"
    
    # Check structure of analysis points
    if result["points"]:
        point = result["points"][0]
        assert "cause" in point
        assert "risk" in point
        assert "recommendation" in point


@patch('requests.post')
@patch('requests.get')
@patch('httpx.post')
@patch('httpx.get')
def test_analyze_endpoint_validation(mock_httpx_get, mock_httpx_post, mock_requests_get, mock_requests_post):
    """Test analyze endpoint input validation"""
    
    setup_successful_auth_mocks(mock_httpx_get, mock_httpx_post, mock_requests_get, mock_requests_post)
    
    # Test missing ID
    test_file = io.BytesIO(b"test content")
    files = {"file": ("test.txt", test_file, "text/plain")}
    
    response = client.post("/api/v1/analyze", files=files, data={}, headers=TEST_HEADERS)
    assert response.status_code == 422
    
    # Test missing file
    data = {"id": "test_doc"}
    response = client.post("/api/v1/analyze", data=data, headers=TEST_HEADERS)
    assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__])