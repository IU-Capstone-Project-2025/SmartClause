from typing import List, Dict, Any, Optional
import logging
import httpx
from pydantic import BaseModel

from ..core.config import settings

logger = logging.getLogger(__name__)


class RetrieveRequest(BaseModel):
    """Request schema for analyzer retrieve endpoint"""
    query: str
    k: int = 5
    distance_function: str = "l2"


class RetrieveResult(BaseModel):
    """Individual retrieve result from analyzer"""
    text: str
    embedding: List[float]
    metadata: Dict[str, Any]
    similarity_score: float


class RetrieveResponse(BaseModel):
    """Response from analyzer retrieve endpoint"""
    results: List[RetrieveResult]
    total_results: int
    query: str
    distance_function: str


class RetrievalService:
    """Service for retrieving legal rules from the analyzer microservice"""
    
    def __init__(self):
        self.analyzer_base_url = settings.analyzer_base_url
        self.timeout = 30.0
    
    async def retrieve_legal_rules(
        self,
        query: str,
        k: int = 10,
        distance_function: str = "l2"
    ) -> Optional[RetrieveResponse]:
        """
        Retrieve legal rules from analyzer microservice using /retrieve-rules endpoint
        
        Args:
            query: Search query for legal rules
            k: Number of results to retrieve
            distance_function: Distance function to use
            
        Returns:
            RetrieveResponse or None if error
        """
        try:
            request_data = RetrieveRequest(
                query=query,
                k=k,
                distance_function=distance_function
            )
            
            url = f"{self.analyzer_base_url}/retrieve-rules"
            
            # Set up headers for the request
            headers = {"Content-Type": "application/json"}
            # Note: For service-to-service calls, analyzer might require authentication
            # This should be implemented with proper service account tokens
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                logger.debug(f"Requesting legal rules from {url} with query: '{query[:50]}...'")
                
                response = await client.post(
                    url,
                    json=request_data.dict(),
                    headers=headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    result = RetrieveResponse(**data)
                    logger.debug(f"Retrieved {len(result.results)} legal rules for query")
                    return result
                else:
                    logger.error(f"Analyzer retrieve-rules error: {response.status_code} - {response.text}")
                    return None
                    
        except httpx.TimeoutException:
            logger.error(f"Timeout retrieving legal rules from analyzer service")
            return None
        except Exception as e:
            logger.error(f"Error retrieving legal rules: {e}")
            return None
    
    async def check_analyzer_health(self) -> bool:
        """Check if analyzer service is healthy"""
        try:
            url = f"{self.analyzer_base_url}/health"
            
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url)
                return response.status_code == 200
                
        except Exception as e:
            logger.error(f"Analyzer health check failed: {e}")
            return False
    
    def format_rules_for_llm(self, retrieve_response: RetrieveResponse) -> str:
        """Format retrieved legal rules for LLM consumption"""
        try:
            if not retrieve_response or not retrieve_response.results:
                return ""
            
            formatted_parts = ["=== RELEVANT LEGAL RULES ==="]
            
            for i, rule in enumerate(retrieve_response.results, 1):
                metadata = rule.metadata
                rule_title = metadata.get("rule_title", "")
                file_name = metadata.get("file_name", "")
                
                if rule_title:
                    formatted_parts.append(f"\n{i}. {rule_title}")
                    if file_name:
                        formatted_parts.append(f"   Source: {file_name}")
                    formatted_parts.append(f"   Content: {rule.text}")
                else:
                    formatted_parts.append(f"\n{i}. {rule.text}")
                    if file_name:
                        formatted_parts.append(f"   Source: {file_name}")
            
            result = "\n".join(formatted_parts)
            logger.debug(f"Formatted {len(retrieve_response.results)} legal rules: {len(result)} characters")
            return result
            
        except Exception as e:
            logger.error(f"Error formatting legal rules for LLM: {e}")
            return ""


# Global retrieval service instance
retrieval_service = RetrievalService() 