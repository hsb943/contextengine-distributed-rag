import importlib.util
import sys
from pathlib import Path
from typing import Callable

from fastapi import FastAPI
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.embeddings import embed_text

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
    """Embed the query, search Qdrant, and return matching chunks."""
    query_vector = embed_text(request.query)
    matches = search_chunks(query_vector, request.top_k)
    results = [SearchResultItem(**match) for match in matches]
    return SearchResponse(query=request.query, results=results)
