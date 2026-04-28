from typing import List

from sentence_transformers import SentenceTransformer

EMBEDDING_MODEL_NAME = "BAAI/bge-small-en-v1.5"
_MODEL = SentenceTransformer(EMBEDDING_MODEL_NAME, device="cpu")
EMBEDDING_DIMENSION = _MODEL.get_embedding_dimension()

def embed_text(text: str) -> List[float]:
    """Embed text with a shared sentence-transformers model.

    Embeddings are normalized so they work well with cosine similarity in
    Qdrant. The model is loaded once at module import time and reused.
    """
    embedding = _MODEL.encode(text, normalize_embeddings=True)
    return embedding.tolist()
