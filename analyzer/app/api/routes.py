from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from fastapi.responses import Response
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
import logging
from ..core.database import get_db, engine
from ..schemas.requests import RetrieveRequest, AnalyzeRequest, EmbedRequest
from ..schemas.responses import RetrieveResponse, AnalyzeResponse, HealthResponse, EmbedResponse, RetrievalMetricsResponse
from ..services.analyzer_service import analyzer_service
from ..services.embedding_service import embedding_service
from ..services.retrieval_service import retrieval_service, DistanceFunction
from ..services.export_service import export_service
from ..core.config import settings
from ..models.database import Rule, RuleChunk, AnalysisResult
import numpy as np
from sklearn.metrics import silhouette_score

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_connected = True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_connected = False
    
    return HealthResponse(
        status="healthy" if db_connected else "unhealthy",
        version=settings.api_version,
        database_connected=db_connected
    )


@router.post("/retrieve-chunk", response_model=RetrieveResponse)
async def retrieve_chunks(
    request: RetrieveRequest,
    db: Session = Depends(get_db)
):
    """
    Retrieve relevant document chunks based on query using hybrid BM25+vector+RRF search (unique chunks).
    """
    try:
        logger.info(f"Retrieve chunks request: query='{request.query[:50]}...', k={request.k}, distance={request.distance_function}")
        if request.k > settings.max_k:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"k cannot exceed {settings.max_k}"
            )
        distance_func = DistanceFunction(request.distance_function)
        response = await retrieval_service.retrieve_chunks_rrf(request, db, distance_func)
        return response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid distance function: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in retrieve_chunks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during document retrieval"
        )


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_document(
    id: str = Form(..., description="Document identifier"),
    file: UploadFile = File(..., description="Document file to analyze"),
    db: Session = Depends(get_db)
):
    """
    Analyze a document for legal risks and recommendations
    
    This endpoint accepts a document file, processes it, and returns
    analysis points containing causes, risks, and recommendations.
    """
    try:
        logger.info(f"Analyze request: id='{id}', filename='{file.filename}'")
        
        # Read file content
        file_content = await file.read()
        
        # Validate file size
        if len(file_content) > settings.max_file_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size exceeds maximum allowed size of {settings.max_file_size} bytes"
            )
        
        # Create analyze request
        analyze_request = AnalyzeRequest(id=id, content=file_content)
        
        response = await analyzer_service.analyze_document(analyze_request, db)
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in analyze_document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during document analysis"
        )


@router.post("/retrieve-rules", response_model=RetrieveResponse)
async def retrieve_rules(
    request: RetrieveRequest,
    db: Session = Depends(get_db)
):
    """
    Retrieve k unique rules (articles) based on query using hybrid BM25+vector+RRF search (unique rules).
    """
    try:
        logger.info(f"Retrieve rules request: query='{request.query[:50]}...', k={request.k}, distance={request.distance_function}")
        if request.k > settings.max_k:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"k cannot exceed {settings.max_k}"
            )
        distance_func = DistanceFunction(request.distance_function)
        response = await retrieval_service.retrieve_rules_rrf(request, db, distance_func)
        return response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid distance function: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in retrieve_rules: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during rule retrieval"
        )


@router.post("/embed", response_model=EmbedResponse)
async def embed_text(request: EmbedRequest):
    """
    Generate embeddings for input text
    
    This endpoint accepts text input and returns the corresponding
    vector embedding using the configured sentence transformer model.
    """
    try:
        logger.info(f"Embed request: text='{request.text[:50]}...'")
        
        # Generate embedding using the embedding service
        embedding = embedding_service.encode_to_list(request.text)
        
        # Get dimension of the embedding
        dimension = len(embedding)
        
        return EmbedResponse(
            text=request.text,
            embedding=embedding,
            dimension=dimension
        )
        
    except Exception as e:
        logger.error(f"Error in embed_text: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during embedding generation"
        )


@router.get("/metrics/retrieval", response_model=RetrievalMetricsResponse)
async def retrieval_metrics(db: Session = Depends(get_db)):
    """
    Compute intrinsic retrieval metrics for all embeddings in the rule_chunks table.
    - Total dimension variance
    - Silhouette Score (document = cluster, by file_name)
    - Effective Intrinsic Dimensionality (EID) and Dimensionality Redundancy (DR)
    """
    # Use the retrieval service to get all embeddings and labels
    embeddings, labels = retrieval_service.get_all_embeddings_and_labels(db)
    if not embeddings or len(embeddings) < 2:
        return RetrievalMetricsResponse(
            total_variance=0.0,
            silhouette_score=0.0,
            eid=0.0,
            dr=0.0
        )
    embeddings = np.array(embeddings)
    labels = np.array(labels)

    # 1. Total dimension variance
    dim_variances = np.var(embeddings, axis=0)
    total_variance = float(np.sum(dim_variances))

    # 2. Silhouette Score (cosine distance, group by file_name)
    try:
        sil_score = float(silhouette_score(embeddings, labels, metric='cosine'))
    except Exception:
        sil_score = 0.0

    # 3. EID & DR (alpha=0.95)
    variances = np.var(embeddings, axis=0)
    sorted_vars = np.sort(variances)[::-1]
    total_var = np.sum(sorted_vars)
    cumsum = np.cumsum(sorted_vars) / total_var if total_var > 0 else np.zeros_like(sorted_vars)
    alpha = 0.95
    j_alpha = int(np.argmax(cumsum >= alpha))
    S_j = cumsum[j_alpha-1] if j_alpha > 0 else 0
    if total_var > 0 and sorted_vars[j_alpha] > 0:
        eid = j_alpha + (alpha - S_j) / sorted_vars[j_alpha]
    else:
        eid = 0.0
    dr = 1.0 - eid / len(sorted_vars) if len(sorted_vars) > 0 else 0.0

    return RetrievalMetricsResponse(
        total_variance=total_variance,
        silhouette_score=sil_score,
        eid=float(eid),
        dr=float(dr)
    )


# Export Endpoint

@router.get("/export/{document_id}/pdf")
async def export_analysis_pdf(
    document_id: str,
    db: Session = Depends(get_db)
):
    """
    Export analysis results as PDF report
    
    Args:
        document_id: Document identifier
        
    Returns:
        PDF file with formatted analysis report
    """
    try:
        logger.info(f"PDF export request for document: {document_id}")
        
        # Get analysis from database
        analysis_result = db.query(AnalysisResult).filter(
            AnalysisResult.document_id == document_id
        ).first()
        
        if not analysis_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis not found for this document"
            )
        
        # Export as PDF
        pdf_bytes = export_service.export_analysis_pdf(
            analysis_result.analysis_points
        )
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=analysis_report_{document_id}.pdf"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting PDF for document {document_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during PDF export"
        ) 