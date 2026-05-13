import logging

from ray import serve

from infrastructure.model_cache import ensure_huggingface_cache_ready
from infrastructure.vector_db.qdrant_client import initialize_qdrant
from pipelines.retrieval_pipeline import retrieve

LOGGER = logging.getLogger(__name__)


@serve.deployment(num_replicas=1, max_ongoing_requests=10, ray_actor_options={"num_cpus": 0.25})
class RetrievalDeployment:
    def __init__(self):
        LOGGER.info("[RAY STARTUP] Validating shared model cache")
        ensure_huggingface_cache_ready()
        LOGGER.info("[RAY STARTUP] RetrievalDeployment initializing Qdrant")
        initialize_qdrant()

    async def search(self, query: str, top_k: int = 50, filters: dict | None = None):
        LOGGER.info("[RETRIEVAL] Request received: %s", query)
        results = retrieve(query=query, top_k=top_k, filters=filters)
        LOGGER.info("[RETRIEVAL] Candidates returned: %d", len(results))
        return results
