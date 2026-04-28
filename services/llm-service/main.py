from fastapi import FastAPI

app = FastAPI(title="LLM Service")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "llm-service"}
