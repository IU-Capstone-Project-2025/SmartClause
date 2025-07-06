import httpx
import logging
from typing import List, Dict, Any, Optional
from ..core.config import settings

logger = logging.getLogger(__name__)


class DocumentService:
    """Service for fetching documents and analysis from backend service"""
    
    def __init__(self):
        # Backend service URL (port 8000)
        self.backend_base_url = "http://backend:8000/api"
        self.timeout = httpx.Timeout(30.0)
    
    async def get_documents_in_space(self, space_id: str, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all documents in a space from the backend service
        
        Args:
            space_id: Space UUID
            user_id: User ID for authorization
            
        Returns:
            List of document objects
        """
        try:
            url = f"{self.backend_base_url}/spaces/{space_id}/documents"
            headers = {"Authorization": f"Bearer {user_id}"}  # Using user_id as token for now
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                logger.debug(f"Fetching documents from {url} for space {space_id}")
                
                response = await client.get(url, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    documents = data.get("documents", [])
                    logger.debug(f"Retrieved {len(documents)} documents for space {space_id}")
                    return documents
                else:
                    logger.error(f"Backend documents error: {response.status_code} - {response.text}")
                    return []
                    
        except httpx.TimeoutException:
            logger.error(f"Timeout fetching documents from backend service")
            return []
        except Exception as e:
            logger.error(f"Error fetching documents: {e}")
            return []
    
    async def get_document_analysis(self, document_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get analysis results for a specific document
        
        Args:
            document_id: Document UUID
            user_id: User ID for authorization
            
        Returns:
            Analysis data or None if not found
        """
        try:
            url = f"{self.backend_base_url}/documents/{document_id}/analysis"
            headers = {"Authorization": f"Bearer {user_id}"}
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                logger.debug(f"Fetching analysis from {url} for document {document_id}")
                
                response = await client.get(url, headers=headers)
                
                if response.status_code == 200:
                    analysis_data = response.json()
                    logger.debug(f"Retrieved analysis for document {document_id}")
                    return analysis_data
                elif response.status_code == 404:
                    logger.debug(f"No analysis found for document {document_id}")
                    return None
                else:
                    logger.error(f"Backend analysis error: {response.status_code} - {response.text}")
                    return None
                    
        except httpx.TimeoutException:
            logger.error(f"Timeout fetching analysis for document {document_id}")
            return None
        except Exception as e:
            logger.error(f"Error fetching document analysis: {e}")
            return None
    
    async def get_space_documents_with_analysis(self, space_id: str, user_id: str) -> Dict[str, Any]:
        """
        Get all documents in a space along with their analysis results
        
        Args:
            space_id: Space UUID
            user_id: User ID for authorization
            
        Returns:
            Dictionary with documents and their analysis data
        """
        try:
            # Get all documents in the space
            documents = await self.get_documents_in_space(space_id, user_id)
            
            if not documents:
                return {"documents": [], "total_documents": 0, "analyzed_documents": 0}
            
            # Fetch analysis for completed documents
            documents_with_analysis = []
            analyzed_count = 0
            
            for doc in documents:
                doc_data = {
                    "id": doc.get("id"),
                    "name": doc.get("name"),
                    "status": doc.get("status"),
                    "analysis_summary": doc.get("analysis_summary"),
                    "analysis": None
                }
                
                # Only fetch analysis for completed documents
                if doc.get("status") == "completed":
                    analysis = await self.get_document_analysis(doc.get("id"), user_id)
                    if analysis:
                        doc_data["analysis"] = analysis
                        analyzed_count += 1
                
                documents_with_analysis.append(doc_data)
            
            logger.info(f"Retrieved {len(documents_with_analysis)} documents ({analyzed_count} with analysis) for space {space_id}")
            
            return {
                "documents": documents_with_analysis,
                "total_documents": len(documents),
                "analyzed_documents": analyzed_count
            }
            
        except Exception as e:
            logger.error(f"Error getting space documents with analysis: {e}")
            return {"documents": [], "total_documents": 0, "analyzed_documents": 0}
    
    def format_analysis_for_llm(self, space_documents: Dict[str, Any]) -> str:
        """
        Format document analysis data for LLM consumption
        
        Args:
            space_documents: Documents with analysis from get_space_documents_with_analysis
            
        Returns:
            Formatted string for LLM context
        """
        try:
            documents = space_documents.get("documents", [])
            analyzed_docs = [doc for doc in documents if doc.get("analysis")]
            
            if not analyzed_docs:
                return ""
            
            formatted_parts = ["=== DOCUMENT ANALYSIS IN THIS SPACE ==="]
            
            for i, doc in enumerate(analyzed_docs, 1):
                doc_name = doc.get("name", "Unknown Document")
                analysis = doc.get("analysis", {})
                
                formatted_parts.append(f"\n{i}. Document: {doc_name}")
                
                # Extract analysis points from the analyzer response
                if "document_points" in analysis:
                    document_points = analysis["document_points"]
                    for point in document_points:
                        point_content = point.get("point_content", "")
                        if point_content:
                            formatted_parts.append(f"   Content: {point_content}")
                        
                        # Include analysis points (risks, recommendations)
                        analysis_points = point.get("analysis_points", [])
                        for ap in analysis_points:
                            if ap.get("risk"):
                                formatted_parts.append(f"   Risk: {ap['risk']}")
                            if ap.get("recommendation"):
                                formatted_parts.append(f"   Recommendation: {ap['recommendation']}")
                
                # Include overall document metadata if available
                if "document_metadata" in analysis:
                    metadata = analysis["document_metadata"]
                    if metadata.get("title"):
                        formatted_parts.append(f"   Title: {metadata['title']}")
                
                formatted_parts.append("")  # Add spacing between documents
            
            result = "\n".join(formatted_parts)
            logger.debug(f"Formatted analysis context: {len(result)} characters")
            return result
            
        except Exception as e:
            logger.error(f"Error formatting analysis for LLM: {e}")
            return ""
    
    async def check_backend_health(self) -> bool:
        """Check if backend service is healthy"""
        try:
            # Try a simple endpoint to check connectivity
            url = f"{self.backend_base_url}/spaces/test/documents"
            headers = {"Authorization": "Bearer test"}
            
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url, headers=headers)
                # 401 or 400 is fine - it means the service is responding
                return response.status_code in [200, 400, 401, 404]
                
        except Exception as e:
            logger.error(f"Backend health check failed: {e}")
            return False


# Global document service instance
document_service = DocumentService() 