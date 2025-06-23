from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
import logging
from ..core.database import get_db, engine
from ..schemas.requests import RetrieveRequest, AnalyzeRequest, EmbedRequest
from ..schemas.responses import RetrieveResponse, AnalyzeResponse, HealthResponse, EmbedResponse
from ..services.analyzer_service import analyzer_service
from ..services.embedding_service import embedding_service
from ..services.retrieval_service import retrieval_service, DistanceFunction
from ..core.config import settings

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


@router.post("/retrieve", response_model=RetrieveResponse)
async def retrieve_documents(
    request: RetrieveRequest,
    db: Session = Depends(get_db)
):
    """
    Retrieve relevant documents based on query using distance-based similarity
    
    This endpoint performs semantic search over the legal document corpus
    and returns the k most relevant text chunks with their embeddings and metadata.
    Supports configurable distance functions: cosine, l2, inner_product.
    """
    try:
        logger.info(f"Retrieve request: query='{request.query[:50]}...', k={request.k}, distance={request.distance_function}")
        
        # Validate k parameter
        if request.k > settings.max_k:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"k cannot exceed {settings.max_k}"
            )
        
        # Convert string distance function to enum
        distance_func = DistanceFunction(request.distance_function)
        
        # Use the new retrieval service with distance-based similarity
        response = await retrieval_service.retrieve_documents(request, db, distance_func)
        return response
        
    except ValueError as e:
        # Handle invalid distance function
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid distance function: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in retrieve_documents: {e}")
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


@router.post("/retrieve-json", response_model=RetrieveResponse)
async def retrieve_documents_json(
    request: RetrieveRequest,
    db: Session = Depends(get_db)
):
    """
    Alternative JSON endpoint for retrieve (for easier testing)
    Same functionality as /retrieve but explicitly named for JSON requests
    """
    return await retrieve_documents(request, db)


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