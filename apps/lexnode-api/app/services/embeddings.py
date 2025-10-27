"""
Embedding generation service for semantic search.
"""

import os
import logging
from typing import List, Optional
import numpy as np

logger = logging.getLogger(__name__)

# Global embedding model
_embedding_model = None


async def init_embeddings():
    """Initialize embedding model."""
    global _embedding_model
    
    model_name = os.getenv("EMBEDDING_MODEL", "text-embedding-ada-002")
    logger.info(f"Initializing embedding model: {model_name}")
    
    # For now, we'll use OpenAI embeddings
    # In production, could use sentence-transformers for local embeddings
    _embedding_model = model_name
    
    logger.info("Embedding model initialized")


def get_embedding_model():
    """Get embedding model."""
    return _embedding_model


async def generate_embedding(text: str) -> List[float]:
    """
    Generate embedding vector for text.
    
    Args:
        text: Text to embed
        
    Returns:
        Embedding vector
    """
    try:
        # Use OpenAI embeddings API
        from openai import AsyncOpenAI
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or api_key == "your-openai-api-key-here":
            # Return mock embedding for development
            logger.warning("Using mock embedding (OpenAI API key not configured)")
            return [0.1] * 1536  # Ada-002 dimension
        
        client = AsyncOpenAI(api_key=api_key)
        
        response = await client.embeddings.create(
            model=_embedding_model or "text-embedding-ada-002",
            input=text
        )
        
        return response.data[0].embedding
        
    except Exception as e:
        logger.error(f"Failed to generate embedding: {e}")
        # Return zero vector as fallback
        return [0.0] * 1536


async def batch_generate_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for multiple texts.
    
    Args:
        texts: List of texts to embed
        
    Returns:
        List of embedding vectors
    """
    embeddings = []
    
    for text in texts:
        embedding = await generate_embedding(text)
        embeddings.append(embedding)
    
    return embeddings


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors.
    
    Args:
        vec1: First vector
        vec2: Second vector
        
    Returns:
        Similarity score (0-1)
    """
    if not vec1 or not vec2:
        return 0.0
    
    vec1_array = np.array(vec1)
    vec2_array = np.array(vec2)
    
    dot_product = np.dot(vec1_array, vec2_array)
    norm1 = np.linalg.norm(vec1_array)
    norm2 = np.linalg.norm(vec2_array)
    
    if float(norm1) == 0 or float(norm2) == 0:
        return 0.0
    
    return float(dot_product / (norm1 * norm2))
