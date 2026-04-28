from pathlib import Path
from typing import Iterable, List, TypedDict
from uuid import NAMESPACE_URL, uuid5

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

COLLECTION_NAME = "documents"
VECTOR_SIZE = 128
STORAGE_PATH = Path(__file__).resolve().parent / "data"


class ChunkRecord(TypedDict):
    """Chunk data ready for vector storage."""

    chunk_id: str
    document_id: str
    text: str
    chunk_index: int
    embedding: List[float]


class SearchResult(TypedDict):
    """Search result payload returned from vector lookup."""

    chunk_id: str
    document_id: str
    text: str
    score: float


def get_client() -> QdrantClient:
    """Create a local Qdrant client for the shared storage path."""
    STORAGE_PATH.mkdir(parents=True, exist_ok=True)
    return QdrantClient(path=str(STORAGE_PATH))


def ensure_collection(client: QdrantClient) -> None:
    """Create the documents collection if it does not already exist."""
    if client.collection_exists(COLLECTION_NAME):
        return

    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
    )


def store_chunks(chunks: Iterable[ChunkRecord]) -> int:
    """Store embedded chunks in Qdrant and return the number stored."""
    client = get_client()
    try:
        ensure_collection(client)

        points = [
            PointStruct(
                id=str(uuid5(NAMESPACE_URL, chunk["chunk_id"])),
                vector=chunk["embedding"],
                payload={
                    "document_id": chunk["document_id"],
                    "chunk_id": chunk["chunk_id"],
                    "text": chunk["text"],
                    "chunk_index": chunk["chunk_index"],
                },
            )
            for chunk in chunks
        ]

        if not points:
            return 0

        client.upsert(collection_name=COLLECTION_NAME, points=points)
        return len(points)
    finally:
        client.close()


def search_chunks(query_vector: List[float], top_k: int) -> List[SearchResult]:
    """Search Qdrant for the most similar chunks."""
    if top_k <= 0:
        return []

    client = get_client()
    try:
        ensure_collection(client)

        if client.count(collection_name=COLLECTION_NAME).count == 0:
            return []

        response = client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
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
    finally:
        client.close()
