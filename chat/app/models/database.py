from sqlalchemy import Column, String, Text, DateTime, Enum, Integer, JSON, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from ..core.database import Base


class MessageType(enum.Enum):
    """Enum for message types"""
    USER = "user"
    ASSISTANT = "assistant"


class Message(Base):
    """Chat message model"""
    __tablename__ = "chat_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    space_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    content = Column(Text, nullable=False)
    type = Column(Enum(MessageType), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Metadata for document references and other context
    message_metadata = Column(JSON, default=dict)
    
    # For message ordering and pagination
    sequence_number = Column(Integer, nullable=False)
    
    # Soft delete
    is_deleted = Column(Boolean, default=False)

    def __repr__(self):
        return f"<Message(id={self.id}, space_id={self.space_id}, type={self.type}, timestamp={self.timestamp})>"


class ChatSession(Base):
    """Chat session model to track conversation context"""
    __tablename__ = "chat_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    space_id = Column(UUID(as_uuid=True), nullable=False, unique=True, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    
    # Configuration for this chat session
    memory_length = Column(Integer, default=10)  # Number of messages to keep in context
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Soft delete
    is_active = Column(Boolean, default=True)

    def __repr__(self):
        return f"<ChatSession(id={self.id}, space_id={self.space_id}, memory_length={self.memory_length})>" 