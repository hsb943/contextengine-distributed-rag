import logging
from typing import Any

from core.chunking import chunk_text
from core.embeddings import embed_batch
from core.text_cleaning import clean_text
from infrastructure.vector_db.qdrant_client import store_chunks

LOGGER = logging.getLogger(__name__)


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
