from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import logging
import uuid

from ..core.database import get_db
from ..core.config import settings
from ..schemas.requests import SendMessageRequest, ChatMemoryConfigRequest
from ..schemas.responses import (
    GetMessagesResponse, SendMessageResponse, HealthResponse, 
    ChatSessionResponse, ChatMessage
)
from ..services.memory_service import memory_service
from ..services.llm_service import llm_service
from ..services.retrieval_service import retrieval_service
from ..models.database import MessageType

logger = logging.getLogger(__name__)

router = APIRouter()


def extract_user_id_from_header(authorization: Optional[str] = Header(None)) -> str:
    """
    Extract user ID from Authorization header.
    For now, this is a placeholder implementation that returns a default user.
    In the future, this will parse JWT token and extract user ID.
    """
    try:
        if authorization is None or authorization.strip() == "":
            logger.debug("No authorization header provided")
            return "default-user-123"  # Default user for development
        
        if authorization.startswith("Bearer "):
            token = authorization[7:]
            logger.debug(f"Received Bearer token: {token[:10]}...")
            # TODO: Parse JWT token and extract user ID
            # For now, return default user
            return "default-user-123"
        
        logger.debug("Authorization header format not recognized")
        return "default-user-123"
        
    except Exception as e:
        logger.error(f"Failed to extract user ID from authorization header: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header"
        )


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        # Check analyzer service health
        analyzer_healthy = await retrieval_service.check_analyzer_health()
        
        overall_status = "healthy" if analyzer_healthy else "degraded"
        
        return HealthResponse(
            status=overall_status,
            version=settings.api_version,
            database_connected=True,  # We assume DB is connected if we get this far
            analyzer_connected=analyzer_healthy
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            version=settings.api_version,
            database_connected=False,
            analyzer_connected=False
        )


@router.get("/spaces/{space_id}/messages", response_model=GetMessagesResponse)
async def get_messages(
    space_id: str,
    limit: int = 50,
    offset: int = 0,
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """Get chat messages for a space"""
    try:
        # Validate space ID format
        try:
            space_uuid = uuid.UUID(space_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid space ID format"
            )
        
        # Extract user ID
        user_id = extract_user_id_from_header(authorization)
        
        # Validate pagination parameters
        if limit < 1 or limit > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Limit must be between 1 and 100"
            )
        
        if offset < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Offset must be non-negative"
            )
        
        # Get paginated messages
        messages, total_count, has_more = await memory_service.get_messages_paginated(
            space_id=space_uuid,
            user_id=user_id,
            db=db,
            limit=limit,
            offset=offset
        )
        
        # Convert to response format
        chat_messages = [
            memory_service.convert_to_chat_message(message)
            for message in messages
        ]
        
        logger.info(f"Retrieved {len(chat_messages)} messages for space {space_id}, user {user_id}")
        
        return GetMessagesResponse(
            messages=chat_messages,
            total_count=total_count,
            has_more=has_more
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting messages for space {space_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while retrieving messages"
        )


@router.post("/spaces/{space_id}/messages", response_model=SendMessageResponse)
async def send_message(
    space_id: str,
    request: SendMessageRequest,
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """Send a message to space chat"""
    try:
        # Validate space ID format
        try:
            space_uuid = uuid.UUID(space_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid space ID format"
            )
        
        # Extract user ID
        user_id = extract_user_id_from_header(authorization)
        
        logger.info(f"Processing message from user {user_id} in space {space_id}")
        
        # Save user message
        user_message = await memory_service.save_message(
            space_id=space_uuid,
            user_id=user_id,
            content=request.content,
            message_type=MessageType.USER,
            metadata={},
            db=db
        )
        
        # Get conversation context for generating response
        conversation_history = await memory_service.get_conversation_context(
            space_id=space_uuid,
            user_id=user_id,
            db=db
        )
        
        # Generate assistant response
        response_text, response_metadata = await llm_service.generate_response(
            user_message=request.content,
            conversation_history=conversation_history,
            space_id=space_id,
            user_id=user_id
        )
        
        # Save assistant message
        assistant_message = await memory_service.save_message(
            space_id=space_uuid,
            user_id=user_id,
            content=response_text,
            message_type=MessageType.ASSISTANT,
            metadata=response_metadata,
            db=db
        )
        
        # Convert to response format
        chat_message = memory_service.convert_to_chat_message(assistant_message)
        
        logger.info(f"Generated and saved assistant response for space {space_id}")
        
        return SendMessageResponse(message=chat_message)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending message to space {space_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while processing message"
        )


@router.get("/spaces/{space_id}/session", response_model=ChatSessionResponse)
async def get_chat_session(
    space_id: str,
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """Get chat session information for a space"""
    try:
        # Validate space ID format
        try:
            space_uuid = uuid.UUID(space_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid space ID format"
            )
        
        # Extract user ID
        user_id = extract_user_id_from_header(authorization)
        
        # Get or create session
        session = await memory_service.get_or_create_session(
            space_id=space_uuid,
            user_id=user_id,
            db=db
        )
        
        return ChatSessionResponse(
            session_id=str(session.id),
            space_id=str(session.space_id),
            memory_length=session.memory_length,
            created_at=session.created_at,
            updated_at=session.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chat session for space {space_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while retrieving chat session"
        )


@router.put("/spaces/{space_id}/session/memory", response_model=ChatSessionResponse)
async def update_memory_length(
    space_id: str,
    request: ChatMemoryConfigRequest,
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """Update memory length for chat session"""
    try:
        # Validate space ID format
        try:
            space_uuid = uuid.UUID(space_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid space ID format"
            )
        
        # Extract user ID
        user_id = extract_user_id_from_header(authorization)
        
        # Update session memory length
        session = await memory_service.update_session_memory_length(
            space_id=space_uuid,
            user_id=user_id,
            memory_length=request.memory_length,
            db=db
        )
        
        return ChatSessionResponse(
            session_id=str(session.id),
            space_id=str(session.space_id),
            memory_length=session.memory_length,
            created_at=session.created_at,
            updated_at=session.updated_at
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating memory length for space {space_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while updating memory length"
        ) 