from pydantic import BaseModel, Field, validator
from typing import Optional


class RetrieveRequest(BaseModel):
    """Request schema for /retrieve endpoint"""
    query: str = Field(..., description="Search query for document retrieval", min_length=1)
    k: int = Field(default=5, description="Number of documents to retrieve", ge=1, le=20)
    
    @validator('query')
    def validate_query(cls, v):
        if not v.strip():
            raise ValueError('Query cannot be empty or whitespace only')
        return v.strip()


class AnalyzeRequest(BaseModel):
    """Request schema for /analyze endpoint"""
    id: str = Field(..., description="Unique identifier for the document", min_length=1)
    content: bytes = Field(..., description="Document content as bytes")
    
    @validator('id')
    def validate_id(cls, v):
        if not v.strip():
            raise ValueError('ID cannot be empty or whitespace only')
        return v.strip()
    
    class Config:
        # Allow bytes field to be serialized
        arbitrary_types_allowed = True


class EmbedRequest(BaseModel):
    """Request schema for /embed endpoint"""
    text: str = Field(..., description="Text to generate embeddings for", min_length=1)
    
    @validator('text')
    def validate_text(cls, v):
        if not v.strip():
            raise ValueError('Text cannot be empty or whitespace only')
        return v.strip() 