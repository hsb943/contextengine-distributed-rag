import logging

from ray import serve

from pipelines.ingestion_pipeline import ingest_document

LOGGER = logging.getLogger(__name__)


@serve.deployment(num_replicas=1, ray_actor_options={"num_cpus": 0})
class IngestionDeployment:
    async def ingest(self, text: str, document_id: str, metadata: dict | None = None):
        result = ingest_document(text=text, document_id=document_id, metadata=metadata)
        LOGGER.info("Ingestion chunks created: %d", result["chunks_created"])
        return result

