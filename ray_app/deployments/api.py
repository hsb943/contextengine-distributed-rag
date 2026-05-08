import logging

from ray import serve
from starlette.requests import Request

LOGGER = logging.getLogger(__name__)


@serve.deployment(num_replicas=1)
class APIDeployment:
    def __init__(self, retrieval, llm, ingestion):
        self.retrieval = retrieval
        self.llm = llm
        self.ingestion = ingestion

    async def __call__(self, request: Request):
        body = await request.json()
        route = body.get("route", "query")
        LOGGER.info("Request received for route: %s", route)

        if route == "ingest":
            return await self.ingestion.ingest.remote(
                text=body["text"],
                document_id=body["document_id"],
                metadata=body.get("metadata"),
            )

        query = body.get("query")
        top_k = body.get("top_k", 3)
        filters = body.get("filters")

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
