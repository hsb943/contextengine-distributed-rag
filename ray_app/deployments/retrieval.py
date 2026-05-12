import logging

from ray import serve

from pipelines.retrieval_pipeline import retrieve

LOGGER = logging.getLogger(__name__)


@serve.deployment(num_replicas=1, max_ongoing_requests=10, ray_actor_options={"num_cpus": 0})
class RetrievalDeployment:
    async def search(self, query: str, top_k: int = 50, filters: dict | None = None):
        LOGGER.info("Retrieval request received: %s", query)
        results = retrieve(query=query, top_k=top_k, filters=filters)
        LOGGER.info("Retrieval candidates returned: %d", len(results))
        return results
