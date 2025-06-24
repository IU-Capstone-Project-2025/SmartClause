from typing import List, Dict, Any, Optional
from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging
import numpy as np

from ..schemas.requests import RetrieveRequest
from ..schemas.responses import RetrieveResponse, RetrieveResult, DocumentMetadata
from ..models.database import Rule, RuleChunk
from .embedding_service import embedding_service

logger = logging.getLogger(__name__)


class DistanceFunction(Enum):
    """Supported distance functions for similarity search"""
    COSINE = "cosine"
    L2 = "l2"
    INNER_PRODUCT = "inner_product"


class RetrievalService:
    """Service for basic distance-based document retrieval"""
    
    def __init__(self, default_distance_function: DistanceFunction = DistanceFunction.COSINE):
        self.default_distance_function = default_distance_function
    
    async def retrieve_rules(
        self,
        request: RetrieveRequest,
        db: Session,
        distance_function: Optional[DistanceFunction] = None
    ) -> RetrieveResponse:
        """
        Retrieve k unique rules based on query using distance-based similarity
        
        This method returns the k most relevant unique rules by finding the best
        chunk for each rule and then selecting the top k rules.
        
        Args:
            request: RetrieveRequest containing query and k
            db: Database session
            distance_function: Distance function to use (defaults to instance default)
            
        Returns:
            RetrieveResponse with k unique rules and their best matching chunks
        """
        if distance_function is None:
            distance_function = self.default_distance_function
            
        logger.info(f"Retrieving {request.k} unique rules for query: '{request.query[:100]}...' using {distance_function.value}")
        
        try:
            # Generate embedding for the query
            query_embedding = embedding_service.encode_to_list(request.query)
            
            # Convert to PostgreSQL array format for querying
            query_vector = f"[{','.join(map(str, query_embedding))}]"
            
            # Build the similarity query based on distance function
            distance_query = self._build_distance_query(distance_function, query_vector)
            
            # Execute similarity search to get best chunk per rule, then top k rules
            sql_query = text(f"""
                WITH rule_best_chunks AS (
                    SELECT DISTINCT ON (r.rule_id)
                        rc.chunk_id,
                        r.rule_id,
                        r.file,
                        r.rule_number,
                        r.rule_title,
                        rc.chunk_text,
                        r.section_title,
                        r.chapter_title,
                        rc.chunk_char_start,
                        rc.chunk_char_end,
                        (rc.chunk_char_end - rc.chunk_char_start) as text_length,
                        rc.embedding,
                        {distance_query} as similarity_score
                    FROM rule_chunks rc
                    JOIN rules r ON rc.rule_id = r.rule_id
                    WHERE rc.embedding IS NOT NULL
                    ORDER BY r.rule_id, similarity_score {"ASC" if distance_function == DistanceFunction.L2 else "DESC"}
                )
                SELECT *
                FROM rule_best_chunks
                ORDER BY similarity_score {"ASC" if distance_function == DistanceFunction.L2 else "DESC"}
                LIMIT :k
            """)
            
            result = db.execute(sql_query, {"k": request.k})
            rows = result.fetchall()
            
            # Convert results to response format
            results = []
            for row in rows:
                # Convert embedding from database format to list
                embedding_list = self._parse_embedding(row.embedding)
                
                # Create metadata object
                metadata = DocumentMetadata(
                    file_name=row.file,
                    rule_number=row.rule_number,
                    rule_title=row.rule_title,
                    section_title=row.section_title,
                    chapter_title=row.chapter_title,
                    start_char=row.chunk_char_start,
                    end_char=row.chunk_char_end,
                    text_length=row.text_length
                )
                
                # Create result object
                retrieve_result = RetrieveResult(
                    text=row.chunk_text,
                    embedding=embedding_list,
                    metadata=metadata,
                    similarity_score=float(row.similarity_score)
                )
                
                results.append(retrieve_result)
            
            return RetrieveResponse(
                results=results,
                total_results=len(results),
                query=request.query,
                distance_function=distance_function.value
            )
            
        except Exception as e:
            logger.error(f"Error in retrieve_rules: {e}")
            raise

    async def retrieve_documents(
        self, 
        request: RetrieveRequest, 
        db: Session,
        distance_function: Optional[DistanceFunction] = None
    ) -> RetrieveResponse:
        """
        Retrieve relevant documents based on query using distance-based similarity
        
        Args:
            request: RetrieveRequest containing query and k
            db: Database session
            distance_function: Distance function to use (defaults to instance default)
            
        Returns:
            RetrieveResponse with results including metadata and similarity scores
        """
        if distance_function is None:
            distance_function = self.default_distance_function
            
        logger.info(f"Retrieving documents for query: '{request.query[:100]}...' using {distance_function.value}")
        
        try:
            # Generate embedding for the query
            query_embedding = embedding_service.encode_to_list(request.query)
            
            # Convert to PostgreSQL array format for querying
            query_vector = f"[{','.join(map(str, query_embedding))}]"
            
            # Build the similarity query based on distance function
            distance_query = self._build_distance_query(distance_function, query_vector)
            
            # Execute the similarity search
            sql_query = text(f"""
                SELECT 
                    rc.chunk_id,
                    r.file,
                    r.rule_number,
                    r.rule_title,
                    rc.chunk_text,
                    r.section_title,
                    r.chapter_title,
                    rc.chunk_char_start,
                    rc.chunk_char_end,
                    (rc.chunk_char_end - rc.chunk_char_start) as text_length,
                    rc.embedding,
                    {distance_query} as similarity_score
                FROM rule_chunks rc
                JOIN rules r ON rc.rule_id = r.rule_id
                WHERE rc.embedding IS NOT NULL
                ORDER BY similarity_score {"ASC" if distance_function == DistanceFunction.L2 else "DESC"}
                LIMIT :k
            """)
            
            result = db.execute(sql_query, {"k": request.k})
            rows = result.fetchall()
            
            # Convert results to response format
            results = []
            for row in rows:
                # Convert embedding from database format to list
                embedding_list = self._parse_embedding(row.embedding)
                
                # Create metadata object
                metadata = DocumentMetadata(
                    file_name=row.file,
                    rule_number=row.rule_number,
                    rule_title=row.rule_title,
                    section_title=row.section_title,
                    chapter_title=row.chapter_title,
                    start_char=row.chunk_char_start,
                    end_char=row.chunk_char_end,
                    text_length=row.text_length
                )
                
                # Create result object
                retrieve_result = RetrieveResult(
                    text=row.chunk_text,
                    embedding=embedding_list,
                    metadata=metadata,
                    similarity_score=float(row.similarity_score)
                )
                
                results.append(retrieve_result)
            
            return RetrieveResponse(
                results=results,
                total_results=len(results),
                query=request.query,
                distance_function=distance_function.value
            )
            
        except Exception as e:
            logger.error(f"Error in retrieve_documents: {e}")
            raise
    
    def _build_distance_query(self, distance_function: DistanceFunction, query_vector: str) -> str:
        """Build the distance query based on the selected function"""
        if distance_function == DistanceFunction.COSINE:
            return f"(1 - (embedding <=> '{query_vector}'))"
        elif distance_function == DistanceFunction.L2:
            return f"(embedding <-> '{query_vector}')"
        elif distance_function == DistanceFunction.INNER_PRODUCT:
            return f"((embedding <#> '{query_vector}') * -1)"
        else:
            raise ValueError(f"Unsupported distance function: {distance_function}")
    
    def _parse_embedding(self, embedding_raw) -> List[float]:
        """Parse embedding from database format to list of floats"""
        if embedding_raw is None:
            return []
        
        # Handle different possible formats
        if isinstance(embedding_raw, list):
            return [float(x) for x in embedding_raw]
        elif isinstance(embedding_raw, str):
            # Remove brackets and split by comma
            clean_str = embedding_raw.strip('[]')
            return [float(x.strip()) for x in clean_str.split(',')]
        else:
            # Try to convert directly
            try:
                return [float(x) for x in embedding_raw]
            except (TypeError, ValueError):
                logger.warning(f"Could not parse embedding: {type(embedding_raw)}")
                return []
    
    def set_distance_function(self, distance_function: DistanceFunction):
        """Change the default distance function"""
        self.default_distance_function = distance_function
        logger.info(f"Distance function changed to: {distance_function.value}")

    def get_all_embeddings_and_labels(self, db: Session):
        """
        Retrieve all embeddings and their file_name labels from the rule_chunks table.
        Returns:
            embeddings: List[List[float]]
            labels: List[str]
        """
        chunks = db.query(RuleChunk).join(Rule).filter(RuleChunk.embedding != None).all()
        embeddings = []
        labels = []
        for chunk in chunks:
            emb = self._parse_embedding(chunk.embedding)
            if emb:
                embeddings.append(emb)
                labels.append(chunk.rule.file or f"chunk_{chunk.chunk_id}")
        return embeddings, labels


# Global retrieval service instance
retrieval_service = RetrievalService() 