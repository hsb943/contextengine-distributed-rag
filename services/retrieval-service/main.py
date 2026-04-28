from fastapi import FastAPI

app = FastAPI(title="Retrieval Service")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "retrieval-service"}
