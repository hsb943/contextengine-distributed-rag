import logging

from ray import serve

from infrastructure.model_cache import ensure_huggingface_cache_ready
from pipelines.ingestion_pipeline import ingest_document

LOGGER = logging.getLogger(__name__)


@serve.deployment(num_replicas=1, ray_actor_options={"num_cpus": 0.25})
class IngestionDeployment:
    def __init__(self):
        LOGGER.info("[RAY STARTUP] Validating shared model cache")
        ensure_huggingface_cache_ready()

    async def ingest(self, text: str, document_id: str, metadata: dict | None = None):
        LOGGER.info("[INGESTION] Request received for document_id=%s", document_id)
        result = ingest_document(text=text, document_id=document_id, metadata=metadata)
        LOGGER.info("[INGESTION] Chunks created: %d", result["chunks_created"])
        return result

