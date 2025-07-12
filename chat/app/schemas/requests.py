from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
from datetime import datetime


class SendMessageRequest(BaseModel):
    """Request schema for sending a message to chat"""
    content: str = Field(..., description="Message content", min_length=1, max_length=10000)
    type: str = Field("user", description="Message type (always 'user' for requests)")
    
    @validator('content')
    def validate_content(cls, v):
        if not v.strip():
            raise ValueError('Message content cannot be empty or whitespace only')
        return v.strip()
    
    @validator('type')
    def validate_type(cls, v):
        if v != "user":
            raise ValueError('Message type must be "user" for incoming requests')
        return v


class ChatMemoryConfigRequest(BaseModel):
    """Request schema for updating chat memory configuration"""
    memory_length: int = Field(..., description="Number of messages to keep in context", ge=1, le=50)
    
    @validator('memory_length')
    def validate_memory_length(cls, v):
        if v < 1 or v > 50:
            raise ValueError('Memory length must be between 1 and 50 messages')
        return v 