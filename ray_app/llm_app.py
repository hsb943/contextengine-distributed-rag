from ray import serve
from starlette.requests import Request

from ray_app.deployments.llm import LLMDeployment


@serve.deployment
class LLMAPI:
    def __init__(self, llm):
        self.llm = llm

    async def __call__(self, request: Request):
        body = await request.json()
        query = body.get("query")
        contexts = body.get("contexts", [])

        if not query:
            return {"error": "query is required"}

        return await self.llm.generate.remote(
            query=query,
            contexts=contexts,
        )


if __name__ == "__main__":
    serve.start()
    app = LLMAPI.bind(LLMDeployment.bind())
    serve.run(app, route_prefix="/", blocking=True)
