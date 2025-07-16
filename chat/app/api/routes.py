from fastapi import APIRouter, Depends, HTTPException, status, Header, Request
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
from ..services.document_service import document_service
from ..models.database import MessageType
from ..utils.auth_utils import auth_utils

logger = logging.getLogger(__name__)

router = APIRouter()





@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        # Check analyzer service health
        analyzer_healthy = await retrieval_service.check_analyzer_health()
        
        # Check backend service health
        backend_healthy = await document_service.check_backend_health()
        
        overall_status = "healthy" if (analyzer_healthy and backend_healthy) else "degraded"
        
        return HealthResponse(
            status=overall_status,
            version=settings.api_version,
            database_connected=True,  # We assume DB is connected if we get this far
            analyzer_connected=analyzer_healthy,
            backend_connected=backend_healthy
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            version=settings.api_version,
            database_connected=False,
            analyzer_connected=False,
            backend_connected=False
        )


@router.get("/spaces/{space_id}/messages", response_model=GetMessagesResponse)
async def get_messages(
    space_id: str,
    request: Request,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    authorization: Optional[str] = Header(None, description="Bearer token for authentication")
):
    """
    Get chat messages for a space.
    Requires authentication via Bearer token or login cookie.
    """
    try:
        # Require authentication (supports both cookies and Authorization header)
        user_id = await auth_utils.require_authentication(request, authorization)
        
        logger.info(f"Get messages request: space_id={space_id}, limit={limit}, offset={offset}, user={user_id}")
        
        # Parse space_id as UUID
        try:
            space_uuid = uuid.UUID(space_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid space ID format"
            )
        
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
    request_data: SendMessageRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    authorization: Optional[str] = Header(None, description="Bearer token for authentication")
):
    """
    Send a message and get AI response.
    Requires authentication via Bearer token or login cookie.
    """
    try:
        # Require authentication (supports both cookies and Authorization header)
        user_id = await auth_utils.require_authentication(request, authorization)
        
        logger.info(f"Send message request: space_id={space_id}, user={user_id}")
        
        # Parse space_id as UUID
        try:
            space_uuid = uuid.UUID(space_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid space ID format"
            )
        
        # Validate message content
        if not request_data.content or not request_data.content.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message content cannot be empty"
            )
        
        # Get JWT token for service-to-service calls
        service_token = auth_utils.get_token_for_service_calls(request, authorization)
        
        logger.info(f"Processing message from user {user_id} in space {space_id}")
        
        # Save user message
        user_message = await memory_service.save_message(
            space_id=space_uuid,
            user_id=user_id,
            content=request_data.content,
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
        
        # Generate assistant response with service token for backend calls
        response_text, response_metadata = await llm_service.generate_response(
            user_message=request_data.content,
            conversation_history=conversation_history,
            space_id=space_id,
            user_id=user_id,
            service_token=service_token
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
        logger.error(f"Error processing message for space {space_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while processing message"
        )


@router.get("/spaces/{space_id}/session", response_model=ChatSessionResponse)
async def get_chat_session(
    space_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    authorization: Optional[str] = Header(None, description="Bearer token for authentication")
):
    """
    Get chat session configuration.
    Requires authentication via Bearer token or login cookie.
    """
    try:
        # Require authentication (supports both cookies and Authorization header)
        user_id = await auth_utils.require_authentication(request, authorization)
        
        logger.info(f"Get chat session request: space_id={space_id}, user={user_id}")
        
        # Parse space_id as UUID
        try:
            space_uuid = uuid.UUID(space_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid space ID format"
            )
        
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
    request_data: ChatMemoryConfigRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    authorization: Optional[str] = Header(None, description="Bearer token for authentication")
):
    """
    Update chat memory configuration.
    Requires authentication via Bearer token or login cookie.
    """
    try:
        # Require authentication (supports both cookies and Authorization header)
        user_id = await auth_utils.require_authentication(request, authorization)
        
        logger.info(f"Update memory length request: space_id={space_id}, memory_length={request_data.memory_length}, user={user_id}")
        
        # Parse space_id as UUID
        try:
            space_uuid = uuid.UUID(space_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid space ID format"
            )
        
        # Validate memory length
        if request_data.memory_length < 1 or request_data.memory_length > 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Memory length must be between 1 and 50"
            )
        
        # Update session memory length
        session = await memory_service.update_session_memory_length(
            space_id=space_uuid,
            user_id=user_id,
            memory_length=request_data.memory_length,
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