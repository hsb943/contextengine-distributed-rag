import logging
from typing import Any

from core.prompts import build_prompt
from core.text_cleaning import clean_ocr_text
from infrastructure.llm_client import call_llm
from pipelines.retrieval_pipeline import retrieve

LOGGER = logging.getLogger(__name__)
MAX_CONTEXT_CHARS = 8000
MIN_SCORE = 0.3


def build_context(sources: list[dict[str, Any]]) -> str:
    """Build a bounded prompt context from retrieved chunks."""
    sections = []
    total_chars = 0

    for index, source in enumerate(sources, start=1):
        cleaned_text = clean_ocr_text(str(source["text"]))
        section = (
            f"[Source {index}]\n"
            f"Document ID: {source['document_id']}\n"
            f"Chunk ID: {source['chunk_id']}\n"
            f"Text: {cleaned_text}"
        )
        projected = total_chars + len(section) + 2
        if sections and projected > MAX_CONTEXT_CHARS:
            break

        sections.append(section)
        total_chars = projected

    return "\n\n---\n\n".join(sections)


def answer_query(
    query: str,
    top_k: int = 3,
    filters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run retrieval, thresholding, context building, and answer generation."""
    LOGGER.info("Query received: %s", query)

    candidates = retrieve(query=query, top_k=50, filters=filters)
    LOGGER.info("Number of candidates retrieved: %d", len(candidates))

    filtered = [candidate for candidate in candidates if float(candidate["score"]) >= MIN_SCORE]
    LOGGER.info("Number after filtering: %d", len(filtered))

    if not filtered:
        LOGGER.info("No candidates met the minimum score threshold.")
        return {
            "query": query,
            "answer": "I don't know.",
            "sources": [],
        }

    final_chunks = filtered[:top_k]
    context = build_context(final_chunks)
    LOGGER.info("Context size (chars): %d", len(context))

    prompt = build_prompt(query, context)

    LOGGER.info("LLM call started.")
    answer = call_llm(prompt)
    LOGGER.info("LLM call finished.")

    return {
        "query": query,
        "answer": answer,
        "sources": [
            {
                "chunk_id": chunk["chunk_id"],
                "document_id": chunk["document_id"],
                "text": chunk["text"],
            }
            for chunk in final_chunks
        ],
    }
