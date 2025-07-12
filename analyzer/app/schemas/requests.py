from pydantic import BaseModel, Field, validator
from typing import Optional


class RetrieveRequest(BaseModel):
    """Request schema for /retrieve endpoint"""
    query: str = Field(..., description="Search query for document retrieval", min_length=1)
    k: int = Field(default=5, description="Number of documents to retrieve", ge=1, le=20)
    distance_function: Optional[str] = Field(
        default="l2", 
        description="Distance function to use: 'cosine', 'l2', or 'inner_product'"
    )
    
    @validator('query')
    def validate_query(cls, v):
        if not v.strip():
            raise ValueError('Query cannot be empty or whitespace only')
        return v.strip()
    
    @validator('distance_function')
    def validate_distance_function(cls, v):
        if v is None:
            return "cosine"
        valid_functions = ["cosine", "l2", "inner_product"]
        if v.lower() not in valid_functions:
            raise ValueError(f'Distance function must be one of: {valid_functions}')
        return v.lower()


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