import json
import os
from urllib import error, request

DEFAULT_LLM_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
DEFAULT_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
SYSTEM_PROMPT = (
    "You are a helpful assistant. Answer the question using the provided "
    "context as your primary evidence. If the context contains the answer, "
    "give a direct answer even if the text is messy or OCR-like. If the answer "
    "is genuinely not supported by the context, say 'I don't know'. "
    "If the user asks for a list, syllabus, modules, topics, summary, or other "
    "structured output, combine evidence from multiple chunks and answer in "
    "clear bullet points or a compact structured format."
)


def generate_answer(query: str, context: str) -> str:
    """Generate an answer from an OpenAI-compatible chat completion API."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set.")

    payload = {
        "model": DEFAULT_LLM_MODEL,
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion: {query}",
            },
        ],
    }

    endpoint = f"{DEFAULT_BASE_URL.rstrip('/')}/chat/completions"
    body = json.dumps(payload).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    http_request = request.Request(endpoint, data=body, headers=headers, method="POST")

    try:
        with request.urlopen(http_request, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"LLM API request failed: {details}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"Unable to reach LLM API: {exc.reason}") from exc

    choices = result.get("choices", [])
    if not choices:
        raise RuntimeError("LLM API returned no choices.")

    message = choices[0].get("message", {})
    content = message.get("content")
    if not content:
        raise RuntimeError("LLM API returned an empty answer.")

    return content.strip()
