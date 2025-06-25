from typing import List, Dict, Any, Optional
from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging
import numpy as np
import pymorphy2

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
                        r.rule_text,
                        r.section_title,
                        r.chapter_title,
                        r.start_char,
                        r.end_char,
                        r.text_length,
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

    async def retrieve_rules_rrf(
        self,
        request: RetrieveRequest,
        db: Session,
        distance_function: Optional[DistanceFunction] = None,
        c: int = 60
    ) -> RetrieveResponse:
        """
        Hybrid retrieval: BM25+vector+RRF for unique rules (articles).
        Returns top-k most relevant unique rules (full article text).
        """
        chunks = db.query(RuleChunk).join(Rule).filter(RuleChunk.embedding != None).all()
        texts = [c.chunk_text for c in chunks]
        ids = [c.chunk_id for c in chunks]
        embeddings = [self._parse_embedding(c.embedding) for c in chunks]

        def preprocess(text):
            tokens = [w for w in text.lower().split() if w.isalpha()]
            return tokens
        corpus = [preprocess(text) for text in texts]
        bm25 = BM25(corpus)
        query_tokens = preprocess(request.query)
        bm25_scores = bm25.get_scores(query_tokens)
        bm25_ranked = sorted(range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True)

        vector_k = min(max(request.k, 30), 20)
        vector_request = RetrieveRequest(
            query=request.query,
            k=vector_k,
            distance_function=request.distance_function or "cosine"
        )
        vector_response = await self.retrieve_documents(vector_request, db, distance_function)
        chunk_id_to_idx = {c.chunk_id: i for i, c in enumerate(chunks)}
        vector_ranked = []
        for result in vector_response.results:
            idx = chunk_id_to_idx.get(result.metadata.start_char)
            if idx is not None:
                vector_ranked.append(idx)

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

        top_rrf = sorted(rrf_scores, key=rrf_scores.get, reverse=True)[:request.k*2]
        seen_rule_ids = set()
        results = []
        for idx in top_rrf:
            chunk = chunks[idx]
            rule_id = chunk.rule_id
            if rule_id in seen_rule_ids:
                continue
            seen_rule_ids.add(rule_id)
            rule_text = chunk.rule.rule_text if hasattr(chunk.rule, 'rule_text') else ''
            metadata = DocumentMetadata(
                file_name=chunk.rule.file,
                rule_number=chunk.rule.rule_number,
                rule_title=chunk.rule.rule_title,
                section_title=chunk.rule.section_title,
                chapter_title=chunk.rule.chapter_title,
                start_char=chunk.rule.start_char if hasattr(chunk.rule, 'start_char') else None,
                end_char=chunk.rule.end_char if hasattr(chunk.rule, 'end_char') else None,
                text_length=chunk.rule.text_length if hasattr(chunk.rule, 'text_length') else None
            )
            results.append(RetrieveResult(
                text=rule_text,
                embedding=embeddings[idx],
                metadata=metadata,
                similarity_score=float(rrf_scores[idx])
            ))
            if len(results) >= request.k:
                break

        return RetrieveResponse(
            results=results,
            total_results=len(results),
            query=request.query,
            distance_function=f'rrf_bm25+vector'
        )

    async def retrieve_chunks_rrf(
        self,
        request: RetrieveRequest,
        db: Session,
        distance_function: Optional[DistanceFunction] = None,
        c: int = 60
    ) -> RetrieveResponse:
        """
        Hybrid retrieval: BM25+vector+RRF for unique chunks.
        Returns top-k most relevant unique chunks (chunk_text).
        """
        chunks = db.query(RuleChunk).join(Rule).filter(RuleChunk.embedding != None).all()
        texts = [c.chunk_text for c in chunks]
        ids = [c.chunk_id for c in chunks]
        metadatas = [
            DocumentMetadata(
                file_name=c.rule.file,
                rule_number=c.rule.rule_number,
                rule_title=c.rule.rule_title,
                section_title=c.rule.section_title,
                chapter_title=c.rule.chapter_title,
                start_char=c.chunk_char_start,
                end_char=c.chunk_char_end,
                text_length=(c.chunk_char_end - c.chunk_char_start)
            ) for c in chunks
        ]
        embeddings = [self._parse_embedding(c.embedding) for c in chunks]

        def preprocess(text):
            tokens = [w for w in text.lower().split() if w.isalpha()]
            return tokens
        corpus = [preprocess(text) for text in texts]
        bm25 = BM25(corpus)
        query_tokens = preprocess(request.query)
        bm25_scores = bm25.get_scores(query_tokens)
        bm25_ranked = sorted(range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True)

        vector_k = min(max(request.k, 30), 20)
        vector_request = RetrieveRequest(
            query=request.query,
            k=vector_k,
            distance_function=request.distance_function or "cosine"
        )
        vector_response = await self.retrieve_documents(vector_request, db, distance_function)
        chunk_id_to_idx = {c.chunk_id: i for i, c in enumerate(chunks)}
        vector_ranked = []
        for result in vector_response.results:
            idx = chunk_id_to_idx.get(result.metadata.start_char)
            if idx is not None:
                vector_ranked.append(idx)

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

        top_rrf = sorted(rrf_scores, key=rrf_scores.get, reverse=True)[:request.k*2]
        seen_chunk_ids = set()
        results = []
        for idx in top_rrf:
            chunk_id = ids[idx]
            if chunk_id in seen_chunk_ids:
                continue
            seen_chunk_ids.add(chunk_id)
            results.append(RetrieveResult(
                text=texts[idx],
                embedding=embeddings[idx],
                metadata=metadatas[idx],
                similarity_score=float(rrf_scores[idx])
            ))
            if len(results) >= request.k:
                break

        return RetrieveResponse(
            results=results,
            total_results=len(results),
            query=request.query,
            distance_function=f'rrf_bm25+vector'
        )


# Global retrieval service instance
retrieval_service = RetrievalService() 

# --- Pure Python BM25 implementation ---
import math
from collections import Counter, defaultdict

class BM25:
    def __init__(self, corpus, k1=1.5, b=0.75):
        self.corpus = corpus
        self.k1 = k1
        self.b = b
        self.N = len(corpus)
        self.avgdl = sum(len(doc) for doc in corpus) / self.N if self.N > 0 else 0
        self.doc_freqs = []
        self.idf = {}
        self.doc_len = []
        self._initialize()

    def _initialize(self):
        df = defaultdict(int)
        for document in self.corpus:
            frequencies = Counter(document)
            self.doc_freqs.append(frequencies)
            self.doc_len.append(len(document))
            for word in frequencies:
                df[word] += 1
        for word, freq in df.items():
            self.idf[word] = math.log(1 + (self.N - freq + 0.5) / (freq + 0.5))

    def get_scores(self, query):
        scores = []
        for idx, document in enumerate(self.corpus):
            score = 0.0
            doc_freq = self.doc_freqs[idx]
            dl = self.doc_len[idx]
            for word in query:
                if word not in doc_freq:
                    continue
                idf = self.idf.get(word, 0)
                tf = doc_freq[word]
                denom = tf + self.k1 * (1 - self.b + self.b * dl / self.avgdl)
                score += idf * (tf * (self.k1 + 1)) / denom
            scores.append(score)
        return scores 