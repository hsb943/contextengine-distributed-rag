from ray import serve
from starlette.requests import Request

from ray_app.deployments.ingestion import IngestionDeployment


@serve.deployment
class IngestionAPI:
    def __init__(self, ingestion):
        self.ingestion = ingestion

    async def __call__(self, request: Request):
        body = await request.json()
        return await self.ingestion.ingest.remote(
            text=body["text"],
            document_id=body["document_id"],
            metadata=body.get("metadata"),
        )


if __name__ == "__main__":
    serve.start(http_options={"host": "0.0.0.0", "port": 8000})
    app = IngestionAPI.bind(IngestionDeployment.bind())
    serve.run(app, route_prefix="/", blocking=True)
