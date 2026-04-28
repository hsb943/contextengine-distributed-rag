import os
import shutil
from pathlib import Path
from typing import Iterable, List, TypedDict
from uuid import NAMESPACE_URL, uuid5

from core.embeddings import EMBEDDING_DIMENSION
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

COLLECTION_NAME = "documents"
VECTOR_SIZE = EMBEDDING_DIMENSION
DEFAULT_STORAGE_PATH = Path(__file__).resolve().parent / "data"


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
    storage_path = get_storage_path()
    storage_path.mkdir(parents=True, exist_ok=True)
    return QdrantClient(path=str(storage_path))


def get_storage_path() -> Path:
    """Resolve the local Qdrant storage path."""
    return Path(os.getenv("QDRANT_PATH", str(DEFAULT_STORAGE_PATH)))


def ensure_collection(client: QdrantClient) -> None:
    """Create the documents collection or recreate it on size mismatch."""
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


def recreate_collection(client: QdrantClient) -> None:
    """Recreate the collection with the current embedding dimension."""
    if client.collection_exists(COLLECTION_NAME):
        client.delete_collection(COLLECTION_NAME)

    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
    )


def reset_storage() -> None:
    """Remove the local embedded Qdrant store so it can be recreated cleanly."""
    storage_path = get_storage_path()
    if storage_path.exists():
        shutil.rmtree(storage_path)


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

        try:
            client.upsert(collection_name=COLLECTION_NAME, points=points)
        except ValueError as exc:
            if "could not broadcast input array from shape" not in str(exc):
                raise

            # Old local collections can retain an outdated vector shape even
            # after service restarts. Recreate and retry once.
            client.close()
            reset_storage()

            retry_client = get_client()
            try:
                ensure_collection(retry_client)
                retry_client.upsert(collection_name=COLLECTION_NAME, points=points)
            finally:
                retry_client.close()
            return len(points)

        return len(points)
    finally:
        try:
            client.close()
        except Exception:
            pass


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
