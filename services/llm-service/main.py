import json
import os
import sys
from pathlib import Path
from urllib import error, request

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.llm import generate_answer

RETRIEVAL_SERVICE_URL = os.getenv(
    "RETRIEVAL_SERVICE_URL",
    "http://127.0.0.1:8001/search",
)
MAX_CONTEXT_CHARS = 4000

app = FastAPI(title="LLM Service")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnswerRequest(BaseModel):
    """Answer generation request."""

    query: str
    top_k: int = Field(default=3, ge=1)
    document_id: str


class SourceItem(BaseModel):
    """Source chunk used for answer generation."""

    chunk_id: str
    document_id: str
    text: str


class AnswerResponse(BaseModel):
    """Final answer and supporting sources."""

    query: str
    answer: str
    sources: list[SourceItem]


def fetch_retrieval_results(query: str, top_k: int, document_id: str) -> list[dict]:
    """Call the retrieval service and return top results."""
    payload = json.dumps(
        {"query": query, "top_k": top_k, "document_id": document_id}
    ).encode("utf-8")
    http_request = request.Request(
        RETRIEVAL_SERVICE_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with request.urlopen(http_request, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Retrieval service request failed: {details}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"Unable to reach retrieval service: {exc.reason}") from exc

    return result.get("results", [])


def build_context(sources: list[dict]) -> str:
    """Build a bounded context string from retrieved sources."""
    sections = []
    total_chars = 0

    for index, source in enumerate(sources, start=1):
        section = (
            f"[Source {index}]\n"
            f"Document ID: {source['document_id']}\n"
            f"Chunk ID: {source['chunk_id']}\n"
            f"Text: {source['text']}"
        )
        projected = total_chars + len(section) + 2
        if sections and projected > MAX_CONTEXT_CHARS:
            break

        sections.append(section)
        total_chars = projected

    return "\n\n---\n\n".join(sections)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "llm-service"}


@app.post("/answer", response_model=AnswerResponse)
def answer(request_data: AnswerRequest) -> AnswerResponse:
    """Retrieve supporting chunks and generate a final answer."""
    if not request_data.document_id.strip():
        raise HTTPException(status_code=400, detail="document_id is required.")

    try:
        results = fetch_retrieval_results(
            request_data.query,
            request_data.top_k,
            request_data.document_id,
        )
        context = build_context(results)
        answer_text = generate_answer(request_data.query, context)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    sources = [
        SourceItem(
            chunk_id=result["chunk_id"],
            document_id=result["document_id"],
            text=result["text"],
        )
        for result in results[: request_data.top_k]
    ]

    return AnswerResponse(
        query=request_data.query,
        answer=answer_text,
        sources=sources,
    )
