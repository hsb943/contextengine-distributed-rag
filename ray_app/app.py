from ray import serve

from ray_app.deployments.api import APIDeployment
from ray_app.deployments.ingestion import IngestionDeployment
from ray_app.deployments.llm import LLMDeployment
from ray_app.deployments.retrieval import RetrievalDeployment


if __name__ == "__main__":
    serve.start(http_options={"host": "0.0.0.0", "port": 8000})

    retrieval = RetrievalDeployment.bind()
    llm = LLMDeployment.bind()
    ingestion = IngestionDeployment.bind()

    app = APIDeployment.bind(retrieval, llm, ingestion)
    serve.run(app, route_prefix="/", blocking=True)
