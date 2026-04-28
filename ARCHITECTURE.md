# RAG System Architecture

## 🧠 Overview

This system is a **Retrieval-Augmented Generation (RAG) pipeline** designed to answer user queries using private or domain-specific documents.

It is built as a **modular, service-oriented architecture** where each component has a clear responsibility and can scale independently.

---

## 🎯 Core Goals

* Decouple ingestion, retrieval, and generation
* Enable independent scaling (CPU vs GPU workloads)
* Allow easy swapping of models (embeddings, reranker, LLM)
* Support future production features (autoscaling, multi-tenancy, connectors)

---

## 🧩 High-Level Architecture

```
User
 │
 ▼
API Gateway
 │
 ├── Query Flow ───────────────────────────────┐
 │                                            ▼
 │                                   Retrieval Service
 │                                            │
 │                                    Vector Database
 │                                            │
 │                                            ▼
 │                                      Reranker
 │                                            │
 │                                            ▼
 │                                       LLM Service
 │                                            │
 │                                            ▼
 │                                         Response
 │
 └── Ingestion Flow ──────────────────────────┐
                                              ▼
                                      Ingestion Service
                                              │
                              Parsing → Chunking → Embedding
                                              │
                                              ▼
                                       Vector Database
```

---

## 🔁 Core Flows

### 1. Query Flow (User → Answer)

1. User sends query via API Gateway
2. Query is forwarded to Retrieval Service
3. Query is embedded using embedding model
4. Vector DB returns top-K similar chunks
5. Reranker reorders results for relevance
6. Top chunks are sent to LLM Service
7. LLM generates final answer
8. Response returned to user

---

### 2. Ingestion Flow (Documents → Knowledge Base)

1. User uploads document (UI/API)
2. Ingestion Service processes document:

   * Parsing (PDF/DOCX → text)
   * Chunking (split into smaller units)
   * Embedding (text → vectors)
3. Chunks + metadata stored in Vector DB

---

## 🧠 System Components

---

### 🔌 API Gateway

**Responsibilities:**

* Entry point for all requests
* Routes `/query` and `/upload`
* Handles authentication (future)

---

### 📥 Ingestion Service (CPU-bound)

**Responsibilities:**

* Document parsing
* Chunking strategy
* Embedding generation
* Indexing into vector DB

**Notes:**

* Can be async / batch-based
* Scales horizontally on CPU nodes

---

### 🔍 Retrieval Service (CPU-bound)

**Responsibilities:**

* Query embedding
* Vector similarity search
* Metadata filtering
* Reranking

**Notes:**

* Critical for answer quality
* Should remain independent from LLM

---

### 🤖 LLM Service (GPU-bound)

**Responsibilities:**

* Prompt construction
* Context injection
* Answer generation

**Notes:**

* Uses vLLM or external API
* Main latency + cost driver
* Scales on GPU nodes

---

### 🗄️ Vector Database

**Options:**

* Qdrant (recommended)
* FAISS (local/dev)

**Stores:**

* embeddings
* metadata (source, page, timestamp)

---

## 🧠 Core Modules (Reusable Logic)

Located in `/core`

---

### ✂️ chunking/

* Fixed chunking
* Recursive chunking
* Semantic chunking (future)

---

### 🔗 embeddings/

* Embedding model wrappers
* Query vs document formatting

---

### 🧹 reranking/

* Cross-encoder rerankers
* Score normalization

---

### 🧾 prompts/

* Prompt templates
* System instructions
* Context formatting

---

## ⚙️ Infrastructure Layer

Located in `/infrastructure`

---

### 🗄️ vector-db/

* Qdrant client
* Index management
* CRUD operations

---

### ⚙️ config/

* Model configs
* Environment variables
* Feature flags

---

## 🧪 Scripts

Located in `/scripts`

* `ingest_batch.py` → bulk ingestion
* `reindex.py` → re-embedding / updates

---

## 🚀 Scaling Strategy (Future)

---

### Horizontal Scaling

| Component         | Scaling Type |
| ----------------- | ------------ |
| Ingestion Service | CPU scaling  |
| Retrieval Service | CPU scaling  |
| LLM Service       | GPU scaling  |

---

### Autoscaling (Kubernetes)

* HPA for ingestion/retrieval
* GPU autoscaling for LLM
* Queue-based scaling (Ray / Kafka optional)

---

## 🔥 Design Principles

1. **Separation of Concerns**

   * Ingestion ≠ Retrieval ≠ Generation

2. **Stateless Services**

   * Easier scaling and deployment

3. **Pluggable Models**

   * Swap embeddings/LLM without rewriting system

4. **Data-Centric Design**

   * Retrieval quality > model size

---

## ⚠️ Known Challenges

* Chunking strategy impacts retrieval quality
* Embedding choice affects recall
* Reranker adds latency but improves precision
* LLM cost dominates system cost

---

## 🧠 Future Enhancements

* Hybrid search (BM25 + dense)
* Multi-LLM routing
* Query classification
* Feedback loop / evaluation pipeline
* Connectors (Google Drive, Slack, etc.)
* Multi-tenant support

---

## 🧾 Summary

This system follows a **modular RAG architecture** where:

* Knowledge is stored externally (vector DB)
* Retrieval is optimized before generation
* LLM is used only for reasoning, not memory

> The intelligence of the system depends more on retrieval quality than model size.

---
