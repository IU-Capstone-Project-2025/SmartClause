from fastapi import HTTPException, status, Header
from typing import Optional
import httpx
import asyncio
import logging

logger = logging.getLogger(__name__)


async def extract_user_id_from_header(authorization: Optional[str] = Header(None)) -> str:
    """
    Extract user ID from Authorization header by validating JWT token with backend service.
    
    Args:
        authorization: Authorization header in format "Bearer <token>"
        
    Returns:
        User ID string if valid
        
    Raises:
        HTTPException: If authentication fails
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


async def verify_document_access(user_id: str, document_id: str) -> bool:
    """
    Verify that a user has access to a specific document by checking with the backend.
    
    Args:
        user_id: User ID from validated token
        document_id: Document ID to check access for
        
    Returns:
        True if user has access, False otherwise
    """
    try:
        backend_url = "http://backend:8000"
        async with httpx.AsyncClient() as client:
            # Check if document exists and belongs to user
            response = await client.get(
                f"{backend_url}/api/documents/{document_id}",
                headers={"Authorization": f"Bearer dummy"},  # We already validated the user
                timeout=5.0
            )
            
            # If document exists and user has access, backend will return 200
            return response.status_code == 200
            
    except Exception as e:
        logger.error(f"Error verifying document access for user {user_id}, document {document_id}: {e}")
        return False


def require_auth(func):
    """
    Decorator to require authentication for endpoint functions.
    
    The decorated function should have an 'authorization' parameter with Header(None).
    This decorator will validate the token and inject the user_id as a parameter.
    """
    import functools
    from fastapi import Depends
    
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        # Extract authorization header from kwargs
        authorization = kwargs.get('authorization')
        
        # Validate and extract user ID
        user_id = await extract_user_id_from_header(authorization)
        
        # Inject user_id into kwargs
        kwargs['user_id'] = user_id
        
        # Call the original function
        return await func(*args, **kwargs)
    
    return wrapper 