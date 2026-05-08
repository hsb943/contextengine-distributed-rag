import logging
import importlib.util
from collections import defaultdict
from typing import Any
from pathlib import Path

from core.embeddings import embed_text
from core.reranking import rerank
from qdrant_client.models import FieldCondition, Filter, MatchValue

LOGGER = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_search_chunks():
    """Load Qdrant search logic from the infrastructure layer."""
    module_path = PROJECT_ROOT / "infrastructure" / "vector-db" / "qdrant_client.py"
    spec = importlib.util.spec_from_file_location("qdrant_vector_client", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load Qdrant infrastructure module.")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.search_chunks


search_chunks = load_search_chunks()


def build_filter(filters: dict[str, Any] | None) -> Filter | None:
    """Build an optional Qdrant filter from metadata conditions."""
    if not filters:
        return None

    conditions = []
    for key, value in filters.items():
        conditions.append(
            FieldCondition(
                key=key,
                match=MatchValue(value=value),
            )
        )

    return Filter(must=conditions)


def retrieve(
    query: str,
    top_k: int = 50,
    filters: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Retrieve and rerank relevant chunks for a query."""
    LOGGER.info("Query received: %s", query)

    query_vector = embed_text(query)
    candidate_limit = max(50, top_k)
    qdrant_filter = build_filter(filters)

    LOGGER.info("Filter applied: %s", qdrant_filter is not None)
    LOGGER.info("Retrieval candidates: %d", candidate_limit)

    matches = search_chunks(query_vector, candidate_limit, qdrant_filter)
    LOGGER.info("Candidates retrieved: %d", len(matches))

    ranked_documents = rerank(
        query,
        [match["text"] for match in matches],
    )
    LOGGER.info("Number after reranking: %d", len(ranked_documents))

    matches_by_text: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for match in matches:
        matches_by_text[match["text"]].append(match)

    results: list[dict[str, Any]] = []
    for text, score in ranked_documents[:top_k]:
        match = matches_by_text[text].pop(0)
        results.append(
            {
                "chunk_id": match["chunk_id"],
                "document_id": match["document_id"],
                "text": match["text"],
                "score": score,
                "metadata": {
                    "document_id": match["document_id"],
                    "chunk_id": match["chunk_id"],
                },
            }
        )

    LOGGER.info("Final top_k: %d", len(results))
    return results
