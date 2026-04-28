# ContextEngine

ContextEngine is a modular Retrieval-Augmented Generation (RAG) system skeleton.
It separates API routing, ingestion, retrieval, generation, reusable core logic,
and infrastructure concerns.

## Run the API Gateway

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the API Gateway:

```bash
cd services/api-gateway
uvicorn main:app --reload
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```
