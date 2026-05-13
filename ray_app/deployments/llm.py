import logging

from ray import serve

from pipelines.generation_pipeline import generate_answer

LOGGER = logging.getLogger(__name__)


@serve.deployment(num_replicas=1, max_ongoing_requests=5, ray_actor_options={"num_cpus": 0.25})
class LLMDeployment:
    async def generate(self, query: str, contexts: list):
        LOGGER.info("[LLM] Generation started.")
        result = generate_answer(query=query, contexts=contexts)
        LOGGER.info("[LLM] Generation finished.")
        return result
