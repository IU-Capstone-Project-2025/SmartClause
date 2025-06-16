from sentence_transformers import SentenceTransformer
from typing import List, Union
import numpy as np
import logging
from ..core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating text embeddings using sentence-transformers"""
    
    def __init__(self):
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the sentence transformer model"""
        try:
            self.model = SentenceTransformer(settings.embedding_model)
            logger.info(f"Loaded embedding model: {settings.embedding_model}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
    
    def encode(self, texts: Union[str, List[str]]) -> Union[np.ndarray, List[np.ndarray]]:
        """
        Generate embeddings for text(s)
        
        Args:
            texts: Single text string or list of text strings
            
        Returns:
            Embeddings as numpy array(s)
        """
        if not self.model:
            raise RuntimeError("Embedding model not loaded")
        
        try:
            embeddings = self.model.encode(texts)
            return embeddings
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise
    
    def encode_to_list(self, texts: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """
        Generate embeddings and return as list(s) for JSON serialization
        
        Args:
            texts: Single text string or list of text strings
            
        Returns:
            Embeddings as list(s) of floats
        """
        embeddings = self.encode(texts)
        
        if isinstance(texts, str):
            return embeddings.tolist()
        else:
            return [emb.tolist() for emb in embeddings]


# Global embedding service instance
embedding_service = EmbeddingService() 