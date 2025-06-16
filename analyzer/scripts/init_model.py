#!/usr/bin/env python3
"""
Script to download and cache the embedding model before application startup.
This ensures the model is available when the application starts.
"""

import os
from sentence_transformers import SentenceTransformer

def download_embedding_model():
    """Download and cache the embedding model specified in settings."""
    # Default model - this should match what's used in the application
    model_name = os.getenv('EMBEDDING_MODEL', 'BAAI/bge-m3')
    
    print(f"Downloading embedding model: {model_name}")
    
    try:
        # This will download and cache the model
        model = SentenceTransformer(model_name)
        print(f"Successfully downloaded and cached model: {model_name}")
        
        # Verify the model works by encoding a test sentence
        test_embedding = model.encode("This is a test sentence.")
        print(f"Model verification successful. Embedding dimension: {len(test_embedding)}")
        
    except Exception as e:
        print(f"Error downloading model {model_name}: {e}")
        raise

if __name__ == "__main__":
    download_embedding_model()
