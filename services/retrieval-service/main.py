import logging
import sys
from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from infrastructure.config import COLLECTION_NAME
from pipelines.retrieval_pipeline import retrieve

app = FastAPI(title="Retrieval Service")
LOGGER = logging.getLogger(__name__)


class SearchRequest(BaseModel):
    """Search request for vector lookup."""

    query: str
    top_k: int = Field(default=5, ge=1)
    document_id: str | None = None
    filters: dict[str, object] | None = None


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

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "retrieval-service"}


@app.on_event("startup")
def log_collection() -> None:
    LOGGER.info("Using Qdrant collection: %s", COLLECTION_NAME)


@app.post("/search", response_model=SearchResponse)
def search(request: SearchRequest) -> SearchResponse:
    """Expose the retrieval pipeline over HTTP."""
    qdrant_filters: dict[str, object] | None = dict(request.filters or {})
    if request.document_id:
        qdrant_filters["document_id"] = request.document_id

    results = retrieve(
        query=request.query,
        top_k=request.top_k,
        filters=qdrant_filters,
    )
    return SearchResponse(query=request.query, results=results)
