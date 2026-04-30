import importlib.util
import logging
import sys
from pathlib import Path
from typing import Callable
from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.chunking import chunk_text
from core.embeddings import embed_text
from infrastructure.config import COLLECTION_NAME
from utils.pdf_parser import extract_text_from_pdf

LOGGER = logging.getLogger(__name__)

app = FastAPI(title="Ingestion Service")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class IngestRequest(BaseModel):
    """Raw text ingestion request."""

    document_id: str
    text: str


class IngestedChunk(BaseModel):
    """Chunk produced by the ingestion pipeline."""

    chunk_id: str
    document_id: str
    text: str
    source: str
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


@app.on_event("startup")
def log_collection() -> None:
    LOGGER.info("Using Qdrant collection: %s", COLLECTION_NAME)


def ingest_document(document_id: str, text: str, source: str) -> IngestResponse:
    """Run the shared text ingestion pipeline for one document."""
    chunks = [
        IngestedChunk(
            chunk_id=f"{document_id}_{index}",
            document_id=document_id,
            text=chunk,
            source=source,
            chunk_index=index,
            embedding=embed_text(chunk),
        )
        for index, chunk in enumerate(chunk_text(text), start=1)
    ]

    if chunks:
        average_size = sum(len(chunk.text.split()) for chunk in chunks) / len(chunks)
        LOGGER.info(
            "Chunked document %s into %d chunks (avg %.1f words)",
            document_id,
            len(chunks),
            average_size,
        )

    stored_count = store_chunks([model_to_dict(chunk) for chunk in chunks])

    return IngestResponse(
        status="stored",
        document_id=document_id,
        num_chunks=stored_count,
    )


@app.post("/ingest", response_model=IngestResponse)
def ingest(request: IngestRequest) -> IngestResponse:
    """Chunk raw text, embed each chunk, store it, and return a status."""
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text input is empty.")

    return ingest_document(request.document_id, request.text, source="text")


@app.post("/ingest/file", response_model=IngestResponse)
def ingest_file(file: UploadFile = File(...)) -> IngestResponse:
    """Extract text from a PDF file and run the existing ingestion pipeline."""
    filename = file.filename or ""
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    content = file.file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        text = extract_text_from_pdf(content)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Unable to parse PDF: {exc}") from exc

    if not text:
        raise HTTPException(status_code=400, detail="No extractable text found in PDF.")

    document_id = Path(filename).stem or str(uuid4())
    return ingest_document(document_id, text, source="pdf")
