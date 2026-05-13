from functools import lru_cache
from logging import getLogger
from typing import Iterable, List, TypedDict
from uuid import NAMESPACE_URL, uuid5

from core.embeddings import EMBEDDING_DIMENSION
from infrastructure.config.config import COLLECTION_NAME, QDRANT_HOST, QDRANT_PORT
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
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


@lru_cache(maxsize=1)
def get_client() -> QdrantClient:
    """Return the shared Docker-backed Qdrant client."""
    LOGGER.info("Connecting to Qdrant at %s:%s", QDRANT_HOST, QDRANT_PORT)
    print(f"[QDRANT] Connecting to {QDRANT_HOST}:{QDRANT_PORT}")
    return QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)


def initialize_qdrant() -> None:
    """Initialize collection state once during deployment startup."""
    ensure_collection_exists(get_client())


def _collection_vector_size(client: QdrantClient) -> int | None:
    collection_info = client.get_collection(COLLECTION_NAME)
    vector_config = collection_info.config.params.vectors
    return getattr(vector_config, "size", None)


def _create_collection(client: QdrantClient) -> None:
    try:
        LOGGER.info("[QDRANT INIT] Creating collection")
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )
    except UnexpectedResponse as exc:
        message = str(exc)
        if "already exists" in message or "409" in message:
            LOGGER.info("[QDRANT INIT] Collection already created by another replica")
            return
        raise


def ensure_collection_exists(client: QdrantClient) -> None:
    """Ensure the configured collection exists and matches the expected vector size."""
    if client.collection_exists(COLLECTION_NAME):
        LOGGER.info("[QDRANT INIT] Collection exists")
        existing_size = _collection_vector_size(client)

        if existing_size == VECTOR_SIZE:
            return

        LOGGER.warning("[QDRANT INIT] Vector size mismatch detected")
        client.delete_collection(COLLECTION_NAME)
        _create_collection(client)
        return

    _create_collection(client)


def store_chunks(chunks: Iterable[ChunkRecord]) -> int:
    """Store embedded chunks in Qdrant and return the number stored."""
    client = get_client()

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

LOGGER.info("Using collection: %s", COLLECTION_NAME)
