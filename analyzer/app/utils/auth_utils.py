import httpx
import logging
from typing import Optional
from fastapi import HTTPException, status, Request
from ..core.config import settings

logger = logging.getLogger(__name__)


class AuthUtils:
    """Authentication utilities for analyzer service"""
    
    def __init__(self):
        # Backend service URL for token validation
        self.backend_base_url = "http://backend:8000/api"
        self.timeout = 5.0
        self.jwt_cookie_name = "smartclause_token"
    
    def extract_token_from_cookie(self, request: Request) -> Optional[str]:
        """
        Extract JWT token from cookie.
        
        Args:
            request: FastAPI Request object containing cookies
            
        Returns:
            JWT token string if found, None otherwise
        """
        try:
            if request is None:
                return None
                
            token = request.cookies.get(self.jwt_cookie_name)
            if token and token.strip():
                logger.debug("Found JWT token in cookie")
                return token
            
            return None
        except Exception as e:
            logger.error(f"Error extracting token from cookie: {e}")
            return None
    
    def extract_token_from_header(self, authorization: Optional[str]) -> Optional[str]:
        """
        Extract JWT token from Authorization header.
        
        Args:
            authorization: Authorization header value (e.g., "Bearer <token>")
            
        Returns:
            JWT token string if found, None otherwise
        """
        try:
            if authorization is None or authorization.strip() == "":
                return None
            
            if not authorization.startswith("Bearer "):
                return None
                
            token = authorization[7:]  # Remove "Bearer " prefix
            if token and token.strip():
                logger.debug("Found JWT token in Authorization header")
                return token
            
            return None
        except Exception as e:
            logger.error(f"Error extracting token from header: {e}")
            return None
    
    def extract_token_from_request(self, request: Request, authorization: Optional[str]) -> Optional[str]:
        """
        Extract JWT token from request (trying both cookies and Authorization header).
        First tries to get token from cookie, then falls back to Authorization header.
        
        Args:
            request: FastAPI Request object (can be None for backward compatibility)
            authorization: Authorization header value (can be None)
            
        Returns:
            JWT token string if found, None otherwise
        """
        try:
            # First try to get token from cookie
            if request is not None:
                token = self.extract_token_from_cookie(request)
                if token:
                    logger.debug("Using JWT token from cookie")
                    return token
            
            # If no token from cookie, try Authorization header
            token = self.extract_token_from_header(authorization)
            if token:
                logger.debug("Using JWT token from Authorization header")
                return token
            
            return None
        except Exception as e:
            logger.error(f"Error extracting token from request: {e}")
            return None
    
    async def validate_token_with_backend(self, token: Optional[str]) -> Optional[str]:
        """
        Validate JWT token with backend service and extract user ID.
        
        Args:
            token: JWT token string
            
        Returns:
            User ID string if valid, None if invalid
        """
        try:
            if not token:
                return None
            
            # Validate token with backend service
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                try:
                    response = await client.get(
                        f"{self.backend_base_url}/auth/profile",
                        headers={"Authorization": f"Bearer {token}"}
                    )
                    
                    if response.status_code == 200:
                        user_data = response.json()
                        user_id = user_data.get("id")
                        if user_id:
                            logger.debug(f"Successfully validated token for user: {user_id}")
                            return user_id
                        else:
                            logger.error("Backend returned valid response but no user ID")
                            return None
                    else:
                        logger.debug(f"Backend token validation failed: {response.status_code}")
                        return None
                        
                except httpx.RequestError as e:
                    logger.error(f"Error connecting to backend for token validation: {e}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error validating token with backend: {e}")
            return None
    
    async def extract_user_id_from_request(self, request: Request, authorization: Optional[str]) -> Optional[str]:
        """
        Extract user ID from request (trying both cookies and Authorization header).
        
        Args:
            request: FastAPI Request object (can be None for backward compatibility)
            authorization: Authorization header value (can be None)
            
        Returns:
            User ID string if valid, None if invalid or missing
        """
        try:
            # Extract token from request
            token = self.extract_token_from_request(request, authorization)
            
            # Validate token with backend and get user ID
            return await self.validate_token_with_backend(token)
            
        except Exception as e:
            logger.error(f"Failed to extract user ID from request: {e}")
            return None
    
    async def extract_user_id_from_header(self, authorization: Optional[str]) -> Optional[str]:
        """
        Extract user ID from Authorization header by validating JWT token with backend service.
        This method is kept for backward compatibility.
        
        Args:
            authorization: Authorization header value (e.g., "Bearer <token>")
            
        Returns:
            User ID string if valid, None if invalid or missing
        """
        return await self.extract_user_id_from_request(None, authorization)
    
    async def require_authentication(self, request: Request = None, authorization: Optional[str] = None) -> str:
        """
        Require valid authentication and return user ID.
        Raises HTTPException if authentication fails.
        
        Args:
            request: FastAPI Request object (optional)
            authorization: Authorization header value (optional)
            
        Returns:
            User ID string
            
        Raises:
            HTTPException: If authentication is invalid or missing
        """
        user_id = await self.extract_user_id_from_request(request, authorization)
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required. Please provide a valid Bearer token or login cookie."
            )
        
        return user_id
    
    async def validate_token_format(self, token: str) -> bool:
        """
        Basic validation of JWT token format (without signature verification).
        
        Args:
            token: JWT token string
            
        Returns:
            True if format is valid, False otherwise
        """
        try:
            # Basic format check: should have 3 parts separated by dots
            parts = token.split('.')
            if len(parts) != 3:
                return False
            
            # Each part should be non-empty
            return all(part.strip() for part in parts)
            
        except Exception:
            return False


# Global auth utils instance
auth_utils = AuthUtils() 