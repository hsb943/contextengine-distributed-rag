import logging
import sys
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from infrastructure.config import COLLECTION_NAME
from pipelines.ingestion_pipeline import ingest_document
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
    metadata: dict[str, object] | None = None


class IngestResponse(BaseModel):
    """Response returned after storing chunks."""

    status: str
    document_id: str
    num_chunks: int


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "ingestion-service"}


@app.on_event("startup")
def log_collection() -> None:
    LOGGER.info("Using Qdrant collection: %s", COLLECTION_NAME)


@app.post("/ingest", response_model=IngestResponse)
def ingest(request: IngestRequest) -> IngestResponse:
    """Parse the request and hand off to the ingestion pipeline."""
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text input is empty.")

    result = ingest_document(
        text=request.text,
        document_id=request.document_id,
        metadata=request.metadata or {"source": "text"},
    )
    return IngestResponse(
        status="stored",
        document_id=result["document_id"],
        num_chunks=result["chunks_created"],
    )


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
    result = ingest_document(
        text=text,
        document_id=document_id,
        metadata={"source": "pdf"},
    )
    return IngestResponse(
        status="stored",
        document_id=result["document_id"],
        num_chunks=result["chunks_created"],
    )
