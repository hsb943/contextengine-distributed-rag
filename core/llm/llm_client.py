from core.prompts import build_prompt
from infrastructure.llm_client import DEFAULT_LLM_MODEL, call_llm


def generate_answer(query: str, context: str, prompt: str | None = None) -> str:
    """Generate an answer from a prompt and context."""
    final_prompt = prompt or build_prompt(query, context)
    return call_llm(final_prompt)
