from ray import serve
from starlette.requests import Request

from ray_app.deployments.retrieval import RetrievalDeployment


@serve.deployment
class RetrievalAPI:
    def __init__(self, retrieval):
        self.retrieval = retrieval

    async def __call__(self, request: Request):
        body = await request.json()
        query = body.get("query")
        top_k = body.get("top_k", 50)
        filters = body.get("filters")

        if not query:
            return {"error": "query is required"}

        return await self.retrieval.search.remote(
            query=query,
            top_k=top_k,
            filters=filters,
        )


if __name__ == "__main__":
    serve.start()
    app = RetrievalAPI.bind(RetrievalDeployment.bind())
    serve.run(app, route_prefix="/", blocking=True)
