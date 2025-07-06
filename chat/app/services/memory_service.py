from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func
from sqlalchemy.orm import selectinload
import logging
import uuid
from datetime import datetime

from ..models.database import Message, ChatSession, MessageType
from ..core.config import settings
from ..schemas.responses import ChatMessage, MessageMetadata

logger = logging.getLogger(__name__)


class MemoryService:
    """Service for managing chat memory and conversation context"""
    
    def __init__(self):
        self.default_memory_length = settings.default_memory_messages
        self.max_memory_length = settings.max_memory_messages
    
    async def get_or_create_session(
        self, 
        space_id: uuid.UUID, 
        user_id: str, 
        db: AsyncSession
    ) -> ChatSession:
        """Get existing chat session or create a new one"""
        try:
            # Try to get existing session
            query = select(ChatSession).where(
                and_(
                    ChatSession.space_id == space_id,
                    ChatSession.user_id == user_id,
                    ChatSession.is_active == True
                )
            )
            result = await db.execute(query)
            session = result.scalar_one_or_none()
            
            if session:
                logger.debug(f"Found existing chat session {session.id} for space {space_id}")
                return session
            
            # Create new session
            session = ChatSession(
                space_id=space_id,
                user_id=user_id,
                memory_length=self.default_memory_length
            )
            db.add(session)
            await db.commit()
            await db.refresh(session)
            
            logger.info(f"Created new chat session {session.id} for space {space_id}")
            return session
            
        except Exception as e:
            logger.error(f"Error getting/creating chat session: {e}")
            await db.rollback()
            raise
    
    async def get_conversation_context(
        self,
        space_id: uuid.UUID,
        user_id: str,
        db: AsyncSession,
        limit: Optional[int] = None
    ) -> List[Message]:
        """Get conversation context (recent messages) for the chat"""
        try:
            # Get chat session first
            session = await self.get_or_create_session(space_id, user_id, db)
            
            # Use session memory length if no specific limit provided
            if limit is None:
                limit = session.memory_length
            
            # Get recent messages ordered by sequence number (most recent first)
            query = select(Message).where(
                and_(
                    Message.space_id == space_id,
                    Message.user_id == user_id,
                    Message.is_deleted == False
                )
            ).order_by(desc(Message.sequence_number)).limit(limit)
            
            result = await db.execute(query)
            messages = result.scalars().all()
            
            # Return in chronological order (oldest first for context)
            context = list(reversed(messages))
            
            logger.debug(f"Retrieved {len(context)} messages for context in space {space_id}")
            return context
            
        except Exception as e:
            logger.error(f"Error getting conversation context: {e}")
            raise
    
    async def save_message(
        self,
        space_id: uuid.UUID,
        user_id: str,
        content: str,
        message_type: MessageType,
        metadata: Optional[Dict[str, Any]],
        db: AsyncSession
    ) -> Message:
        """Save a new message to the database"""
        try:
            # Get next sequence number
            query = select(func.coalesce(func.max(Message.sequence_number), 0) + 1).where(
                and_(
                    Message.space_id == space_id,
                    Message.user_id == user_id
                )
            )
            result = await db.execute(query)
            sequence_number = result.scalar()
            
            # Create new message
            message = Message(
                space_id=space_id,
                user_id=user_id,
                content=content,
                type=message_type,
                message_metadata=metadata or {},
                sequence_number=sequence_number
            )
            
            db.add(message)
            await db.commit()
            await db.refresh(message)
            
            logger.debug(f"Saved message {message.id} (type: {message_type.value}) to space {space_id}")
            return message
            
        except Exception as e:
            logger.error(f"Error saving message: {e}")
            await db.rollback()
            raise
    
    async def get_messages_paginated(
        self,
        space_id: uuid.UUID,
        user_id: str,
        db: AsyncSession,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[Message], int, bool]:
        """Get paginated messages for a space"""
        try:
            # Get total count
            count_query = select(func.count(Message.id)).where(
                and_(
                    Message.space_id == space_id,
                    Message.user_id == user_id,
                    Message.is_deleted == False
                )
            )
            count_result = await db.execute(count_query)
            total_count = count_result.scalar()
            
            # Get messages with pagination
            query = select(Message).where(
                and_(
                    Message.space_id == space_id,
                    Message.user_id == user_id,
                    Message.is_deleted == False
                )
            ).order_by(desc(Message.sequence_number)).offset(offset).limit(limit)
            
            result = await db.execute(query)
            messages = result.scalars().all()
            
            # Calculate if there are more messages
            has_more = (offset + len(messages)) < total_count
            
            # Return in chronological order (most recent first for API response)
            logger.debug(f"Retrieved {len(messages)} messages (offset: {offset}, limit: {limit}) for space {space_id}")
            return list(messages), total_count, has_more
            
        except Exception as e:
            logger.error(f"Error getting paginated messages: {e}")
            raise
    
    async def update_session_memory_length(
        self,
        space_id: uuid.UUID,
        user_id: str,
        memory_length: int,
        db: AsyncSession
    ) -> ChatSession:
        """Update the memory length for a chat session"""
        try:
            # Validate memory length
            if memory_length < 1 or memory_length > self.max_memory_length:
                raise ValueError(f"Memory length must be between 1 and {self.max_memory_length}")
            
            # Get session
            session = await self.get_or_create_session(space_id, user_id, db)
            
            # Update memory length
            session.memory_length = memory_length
            session.updated_at = datetime.utcnow()
            
            await db.commit()
            await db.refresh(session)
            
            logger.info(f"Updated memory length to {memory_length} for session {session.id}")
            return session
            
        except Exception as e:
            logger.error(f"Error updating session memory length: {e}")
            await db.rollback()
            raise
    
    def convert_to_chat_message(self, message: Message) -> ChatMessage:
        """Convert database Message to ChatMessage schema"""
        return ChatMessage(
            id=str(message.id),
            content=message.content,
            type=message.type.value,
            timestamp=message.timestamp,
            metadata=MessageMetadata(
                document_references=message.message_metadata.get('document_references', []),
                retrieval_context=message.message_metadata.get('retrieval_context'),
                analysis_context=message.message_metadata.get('analysis_context')
            )
        )


# Global memory service instance
memory_service = MemoryService() 