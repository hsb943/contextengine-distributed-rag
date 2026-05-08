import json
import os
from urllib import error, request

DEFAULT_LLM_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
DEFAULT_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")


def call_llm(prompt: str) -> str:
    """Call an OpenAI-compatible chat completion endpoint."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set.")

    payload = {
        "model": DEFAULT_LLM_MODEL,
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
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

