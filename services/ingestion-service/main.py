import importlib.util
import sys
from pathlib import Path
from typing import Callable

from fastapi import FastAPI
from pydantic import BaseModel

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.chunking import chunk_text
from core.embeddings import embed_text

app = FastAPI(title="Ingestion Service")


class IngestRequest(BaseModel):
    """Raw text ingestion request."""

    document_id: str
    text: str


class IngestedChunk(BaseModel):
    """Chunk produced by the ingestion pipeline."""

    chunk_id: str
    document_id: str
    text: str
    chunk_index: int
    embedding: list[float]


class IngestResponse(BaseModel):
    """Response returned after storing chunks."""

    status: str
    document_id: str
    num_chunks: int


def load_store_chunks() -> Callable[[list[dict]], int]:
    """Load Qdrant storage from the infrastructure layer."""
    module_path = PROJECT_ROOT / "infrastructure" / "vector-db" / "qdrant_client.py"
    spec = importlib.util.spec_from_file_location("qdrant_vector_client", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load Qdrant infrastructure module.")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.store_chunks


store_chunks = load_store_chunks()


def model_to_dict(model: BaseModel) -> dict:
    """Serialize a Pydantic model across supported Pydantic versions."""
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "ingestion-service"}


@app.post("/ingest", response_model=IngestResponse)
def ingest(request: IngestRequest) -> IngestResponse:
    """Chunk raw text, embed each chunk, store it, and return a status."""
    chunks = [
        IngestedChunk(
            chunk_id=f"{request.document_id}_{index}",
            document_id=request.document_id,
            text=chunk,
            chunk_index=index,
            embedding=embed_text(chunk),
        )
        for index, chunk in enumerate(chunk_text(request.text), start=1)
    ]

    stored_count = store_chunks([model_to_dict(chunk) for chunk in chunks])

    return IngestResponse(
        status="stored",
        document_id=request.document_id,
        num_chunks=stored_count,
    )
