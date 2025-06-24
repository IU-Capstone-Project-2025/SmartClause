from typing import List, Dict, Any, Optional
from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging
import numpy as np
from rank_bm25 import BM25Okapi
import pymorphy2
from stop_words import get_stop_words

from ..schemas.requests import RetrieveRequest
from ..schemas.responses import RetrieveResponse, RetrieveResult, DocumentMetadata
from ..models.database import LegalRule
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
                    id,
                    file_name,
                    rule_number,
                    rule_title,
                    rule_text,
                    section_title,
                    chapter_title,
                    start_char,
                    end_char,
                    text_length,
                    embedding,
                    {distance_query} as similarity_score
                FROM legal_rules 
                WHERE embedding IS NOT NULL
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
                    file_name=row.file_name,
                    rule_number=row.rule_number,
                    rule_title=row.rule_title,
                    section_title=row.section_title,
                    chapter_title=row.chapter_title,
                    start_char=row.start_char,
                    end_char=row.end_char,
                    text_length=row.text_length
                )
                
                # Create result object
                retrieve_result = RetrieveResult(
                    text=row.rule_text,
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

    def _preprocess_bm25(self, text, morph=None, stopwords=None):
        if morph is None:
            morph = pymorphy2.MorphAnalyzer()
        if stopwords is None:
            stopwords = set(get_stop_words("ru"))
        tokens = [w for w in text.lower().split() if w.isalpha()]
        tokens = [morph.normal_forms(w)[0] for w in tokens if w not in stopwords]
        return tokens

    async def retrieve_documents_bm25_rrf(
        self,
        request: 'RetrieveRequest',
        db: 'Session',
        c: int = 60
    ) -> 'RetrieveResponse':
        """
        Retrieve relevant documents using BM25 + vector search with RRF re-ranking.
        """
        # 1. Retrieve all documents
        rules = db.query(LegalRule).filter(LegalRule.embedding != None).all()
        texts = [r.rule_text for r in rules]
        ids = [r.id for r in rules]
        metadatas = [
            DocumentMetadata(
                file_name=r.file_name,
                rule_number=r.rule_number,
                rule_title=r.rule_title,
                section_title=r.section_title,
                chapter_title=r.chapter_title,
                start_char=r.start_char,
                end_char=r.end_char,
                text_length=r.text_length
            ) for r in rules
        ]
        embeddings = [self._parse_embedding(r.embedding) for r in rules]

        # 2. BM25
        morph = pymorphy2.MorphAnalyzer()
        stopwords = set(get_stop_words("ru"))
        corpus = [self._preprocess_bm25(text, morph, stopwords) for text in texts]
        bm25 = BM25Okapi(corpus)
        query_tokens = self._preprocess_bm25(request.query, morph, stopwords)
        bm25_scores = bm25.get_scores(query_tokens)
        bm25_ranked = sorted(range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True)

        # 3. Vector search (use the existing method)
        vector_response = await self.retrieve_documents(request, db)
        vector_rule_numbers = [r.metadata.rule_number for r in vector_response.results]
        vector_ranked = [ids.index(rules[i].id) for i, r in enumerate(rules) if r.rule_number in vector_rule_numbers]

        # 4. RRF
        def rrf(idx, ranked_list):
            try:
                return ranked_list.index(idx)
            except ValueError:
                return len(ranked_list)

        rrf_scores = {}
        for i in range(len(ids)):
            rv = rrf(i, vector_ranked)
            rf = rrf(i, bm25_ranked)
            rrf_scores[i] = 1/(c + rv) + 1/(c + rf)

        # 5. Final output (top-k)
        top_rrf = sorted(rrf_scores, key=rrf_scores.get, reverse=True)[:request.k]
        results = []
        for idx in top_rrf:
            results.append(RetrieveResult(
                text=texts[idx],
                embedding=embeddings[idx],
                metadata=metadatas[idx],
                similarity_score=float(rrf_scores[idx])
            ))

        return RetrieveResponse(
            results=results,
            total_results=len(results),
            query=request.query,
            distance_function=f'rrf_bm25+vector'
        )


# Global retrieval service instance
retrieval_service = RetrievalService() 