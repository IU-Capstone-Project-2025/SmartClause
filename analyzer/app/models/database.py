from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import UserDefinedType
from sqlalchemy.sql import func
from ..core.database import Base


class Vector(UserDefinedType):
    """Custom type for pgvector"""
    def __init__(self, dimension):
        self.dimension = dimension
    
    def get_col_spec(self):
        return f"vector({self.dimension})"


class LegalRule(Base):
    """Model for storing legal rules (articles) from Civil Code"""
    __tablename__ = "legal_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String(255))
    rule_number = Column(Integer, index=True)
    rule_title = Column(Text)
    rule_text = Column(Text)
    section_title = Column(Text)
    chapter_title = Column(Text)
    start_char = Column(Integer)
    end_char = Column(Integer)
    text_length = Column(Integer)
    embedding = Column(Vector(1024))  # 1024-dimensional vector for BGE-M3
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())


class DocumentEmbedding(Base):
    """Model for storing document embeddings for RAG retrieval"""
    __tablename__ = "document_embeddings"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(String(255), unique=True, index=True)
    text_chunk = Column(Text)
    embedding = Column(Vector(1024))  # 1024-dimensional vector for BGE-M3
    document_metadata = Column(JSONB)
    created_at = Column(TIMESTAMP, server_default=func.now())


class AnalysisResult(Base):
    """Model for storing analysis results"""
    __tablename__ = "analysis_results"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(String(255), index=True)
    analysis_points = Column(JSONB)
    created_at = Column(TIMESTAMP, server_default=func.now()) 