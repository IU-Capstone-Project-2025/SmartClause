from typing import List, Dict, Any, Optional
import logging
import httpx
import asyncio
from pydantic import BaseModel

from ..core.config import settings

logger = logging.getLogger(__name__)


class RetrieveRequest(BaseModel):
    """Request schema for analyzer retrieve endpoint"""
    query: str
    k: int = 5
    distance_function: str = "cosine"


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
    """Service for integrating with analyzer microservice retrieval endpoints"""
    
    def __init__(self):
        self.analyzer_base_url = settings.analyzer_base_url
        self.timeout = 30.0
    
    async def retrieve_legal_context(
        self,
        query: str,
        k: int = 5,
        distance_function: str = "cosine"
    ) -> Optional[RetrieveResponse]:
        """
        Retrieve legal context from analyzer microservice using /retrieve-rules endpoint
        
        Args:
            query: Search query for legal context
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
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                logger.debug(f"Requesting legal context from {url} with query: '{query[:50]}...'")
                
                response = await client.post(
                    url,
                    json=request_data.dict()
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
            logger.error(f"Timeout retrieving legal context from analyzer service")
            return None
        except Exception as e:
            logger.error(f"Error retrieving legal context: {e}")
            return None
    
    async def retrieve_document_chunks(
        self,
        query: str,
        k: int = 5,
        distance_function: str = "cosine"
    ) -> Optional[RetrieveResponse]:
        """
        Retrieve document chunks from analyzer microservice using /retrieve-chunk endpoint
        
        Args:
            query: Search query for document chunks
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
            
            url = f"{self.analyzer_base_url}/retrieve-chunk"
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                logger.debug(f"Requesting document chunks from {url} with query: '{query[:50]}...'")
                
                response = await client.post(
                    url,
                    json=request_data.dict()
                )
                
                if response.status_code == 200:
                    data = response.json()
                    result = RetrieveResponse(**data)
                    logger.debug(f"Retrieved {len(result.results)} document chunks for query")
                    return result
                else:
                    logger.error(f"Analyzer retrieve-chunk error: {response.status_code} - {response.text}")
                    return None
                    
        except httpx.TimeoutException:
            logger.error(f"Timeout retrieving document chunks from analyzer service")
            return None
        except Exception as e:
            logger.error(f"Error retrieving document chunks: {e}")
            return None
    
    async def get_combined_context(
        self,
        query: str,
        k_rules: int = 3,
        k_chunks: int = 3
    ) -> Dict[str, Any]:
        """
        Get combined context from both legal rules and document chunks
        
        Args:
            query: Search query
            k_rules: Number of legal rules to retrieve
            k_chunks: Number of document chunks to retrieve
            
        Returns:
            Dictionary with legal and document context
        """
        try:
            # Retrieve both legal rules and document chunks in parallel
            legal_task = self.retrieve_legal_context(query, k_rules)
            chunks_task = self.retrieve_document_chunks(query, k_chunks)
            
            legal_response, chunks_response = await asyncio.gather(
                legal_task, chunks_task, return_exceptions=True
            )
            
            context = {
                "legal_rules": [],
                "document_chunks": [],
                "query": query
            }
            
            # Process legal rules response
            if isinstance(legal_response, RetrieveResponse):
                for result in legal_response.results:
                    context["legal_rules"].append({
                        "text": result.text,
                        "metadata": result.metadata,
                        "similarity_score": result.similarity_score
                    })
            elif isinstance(legal_response, Exception):
                logger.error(f"Error retrieving legal rules: {legal_response}")
            
            # Process document chunks response
            if isinstance(chunks_response, RetrieveResponse):
                for result in chunks_response.results:
                    context["document_chunks"].append({
                        "text": result.text,
                        "metadata": result.metadata,
                        "similarity_score": result.similarity_score
                    })
            elif isinstance(chunks_response, Exception):
                logger.error(f"Error retrieving document chunks: {chunks_response}")
            
            logger.debug(f"Combined context: {len(context['legal_rules'])} rules, {len(context['document_chunks'])} chunks")
            return context
            
        except Exception as e:
            logger.error(f"Error getting combined context: {e}")
            return {
                "legal_rules": [],
                "document_chunks": [],
                "query": query
            }
    
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
    
    def format_context_for_llm(self, context: Dict[str, Any]) -> str:
        """Format retrieved context for LLM consumption"""
        try:
            formatted_parts = []
            
            # Add legal rules context
            if context.get("legal_rules"):
                formatted_parts.append("=== RELEVANT LEGAL RULES ===")
                for i, rule in enumerate(context["legal_rules"], 1):
                    metadata = rule.get("metadata", {})
                    rule_title = metadata.get("rule_title", "")
                    file_name = metadata.get("file_name", "")
                    
                    if rule_title:
                        formatted_parts.append(f"\n{i}. {rule_title}")
                        if file_name:
                            formatted_parts.append(f"   Source: {file_name}")
                        formatted_parts.append(f"   Content: {rule['text']}")
                    else:
                        formatted_parts.append(f"\n{i}. {rule['text']}")
                        if file_name:
                            formatted_parts.append(f"   Source: {file_name}")
            
            # Add document chunks context
            if context.get("document_chunks"):
                if formatted_parts:  # Add separator if we have legal rules
                    formatted_parts.append("\n")
                formatted_parts.append("=== RELEVANT DOCUMENT EXCERPTS ===")
                for i, chunk in enumerate(context["document_chunks"], 1):
                    metadata = chunk.get("metadata", {})
                    file_name = metadata.get("file_name", "")
                    
                    formatted_parts.append(f"\n{i}. {chunk['text']}")
                    if file_name:
                        formatted_parts.append(f"   Source: {file_name}")
            
            result = "\n".join(formatted_parts)
            logger.debug(f"Formatted context: {len(result)} characters")
            return result
            
        except Exception as e:
            logger.error(f"Error formatting context for LLM: {e}")
            return ""


# Global retrieval service instance
retrieval_service = RetrievalService() 