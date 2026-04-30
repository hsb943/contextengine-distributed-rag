import logging
from typing import List

import torch
from sentence_transformers import SentenceTransformer

LOGGER = logging.getLogger(__name__)

EMBEDDING_MODEL_NAME = "BAAI/bge-base-en-v1.5"
_DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
_MODEL = SentenceTransformer(EMBEDDING_MODEL_NAME, device=_DEVICE)
EMBEDDING_DIMENSION = _MODEL.get_embedding_dimension()

LOGGER.info("Using embedding model: %s", EMBEDDING_MODEL_NAME)
LOGGER.info("Embedding dimension: %s", EMBEDDING_DIMENSION)


def embed_text(text: str) -> List[float]:
    """Embed text with a shared sentence-transformers model.

    Embeddings are normalized so they work well with cosine similarity in
    Qdrant. The model is loaded once at module import time and reused.
    """
    embedding = _MODEL.encode(text, normalize_embeddings=True)
    return embedding.tolist()


def embed_batch(texts: List[str]) -> List[List[float]]:
    """Embed multiple texts with the shared sentence-transformers model."""
    if not texts:
        return []

    embeddings = _MODEL.encode(
        texts,
        batch_size=32,
        normalize_embeddings=True,
    )
    return embeddings.tolist()
