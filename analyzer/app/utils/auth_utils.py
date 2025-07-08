import httpx
import logging
from typing import Optional
from fastapi import HTTPException, status
from ..core.config import settings

logger = logging.getLogger(__name__)


class AuthUtils:
    """Authentication utilities for analyzer service"""
    
    def __init__(self):
        # Backend service URL for token validation
        self.backend_base_url = "http://backend:8000/api"
        self.timeout = 5.0
    
    async def extract_user_id_from_header(self, authorization: Optional[str]) -> Optional[str]:
        """
        Extract user ID from Authorization header by validating JWT token with backend service.
        
        Args:
            authorization: Authorization header value (e.g., "Bearer <token>")
            
        Returns:
            User ID string if valid, None if invalid or missing
        """
        try:
            if authorization is None or authorization.strip() == "":
                logger.debug("No authorization header provided")
                return None
            
            if not authorization.startswith("Bearer "):
                logger.debug("Authorization header is not in Bearer format")
                return None
                
            token = authorization[7:]  # Remove "Bearer " prefix
            logger.debug(f"Received Bearer token: {token[:10]}...")
            
            # Validate token with backend service
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                try:
                    response = await client.get(
                        f"{self.backend_base_url}/auth/profile",
                        headers={"Authorization": authorization}
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
            logger.error(f"Failed to extract user ID from authorization header: {e}")
            return None
    
    async def require_authentication(self, authorization: Optional[str]) -> str:
        """
        Require valid authentication and return user ID.
        Raises HTTPException if authentication fails.
        
        Args:
            authorization: Authorization header value
            
        Returns:
            User ID string
            
        Raises:
            HTTPException: If authentication is invalid or missing
        """
        user_id = await self.extract_user_id_from_header(authorization)
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required. Please provide a valid Bearer token."
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