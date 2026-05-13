import logging
from threading import Lock
from typing import List

import torch
from sentence_transformers import SentenceTransformer

from infrastructure.model_cache import resolve_embedding_model_path

LOGGER = logging.getLogger(__name__)

EMBEDDING_MODEL_NAME = "BAAI/bge-base-en-v1.5"
_DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
EMBEDDING_DIMENSION = 768
_MODEL: SentenceTransformer | None = None
_MODEL_LOCK = Lock()

LOGGER.info("Using embedding model: %s", EMBEDDING_MODEL_NAME)
LOGGER.info("Embedding dimension: %s", EMBEDDING_DIMENSION)


def _get_model() -> SentenceTransformer:
    """Load the embedding model lazily so import-time startup stays light."""
    global _MODEL

    if _MODEL is None:
        with _MODEL_LOCK:
            if _MODEL is None:
                model_path = resolve_embedding_model_path()
                LOGGER.info("Loading embedding model from cache on %s", _DEVICE)
                _MODEL = SentenceTransformer(str(model_path), device=_DEVICE)
    return _MODEL


def embed_text(text: str) -> List[float]:
    """Embed text with a shared sentence-transformers model.

    Embeddings are normalized so they work well with cosine similarity in
    Qdrant. The model is loaded lazily and reused.
    """
    model = _get_model()
    embedding = model.encode(text, normalize_embeddings=True)
    return embedding.tolist()


def embed_batch(texts: List[str]) -> List[List[float]]:
    """Embed multiple texts with the shared sentence-transformers model."""
    if not texts:
        return []

    model = _get_model()
    embeddings = model.encode(
        texts,
        batch_size=32,
        normalize_embeddings=True,
    )
    return embeddings.tolist()
