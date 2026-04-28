from typing import Iterable, List, TypedDict
from uuid import NAMESPACE_URL, uuid5

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

COLLECTION_NAME = "documents"
VECTOR_SIZE = 128

client = QdrantClient(":memory:")


class ChunkRecord(TypedDict):
    """Chunk data ready for vector storage."""

    chunk_id: str
    document_id: str
    text: str
    chunk_index: int
    embedding: List[float]


def ensure_collection() -> None:
    """Create the documents collection if it does not already exist."""
    if client.collection_exists(COLLECTION_NAME):
        return

    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
    )


def store_chunks(chunks: Iterable[ChunkRecord]) -> int:
    """Store embedded chunks in Qdrant and return the number stored."""
    ensure_collection()

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
