from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid


class MessageMetadata(BaseModel):
    """Metadata for chat messages"""
    document_references: List[Dict[str, Any]] = Field(default_factory=list, description="References to analyzed documents")
    retrieval_context: Optional[Dict[str, Any]] = Field(default=None, description="Context from legal database retrieval")
    analysis_context: Optional[Dict[str, Any]] = Field(default=None, description="Context from document analysis")


class ChatMessage(BaseModel):
    """Chat message response schema"""
    id: str = Field(..., description="Message ID")
    content: str = Field(..., description="Message content")
    type: str = Field(..., description="Message type: 'user' or 'assistant'")
    timestamp: datetime = Field(..., description="Message timestamp")
    metadata: MessageMetadata = Field(default_factory=MessageMetadata, description="Message metadata")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class GetMessagesResponse(BaseModel):
    """Response schema for getting chat messages"""
    messages: List[ChatMessage] = Field(..., description="List of chat messages")
    total_count: int = Field(..., description="Total number of messages in the chat")
    has_more: bool = Field(..., description="Whether there are more messages available")


class SendMessageResponse(BaseModel):
    """Response schema for sending a message"""
    message: ChatMessage = Field(..., description="The created message")


class HealthResponse(BaseModel):
    """Health check response schema"""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    database_connected: bool = Field(..., description="Database connection status")
    analyzer_connected: bool = Field(..., description="Analyzer service connection status")
    backend_connected: bool = Field(..., description="Backend service connection status")


class ChatSessionResponse(BaseModel):
    """Response schema for chat session information"""
    session_id: str = Field(..., description="Chat session ID")
    space_id: str = Field(..., description="Space ID")
    memory_length: int = Field(..., description="Number of messages kept in context")
    created_at: datetime = Field(..., description="Session creation timestamp")
    updated_at: datetime = Field(..., description="Session last update timestamp")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        } 