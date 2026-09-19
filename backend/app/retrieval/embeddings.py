"""Embedding service — sentence-transformers for free local embeddings."""

import logging
from typing import List, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

_model = None


def get_embedding_model():
    """Lazy-load the sentence-transformers model."""
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
            _model = SentenceTransformer(settings.EMBEDDING_MODEL)
            logger.info("Embedding model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
    return _model


def generate_embedding(text: str) -> List[float]:
    """Generate embedding for a single text string."""
    model = get_embedding_model()
    embedding = model.encode(text, normalize_embeddings=True)
    return embedding.tolist()


def generate_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """Generate embeddings for a batch of texts."""
    import os
    import torch
    
    # Restrict PyTorch thread overhead to save RAM on 512MB instances
    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["MKL_NUM_THREADS"] = "1"
    torch.set_num_threads(1)
    
    model = get_embedding_model()
    # Reduced batch_size from 32 to 8 to prevent memory spikes
    embeddings = model.encode(texts, normalize_embeddings=True, batch_size=8)
    
    return [e.tolist() for e in embeddings]
