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
from ..services.document_service import document_service
from ..models.database import MessageType

logger = logging.getLogger(__name__)

router = APIRouter()


async def extract_user_id_from_header(authorization: Optional[str] = Header(None)) -> str:
    """
    Extract user ID from Authorization header by validating JWT token with backend service.
    """
    try:
        if authorization is None or authorization.strip() == "":
            logger.debug("No authorization header provided")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header is required"
            )
        
        if not authorization.startswith("Bearer "):
            logger.debug("Authorization header is not in Bearer format")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header must be in Bearer format"
            )
            
        token = authorization[7:]
        logger.debug(f"Received Bearer token: {token[:10]}...")
        
        # Validate token with backend service
        import httpx
        
        try:
            backend_url = "http://backend:8000"  # Backend service URL
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{backend_url}/api/auth/profile",
                    headers={"Authorization": authorization},
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    user_data = response.json()
                    user_id = user_data.get("id")
                    if user_id:
                        logger.debug(f"Successfully validated token for user: {user_id}")
                        return user_id
                    else:
                        logger.error("Backend returned valid response but no user ID")
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid token: no user ID"
                        )
                else:
                    logger.debug(f"Backend token validation failed: {response.status_code}")
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid or expired token"
                    )
                    
        except httpx.RequestError as e:
            logger.error(f"Error connecting to backend for token validation: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service unavailable"
            )
        except httpx.TimeoutException:
            logger.error("Timeout validating token with backend")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service timeout"
            )
        
    except HTTPException:
        raise
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
        user_id = await extract_user_id_from_header(authorization)
        
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
        user_id = await extract_user_id_from_header(authorization)
        
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
        user_id = await extract_user_id_from_header(authorization)
        
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
        user_id = await extract_user_id_from_header(authorization)
        
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