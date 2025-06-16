from pydantic import BaseModel, Field
from typing import List, Optional


class TextEmbeddingPair(BaseModel):
    """Response item for /retrieve endpoint"""
    text: str = Field(..., description="Retrieved text chunk")
    embedding: List[float] = Field(..., description="Vector embedding of the text")


class RetrieveResponse(BaseModel):
    """Response schema for /retrieve endpoint"""
    results: List[TextEmbeddingPair] = Field(..., description="List of text/embedding pairs")
    total_results: int = Field(..., description="Total number of results found")
    query: str = Field(..., description="Original query")


class AnalysisPoint(BaseModel):
    """Analysis point structure"""
    cause: str = Field(..., description="Identified legal cause or issue")
    risk: str = Field(..., description="Associated legal risk")
    recommendation: str = Field(..., description="Recommended action or solution")


class AnalyzeResponse(BaseModel):
    """Response schema for /analyze endpoint"""
    points: List[AnalysisPoint] = Field(..., description="List of analysis points")
    document_id: str = Field(..., description="Document identifier")
    analysis_timestamp: str = Field(..., description="Timestamp of analysis")


class HealthResponse(BaseModel):
    """Response schema for health check"""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    database_connected: bool = Field(..., description="Database connection status")


class EmbedResponse(BaseModel):
    """Response schema for /embed endpoint"""
    text: str = Field(..., description="Original input text")
    embedding: List[float] = Field(..., description="Vector embedding of the text")
    dimension: int = Field(..., description="Dimension of the embedding vector") 