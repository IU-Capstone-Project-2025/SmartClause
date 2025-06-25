from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class TextEmbeddingPair(BaseModel):
    """Response item for /retrieve endpoint"""
    text: str = Field(..., description="Retrieved text chunk")
    embedding: List[float] = Field(..., description="Vector embedding of the text")


class DocumentMetadata(BaseModel):
    """Metadata for legal rule documents"""
    file_name: Optional[str] = Field(None, description="Source file name")
    rule_number: Optional[int] = Field(None, description="Article/rule number")
    rule_title: Optional[str] = Field(None, description="Article title")
    section_title: Optional[str] = Field(None, description="Section title")
    chapter_title: Optional[str] = Field(None, description="Chapter title")
    start_char: Optional[int] = Field(None, description="Start character position")
    end_char: Optional[int] = Field(None, description="End character position")
    text_length: Optional[int] = Field(None, description="Text length in characters")


class RetrieveResult(BaseModel):
    """Enhanced response item for /retrieve endpoint with metadata"""
    text: str = Field(..., description="Retrieved text chunk")
    embedding: List[float] = Field(..., description="Vector embedding of the text")
    metadata: DocumentMetadata = Field(..., description="Document metadata")
    similarity_score: float = Field(..., description="Similarity score (distance-based)")


class RetrieveResponse(BaseModel):
    """Response schema for /retrieve endpoint"""
    results: List[RetrieveResult] = Field(..., description="List of text/embedding pairs with metadata")
    total_results: int = Field(..., description="Total number of results found")
    query: str = Field(..., description="Original query")
    distance_function: str = Field(..., description="Distance function used for similarity")


class AnalysisPoint(BaseModel):
    """Analysis point structure"""
    cause: str = Field(..., description="Identified legal cause or issue")
    risk: str = Field(..., description="Associated legal risk")
    recommendation: str = Field(..., description="Recommended action or solution")


class DocumentPointAnalysis(BaseModel):
    """Analysis result for a single document point/clause"""
    point_number: Optional[str] = Field(None, description="Point number (e.g., '1.', 'Article 5')")
    point_content: str = Field(..., description="Original content of the document point")
    point_type: str = Field(..., description="Type of point (numbered_clause, bullet_point, paragraph)")
    analysis_points: List[AnalysisPoint] = Field(..., description="Analysis results for this point")


class AnalyzeResponse(BaseModel):
    """Response schema for /analyze endpoint"""
    document_points: List[DocumentPointAnalysis] = Field(..., description="Analysis results for each document point")
    document_id: str = Field(..., description="Document identifier")
    document_metadata: Dict[str, Any] = Field(..., description="Document metadata (length, word count, etc.)")
    total_points: int = Field(..., description="Total number of points analyzed")
    analysis_timestamp: str = Field(..., description="Timestamp of analysis")
    
    # For backward compatibility
    points: List[AnalysisPoint] = Field(default_factory=list, description="Deprecated: use document_points instead")


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


class RetrievalMetricsResponse(BaseModel):
    """Response schema for retrieval metrics endpoint"""
    total_variance: float = Field(..., description="Total variance across all embedding dimensions")
    silhouette_score: float = Field(..., description="Silhouette score for document clusters")
    eid: float = Field(..., description="Effective Intrinsic Dimensionality (EID)")
    dr: float = Field(..., description="Dimensionality Redundancy (DR)") 