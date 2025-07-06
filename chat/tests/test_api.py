import pytest
import uuid
from httpx import AsyncClient
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint():
    """Test the health check endpoint"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    
    data = response.json()
    assert "status" in data
    assert "version" in data
    assert "database_connected" in data
    assert "analyzer_connected" in data


def test_get_messages_invalid_space_id():
    """Test getting messages with invalid space ID"""
    response = client.get("/api/v1/spaces/invalid-uuid/messages")
    assert response.status_code == 400
    assert "Invalid space ID format" in response.json()["detail"]


def test_get_messages_valid_space_id():
    """Test getting messages with valid space ID"""
    space_id = str(uuid.uuid4())
    response = client.get(f"/api/v1/spaces/{space_id}/messages")
    assert response.status_code == 200
    
    data = response.json()
    assert "messages" in data
    assert "total_count" in data
    assert "has_more" in data
    assert isinstance(data["messages"], list)


def test_send_message_invalid_space_id():
    """Test sending message with invalid space ID"""
    message_data = {
        "content": "Test message",
        "type": "user"
    }
    
    response = client.post("/api/v1/spaces/invalid-uuid/messages", json=message_data)
    assert response.status_code == 400
    assert "Invalid space ID format" in response.json()["detail"]


def test_send_message_empty_content():
    """Test sending message with empty content"""
    space_id = str(uuid.uuid4())
    message_data = {
        "content": "",
        "type": "user"
    }
    
    response = client.post(f"/api/v1/spaces/{space_id}/messages", json=message_data)
    assert response.status_code == 422  # Validation error


def test_send_message_invalid_type():
    """Test sending message with invalid type"""
    space_id = str(uuid.uuid4())
    message_data = {
        "content": "Test message",
        "type": "invalid"
    }
    
    response = client.post(f"/api/v1/spaces/{space_id}/messages", json=message_data)
    assert response.status_code == 422  # Validation error


def test_get_chat_session():
    """Test getting chat session information"""
    space_id = str(uuid.uuid4())
    response = client.get(f"/api/v1/spaces/{space_id}/session")
    assert response.status_code == 200
    
    data = response.json()
    assert "session_id" in data
    assert "space_id" in data
    assert "memory_length" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_update_memory_length():
    """Test updating memory length"""
    space_id = str(uuid.uuid4())
    memory_data = {
        "memory_length": 15
    }
    
    response = client.put(f"/api/v1/spaces/{space_id}/session/memory", json=memory_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["memory_length"] == 15


def test_update_memory_length_invalid():
    """Test updating memory length with invalid value"""
    space_id = str(uuid.uuid4())
    memory_data = {
        "memory_length": 100  # Too high
    }
    
    response = client.put(f"/api/v1/spaces/{space_id}/session/memory", json=memory_data)
    assert response.status_code == 422  # Validation error


def test_pagination_parameters():
    """Test pagination parameters validation"""
    space_id = str(uuid.uuid4())
    
    # Test negative offset
    response = client.get(f"/api/v1/spaces/{space_id}/messages?offset=-1")
    assert response.status_code == 400
    
    # Test limit too high
    response = client.get(f"/api/v1/spaces/{space_id}/messages?limit=200")
    assert response.status_code == 400
    
    # Test valid pagination
    response = client.get(f"/api/v1/spaces/{space_id}/messages?limit=10&offset=0")
    assert response.status_code == 200


# Note: These tests assume a test database is available
# In a real environment, you would need to:
# 1. Set up a test database
# 2. Use test fixtures
# 3. Mock external services (analyzer, OpenRouter)
# 4. Add authentication tests 