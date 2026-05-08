from logging import getLogger
from typing import Iterable, List, TypedDict
from uuid import NAMESPACE_URL, uuid5

from core.embeddings import EMBEDDING_DIMENSION
from infrastructure.config.config import COLLECTION_NAME, QDRANT_HOST, QDRANT_PORT
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

VECTOR_SIZE = EMBEDDING_DIMENSION
LOGGER = getLogger(__name__)


class ChunkRecord(TypedDict):
    """Chunk data ready for vector storage."""

    chunk_id: str
    document_id: str
    doc_type: str | None
    text: str
    source: str
    chunk_index: int
    embedding: List[float]


class SearchResult(TypedDict):
    """Search result payload returned from vector lookup."""

    chunk_id: str
    document_id: str
    text: str
    score: float


def get_client() -> QdrantClient:
    """Return the shared Docker-backed Qdrant client."""
    return _CLIENT


def ensure_collection(client: QdrantClient) -> None:
    """Create the configured collection or recreate it on size mismatch."""
    if client.collection_exists(COLLECTION_NAME):
        collection_info = client.get_collection(COLLECTION_NAME)
        vector_config = collection_info.config.params.vectors
        existing_size = getattr(vector_config, "size", None)

        if existing_size == VECTOR_SIZE:
            return

        client.delete_collection(COLLECTION_NAME)

    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
    )


def store_chunks(chunks: Iterable[ChunkRecord]) -> int:
    """Store embedded chunks in Qdrant and return the number stored."""
    client = get_client()
    ensure_collection(client)

    points = [
        PointStruct(
            id=str(uuid5(NAMESPACE_URL, chunk["chunk_id"])),
            vector=chunk["embedding"],
            payload={
                "document_id": chunk["document_id"],
                "doc_type": chunk.get("doc_type", None),
                "chunk_id": chunk["chunk_id"],
                "text": chunk["text"],
                "source": chunk["source"],
                "chunk_index": chunk["chunk_index"],
            },
        )
        for chunk in chunks
    ]

    if not points:
        return 0

    client.upsert(collection_name=COLLECTION_NAME, points=points)
    return len(points)


def search_chunks(
    query_vector: List[float],
    top_k: int,
    query_filter: Filter | None = None,
) -> List[SearchResult]:
    """Search Qdrant for the most similar chunks."""
    if top_k <= 0:
        return []

    client = get_client()
    ensure_collection(client)

    if client.count(collection_name=COLLECTION_NAME).count == 0:
        return []

    if query_filter is None:
        LOGGER.warning("Running retrieval without metadata filters.")

    response = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        query_filter=query_filter,
        limit=top_k,
        with_payload=True,
    )

    results: List[SearchResult] = []
    for match in response.points:
        payload = match.payload or {}
        results.append(
            SearchResult(
                chunk_id=str(payload.get("chunk_id", "")),
                document_id=str(payload.get("document_id", "")),
                text=str(payload.get("text", "")),
                score=float(match.score),
            )
        )
    return results


LOGGER.info("Connected to Qdrant at %s:%s", QDRANT_HOST, QDRANT_PORT)
LOGGER.info("Using collection: %s", COLLECTION_NAME)
print(f"[QDRANT] Connecting to {QDRANT_HOST}:{QDRANT_PORT}")
_CLIENT = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
ensure_collection(_CLIENT)
