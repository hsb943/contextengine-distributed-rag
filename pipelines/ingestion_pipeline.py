import importlib.util
import logging
from pathlib import Path
from typing import Any
from uuid import uuid4

from core.chunking import chunk_text
from core.embeddings import embed_batch
from core.text_cleaning import clean_text

LOGGER = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_store_chunks():
    """Load Qdrant storage from the infrastructure layer."""
    module_path = PROJECT_ROOT / "infrastructure" / "vector-db" / "qdrant_client.py"
    spec = importlib.util.spec_from_file_location("qdrant_vector_client", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load Qdrant infrastructure module.")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.store_chunks


store_chunks = load_store_chunks()


def ingest_document(
    text: str,
    document_id: str,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Clean, chunk, embed, and store a document in Qdrant."""
    cleaned_text = clean_text(text)
    chunks = chunk_text(cleaned_text)

    LOGGER.info("Document ID: %s", document_id)
    LOGGER.info("Chunks created: %d", len(chunks))

    if not chunks:
        LOGGER.info("Embedding completed: 0")
        LOGGER.info("Upsert success: 0")
        return {
            "document_id": document_id,
            "chunks_created": 0,
        }

    embeddings = embed_batch(chunks)

    source = "pdf"
    doc_type = None
    if metadata:
        source = str(metadata.get("source", source))
        doc_type = metadata.get("doc_type")

    chunk_records = []
    for index, (chunk, embedding) in enumerate(zip(chunks, embeddings), start=1):
        chunk_records.append(
            {
                "chunk_id": f"{document_id}_{index}",
                "document_id": document_id,
                "doc_type": doc_type,
                "text": chunk,
                "source": source,
                "chunk_index": index,
                "embedding": embedding,
            }
        )

    LOGGER.info("Embedding completed: %d", len(chunk_records))
    stored_count = store_chunks(chunk_records)
    LOGGER.info("Upsert success: %d", stored_count)

    return {
        "document_id": document_id,
        "chunks_created": stored_count,
    }
