import importlib.util
import logging
import sys
from collections import defaultdict
from collections.abc import Callable
from typing import Any
from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.embeddings import embed_text
from infrastructure.config import COLLECTION_NAME
from core.reranking import rerank
from qdrant_client.models import Filter, FieldCondition, MatchValue

app = FastAPI(title="Retrieval Service")
LOGGER = logging.getLogger(__name__)


class SearchRequest(BaseModel):
    """Search request for vector lookup."""

    query: str
    top_k: int = Field(default=5, ge=1)
    document_id: str | None = None
    filters: dict[str, Any] | None = None


class SearchResultItem(BaseModel):
    """Retrieved chunk returned to the caller."""

    chunk_id: str
    document_id: str
    text: str
    score: float


class SearchResponse(BaseModel):
    """Search response for the query."""

    query: str
    results: list[SearchResultItem]


def load_search_chunks() -> Callable[[list[float], int, Filter | None], list[dict]]:
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
    """Build a Qdrant filter from optional metadata filters."""
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


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "retrieval-service"}


@app.on_event("startup")
def log_collection() -> None:
    LOGGER.info("Using Qdrant collection: %s", COLLECTION_NAME)


@app.post("/search", response_model=SearchResponse)
def search(request: SearchRequest) -> SearchResponse:
    """Embed the query, search Qdrant, rerank results, and return matches."""
    query_vector = embed_text(request.query)
    candidate_limit = max(50, request.top_k)
    qdrant_filters: dict[str, Any] | None = dict(request.filters or {})
    if request.document_id:
        qdrant_filters["document_id"] = request.document_id

    qdrant_filter = build_filter(qdrant_filters)
    LOGGER.info("Document ID filter: %s", request.document_id)
    LOGGER.info("Filters: %s", request.filters)
    LOGGER.info("Filter applied: %s", qdrant_filter is not None)
    LOGGER.info("Retrieval candidates: %d", candidate_limit)
    matches = search_chunks(query_vector, candidate_limit, qdrant_filter)
    LOGGER.info("Candidates retrieved: %d", len(matches))
    LOGGER.info("Reranker input: %d", len(matches))

    ranked_documents = rerank(
        request.query,
        [match["text"] for match in matches],
    )

    matches_by_text: dict[str, list[dict]] = defaultdict(list)
    for match in matches:
        matches_by_text[match["text"]].append(match)

    results = []
    for text, score in ranked_documents[: request.top_k]:
        match = matches_by_text[text].pop(0)
        results.append(
            SearchResultItem(
                chunk_id=match["chunk_id"],
                document_id=match["document_id"],
                text=match["text"],
                score=score,
            )
        )

    LOGGER.info("Final results: %d", len(results))
    return SearchResponse(query=request.query, results=results)
