import logging
from typing import Any

from core.prompts import build_prompt
from core.text_cleaning import clean_ocr_text
from infrastructure.llm_client import call_llm

LOGGER = logging.getLogger(__name__)
MAX_CONTEXT_CHARS = 8000


def build_context(contexts: list[Any]) -> str:
    """Build a bounded prompt context from retrieved chunks."""
    sections = []
    total_chars = 0

    for index, context in enumerate(contexts, start=1):
        chunk_text = context["text"] if isinstance(context, dict) else context.text
        document_id = context["document_id"] if isinstance(context, dict) else context.document_id
        chunk_id = context["chunk_id"] if isinstance(context, dict) else context.chunk_id

        cleaned_text = clean_ocr_text(str(chunk_text))
        section = (
            f"[Source {index}]\n"
            f"Document ID: {document_id}\n"
            f"Chunk ID: {chunk_id}\n"
            f"Text: {cleaned_text}"
        )
        projected = total_chars + len(section) + 2
        if sections and projected > MAX_CONTEXT_CHARS:
            break

        sections.append(section)
        total_chars = projected

    return "\n\n---\n\n".join(sections)


def generate_answer(query: str, contexts: list[Any]) -> dict[str, Any]:
    """Build a prompt from contexts and call the LLM."""
    context_text = build_context(contexts)
    LOGGER.info("Generation context length (chars): %d", len(context_text))

    prompt = build_prompt(query, context_text)

    LOGGER.info("LLM call started.")
    answer = call_llm(prompt)
    LOGGER.info("LLM call finished.")

    return {
        "answer": answer,
        "sources": contexts,
    }
