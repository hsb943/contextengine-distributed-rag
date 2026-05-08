import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pipelines.rag_pipeline import answer_query

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
    top_k: int = Field(default=3, ge=1, le=10)
    filters: dict[str, object] | None = None


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


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "llm-service"}


@app.post("/answer", response_model=AnswerResponse)
def answer(request_data: AnswerRequest) -> AnswerResponse:
    """Expose the reusable RAG pipeline over HTTP."""
    try:
        result = answer_query(
            query=request_data.query,
            top_k=request_data.top_k,
            filters=request_data.filters,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    sources = [
        SourceItem(
            chunk_id=item["chunk_id"],
            document_id=item["document_id"],
            text=item["text"],
        )
        for item in result["sources"]
    ]

    return AnswerResponse(
        query=request_data.query,
        answer=result["answer"],
        sources=sources,
    )
