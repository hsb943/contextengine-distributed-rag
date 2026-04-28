import importlib.util
import sys
from collections import defaultdict
from collections.abc import Callable
from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.embeddings import embed_text
from core.reranking import rerank

app = FastAPI(title="Retrieval Service")


class SearchRequest(BaseModel):
    """Search request for vector lookup."""

    query: str
    top_k: int = Field(default=5, ge=1)


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


def load_search_chunks() -> Callable[[list[float], int], list[dict]]:
    """Load Qdrant search logic from the infrastructure layer."""
    module_path = PROJECT_ROOT / "infrastructure" / "vector-db" / "qdrant_client.py"
    spec = importlib.util.spec_from_file_location("qdrant_vector_client", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load Qdrant infrastructure module.")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.search_chunks


search_chunks = load_search_chunks()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "retrieval-service"}


@app.post("/search", response_model=SearchResponse)
def search(request: SearchRequest) -> SearchResponse:
    """Embed the query, search Qdrant, rerank results, and return matches."""
    query_vector = embed_text(request.query)
    candidate_limit = max(10, request.top_k)
    matches = search_chunks(query_vector, candidate_limit)

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

    return SearchResponse(query=request.query, results=results)
