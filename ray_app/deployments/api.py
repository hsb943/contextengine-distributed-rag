import logging
from pathlib import Path
from uuid import uuid4

from ray import serve
from starlette.requests import Request

from utils.pdf_parser import extract_text_from_pdf

LOGGER = logging.getLogger(__name__)


@serve.deployment(num_replicas=1, ray_actor_options={"num_cpus": 0.25})
class APIDeployment:
    def __init__(self, retrieval, llm, ingestion):
        self.retrieval = retrieval
        self.llm = llm
        self.ingestion = ingestion

    async def __call__(self, request: Request):
        if request.method == "GET":
            LOGGER.info("[API] Health check received")
            return {"status": "ok", "service": "ray-api"}

        path = request.url.path.rstrip("/") or "/"

        if path == "/ingest/file":
            form = await request.form()
            upload = form.get("file")
            if upload is None:
                return {"error": "file is required"}

            filename = getattr(upload, "filename", "") or ""
            if not filename.lower().endswith(".pdf"):
                return {"error": "Only PDF files are supported."}

            content = await upload.read()
            if not content:
                return {"error": "Uploaded file is empty."}

            try:
                text = extract_text_from_pdf(content)
            except Exception as exc:
                return {"error": f"Unable to parse PDF: {exc}"}

            if not text.strip():
                return {"error": "No extractable text found in PDF."}

            document_id = Path(filename).stem or str(uuid4())
            result = await self.ingestion.ingest.remote(
                text=text,
                document_id=document_id,
                metadata={"source": "pdf"},
            )
            return result

        if path == "/answer":
            body = await request.json()
            query = body.get("query")
            top_k = body.get("top_k", 3)
            filters = body.get("filters")
            document_id = body.get("document_id")
            if document_id and filters is None:
                filters = {"document_id": document_id}

            if not query:
                return {"error": "query is required"}

            candidates = await self.retrieval.search.remote(
                query=query,
                top_k=50,
                filters=filters,
            )
            final_contexts = candidates[:top_k]
            return await self.llm.generate.remote(
                query=query,
                contexts=final_contexts,
            )

        body = await request.json()
        route = body.get("route", "query")
        LOGGER.info("[API] Request received for route: %s", route)

        if route == "ingest":
            return await self.ingestion.ingest.remote(
                text=body["text"],
                document_id=body["document_id"],
                metadata=body.get("metadata"),
            )

        query = body.get("query")
        top_k = body.get("top_k", 3)
        filters = body.get("filters")
        document_id = body.get("document_id")
        if document_id and filters is None:
            filters = {"document_id": document_id}

        if not query:
            return {"error": "query is required"}

        candidates = await self.retrieval.search.remote(
            query=query,
            top_k=50,
            filters=filters,
        )
        final_contexts = candidates[:top_k]
        return await self.llm.generate.remote(
            query=query,
            contexts=final_contexts,
        )
