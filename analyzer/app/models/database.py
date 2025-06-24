from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import UserDefinedType
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..core.database import Base


class Vector(UserDefinedType):
    """Custom type for pgvector"""
    def __init__(self, dimension):
        self.dimension = dimension
    
    def get_col_spec(self):
        return f"vector({self.dimension})"


class Rule(Base):
    """Model for storing legal rules (articles) from Russian legal codes"""
    __tablename__ = "rules"
    
    rule_id = Column(Integer, primary_key=True, index=True)
    file = Column(String(255), index=True)
    rule_number = Column(Integer, index=True)
    rule_title = Column(Text)
    rule_text = Column(Text)
    section_title = Column(Text)
    chapter_title = Column(Text)
    start_char = Column(Integer)
    end_char = Column(Integer)
    text_length = Column(Integer)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    # Relationship to chunks
    chunks = relationship("RuleChunk", back_populates="rule", cascade="all, delete-orphan")


class RuleChunk(Base):
    """Model for storing rule chunks with embeddings"""
    __tablename__ = "rule_chunks"
    
    chunk_id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(Integer, ForeignKey("rules.rule_id"), index=True)
    chunk_number = Column(Integer)
    chunk_text = Column(Text)
    chunk_char_start = Column(Integer)
    chunk_char_end = Column(Integer)
    embedding = Column(Vector(1024))  # 1024-dimensional vector for BGE-M3
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    # Relationship to parent rule
    rule = relationship("Rule", back_populates="chunks")


class AnalysisResult(Base):
    """Model for storing analysis results"""
    __tablename__ = "analysis_results"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(String(255), index=True)
    analysis_points = Column(JSONB)
    created_at = Column(TIMESTAMP, server_default=func.now()) 