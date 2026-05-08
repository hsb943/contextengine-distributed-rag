import logging
from typing import Any

from pipelines.generation_pipeline import generate_answer
from pipelines.retrieval_pipeline import retrieve

LOGGER = logging.getLogger(__name__)


def answer_query(
    query: str,
    top_k: int = 3,
    filters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run retrieval and answer generation for the FastAPI path."""
    LOGGER.info("Query received: %s", query)

    candidates = retrieve(query=query, top_k=50, filters=filters)
    LOGGER.info("Number of candidates retrieved: %d", len(candidates))

    final_chunks = candidates[:top_k]
    LOGGER.info("Final chunks selected: %d", len(final_chunks))
    result = generate_answer(query, final_chunks)
    return {
        "query": query,
        "answer": result["answer"],
        "sources": [
            {
                "chunk_id": chunk["chunk_id"],
                "document_id": chunk["document_id"],
                "text": chunk["text"],
            }
            for chunk in final_chunks
        ],
    }
