from ray import serve

from ray_app.deployments.api import APIDeployment
from ray_app.deployments.ingestion import IngestionDeployment
from ray_app.deployments.llm import LLMDeployment
from ray_app.deployments.retrieval import RetrievalDeployment


def build_app():
    retrieval = RetrievalDeployment.bind()
    llm = LLMDeployment.bind()
    ingestion = IngestionDeployment.bind()
    return APIDeployment.bind(retrieval, llm, ingestion)


app = build_app()


if __name__ == "__main__":
    serve.start(http_options={"host": "0.0.0.0", "port": 8000})
    serve.run(app, route_prefix="/", blocking=True)
