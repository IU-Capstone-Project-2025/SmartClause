from typing import List, Optional, Tuple, Dict
from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging
import time


from ..schemas.requests import RetrieveRequest
from ..schemas.responses import RetrieveResponse, RetrieveResult, DocumentMetadata
from ..models.database import Rule, RuleChunk
from .embedding_service import embedding_service

logger = logging.getLogger(__name__)

class DistanceFunction(str, Enum):
    """Vector distance metrics supported by pgvector."""

    L2 = "l2"      # Euclidean (<->)
    COSINE = "cosine"  # Cosine (<=>)

    def sql_operator(self) -> str:
        return "<->" if self is DistanceFunction.L2 else "<=>"


class RetrievalService:
    """Hybrid BM25 + dense‑vector search executed completely in PostgreSQL.

    *   Two candidate sets (vector / FTS) are produced with `LIMIT k_vec`.
    *   Scores are converted to **Reciprocal Rank** (1/(C+rank)).
    *   Lists are fused via SUM(score) → higher = better.

    Public method signatures are unchanged, therefore **routes.py** remains
    untouched.  Each public method logs timings (ms) for key phases.
    """

    _C_RRF: int = 60              # Constant C in RRF
    _PRESELECT_MULTIPLIER: int = 10  # Oversampling factor before fusion
    _MAX_OVERSAMPLE: int = 20        # Respect Pydantic limit k<=20 in requests

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------

    async def retrieve_chunks_rrf(
        self,
        request: RetrieveRequest,
        db: Session,
        distance: DistanceFunction = DistanceFunction.L2,
    ) -> RetrieveResponse:
        """Return *k* chunks ranked by RRF(BM25 + vector)."""

        timings: Dict[str, float] = {}
        t0 = time.perf_counter()

        # --- encode -------------------------------------------------------
        q_vec: List[float] = embedding_service.encode_to_list(request.query)
        q_vec_pg = f"[{','.join(f'{x:.6f}' for x in q_vec)}]"
        t1 = time.perf_counter(); timings["encode_ms"] = (t1 - t0) * 1000

        # --- sql ----------------------------------------------------------
        k_final = max(1, request.k)
        k_vec = max(100, k_final * self._PRESELECT_MULTIPLIER)
        k_lex = k_vec

        sql = text(
            f"""
            WITH vec AS (
                SELECT chunk_id,
                       1.0 / (:c + ROW_NUMBER() OVER()) AS score
                FROM   rule_chunks
                ORDER  BY embedding {distance.sql_operator()} :q_vec
                LIMIT  :k_vec
            ),
            lex AS (
                SELECT chunk_id,
                       1.0 / (:c + ROW_NUMBER() OVER()) AS score
                FROM   rule_chunks
                WHERE  chunk_tsv @@ plainto_tsquery('russian', :q)
                ORDER  BY ts_rank_cd(chunk_tsv, plainto_tsquery('russian', :q)) DESC
                LIMIT  :k_lex
            ),
            fusion AS (
                SELECT chunk_id, SUM(score) AS rrf
                FROM   (
                    SELECT * FROM vec
                    UNION ALL
                    SELECT * FROM lex
                ) candidates
                GROUP  BY chunk_id
            )
            SELECT f.rrf,
                   rc.chunk_text,
                   rc.embedding,
                   rc.chunk_char_start,
                   rc.chunk_char_end,
                   r.file,
                   r.rule_number,
                   r.rule_title,
                   r.section_title,
                   r.chapter_title
            FROM   fusion f
            JOIN   rule_chunks rc ON rc.chunk_id = f.chunk_id
            JOIN   rules       r  ON r.rule_id   = rc.rule_id
            ORDER  BY f.rrf DESC
            LIMIT  :k_final;
            """
        )

        rows = db.execute(
            sql,
            {
                "c": self._C_RRF,
                "q": request.query,
                "q_vec": q_vec_pg,
                "k_vec": k_vec,
                "k_lex": k_lex,
                "k_final": k_final,
            },
        ).fetchall()
        t2 = time.perf_counter(); timings["sql_ms"] = (t2 - t1) * 1000

        # --- post‑processing ---------------------------------------------
        results: List[RetrieveResult] = [
            RetrieveResult(
                text=row.chunk_text,
                embedding=self._pgvector_to_list(row.embedding),
                similarity_score=float(row.rrf),
                metadata=DocumentMetadata(
                    file_name=row.file,
                    rule_number=row.rule_number,
                    rule_title=row.rule_title,
                    section_title=row.section_title,
                    chapter_title=row.chapter_title,
                    start_char=row.chunk_char_start,
                    end_char=row.chunk_char_end,
                    text_length=row.chunk_char_end - row.chunk_char_start,
                ),
            )
            for row in rows
        ]
        t3 = time.perf_counter(); timings["post_ms"] = (t3 - t2) * 1000
        timings["total_ms"] = (t3 - t0) * 1000

        logger.debug(
            "Hybrid search timings (ms) – encode: %.1f | sql: %.1f | post: %.1f | total: %.1f",
            timings["encode_ms"], timings["sql_ms"], timings["post_ms"], timings["total_ms"],
        )

        return RetrieveResponse(
            query=request.query,
            results=results,
            total_results=len(results),
            distance_function=f"rrf(bm25+{distance.value}) (sql)",
        )

    async def retrieve_rules_rrf(
        self,
        request: RetrieveRequest,
        db: Session,
        distance: DistanceFunction = DistanceFunction.L2,
    ) -> RetrieveResponse:
        """Return *k* unique rules (best chunk per rule)."""

        t0 = time.perf_counter()

        # oversample within Pydantic limit (k<=20)
        oversized_k = min(request.k * self._PRESELECT_MULTIPLIER, self._MAX_OVERSAMPLE)
        oversized_request = RetrieveRequest(query=request.query, k=oversized_k)  # type: ignore
        chunk_response = await self.retrieve_chunks_rrf(oversized_request, db, distance)
        t1 = time.perf_counter()

        best_by_rule: Dict[int, RetrieveResult] = {}
        for res in chunk_response.results:
            rule_id = res.metadata.rule_number
            if (rule_id not in best_by_rule) or (res.similarity_score > best_by_rule[rule_id].similarity_score):
                best_by_rule[rule_id] = res

        sorted_rules = sorted(best_by_rule.values(), key=lambda r: r.similarity_score, reverse=True)[: request.k]
        t2 = time.perf_counter()

        logger.debug(
            "Rules aggregation timings (ms) – chunks: %.1f | aggregate: %.1f | total: %.1f",
            (t1 - t0) * 1000,
            (t2 - t1) * 1000,
            (t2 - t0) * 1000,
        )

        return RetrieveResponse(
            query=request.query,
            results=sorted_rules,
            total_results=len(sorted_rules),
            distance_function=f"rrf(bm25+{distance.value}) (sql) – unique rules",
        )

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    def get_all_embeddings_and_labels(self, db: Session) -> Tuple[List[List[float]], List[str]]:
        sql = text("SELECT rc.embedding, r.file FROM rule_chunks rc JOIN rules r ON r.rule_id = rc.rule_id")
        rows = db.execute(sql).fetchall()
        embeddings = [self._pgvector_to_list(row.embedding) for row in rows]
        labels = [row.file for row in rows]
        return embeddings, labels

    @staticmethod
    def _pgvector_to_list(pg_vec) -> List[float]:
        if pg_vec is None:
            return []
        if isinstance(pg_vec, str):  # psycopg + vector might return text
            return [float(x) for x in pg_vec.strip("[]").split(",") if x]
        return list(pg_vec)


# Singleton instance
retrieval_service = RetrievalService()