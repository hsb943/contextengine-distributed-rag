# 🌐 Global RAG System Architecture

## 🧠 Overview

This system is a **Global Retrieval-Augmented Generation (RAG) platform** designed to support **continuous document ingestion** and **independent querying across the entire knowledge base**.

Unlike traditional "chat with document" systems, this architecture enables:

* Upload once → query anytime
* No dependency between ingestion and querying
* Organization-wide knowledge search (e.g., legal, finance, enterprise)

---

## 🎯 Core Goals

* Decouple ingestion and querying completely
* Support **global semantic search across all documents**
* Maintain high retrieval accuracy using reranking
* Enable scalable, production-ready architecture
* Allow optional filtering (not mandatory)

---

## 🧩 High-Level Architecture

```
                ┌─────────────────────┐
                │   Ingestion Flow    │
                └────────┬────────────┘
                         ▼
                Ingestion Service
                         │
         Parsing → Chunking → Embedding
                         │
                         ▼
                ┌─────────────────────┐
                │   Vector Database   │
                │     (Qdrant)        │
                └────────┬────────────┘
                         │
                         ▼
                ┌─────────────────────┐
                │   Retrieval Flow    │
                └────────┬────────────┘
                         ▼
                Retrieval Service
                         │
           High-Recall Vector Search
                         │
                         ▼
                     Reranker
                         │
                         ▼
                    LLM Service
                         │
                         ▼
                      Response
```

---

## 🔁 Core Flows

---

### 1. Query Flow (Global Search)

1. User sends query
2. Retrieval Service embeds query
3. Vector DB returns **top 30–50 candidate chunks**
4. Reranker selects **top 5–10 most relevant chunks**
5. LLM generates answer using selected context
6. Response returned with sources

> ⚠️ No document selection required

---

### 2. Ingestion Flow (Continuous Knowledge Update)

1. Documents are uploaded via API/UI

2. Ingestion Service processes:

   * Parsing (PDF/DOCX → text)
   * Chunking (semantic / paragraph-based)
   * Embedding (batched)

3. Chunks stored in Vector DB with metadata

---

## 🧠 System Components

---

### 🔌 API Gateway

**Responsibilities:**

* Entry point for all requests
* Routes:

  * `/ingest`
  * `/query`
* Handles auth (future)

---

### 📥 Ingestion Service (CPU-bound)

**Responsibilities:**

* Document parsing
* Smart chunking (semantic / structure-aware)
* Batch embedding
* Metadata enrichment
* Indexing into vector DB

**Notes:**

* Can run async / batch jobs
* Designed for continuous ingestion

---

### 🔍 Retrieval Service (CPU-bound)

**Responsibilities:**

* Query embedding
* High-recall vector search (top_k = 30–50)
* Optional metadata filtering
* Passing candidates to reranker

**Modes:**

```text
Global Mode (default) → search entire DB
Filtered Mode         → search within subset (optional)
```

---

### 🧹 Reranker (Critical Component)

**Responsibilities:**

* Re-rank retrieved candidates using cross-encoder
* Reduce noise from global search
* Output top 5–10 chunks

---

### 🤖 LLM Service (GPU / API)

**Responsibilities:**

* Prompt construction
* Context injection
* Answer generation

**Constraints:**

* Must answer only from retrieved context
* Must avoid hallucination

---

### 🗄️ Vector Database (Qdrant)

**Stores:**

* Embeddings
* Metadata payload
* Chunk text

---

## 🧾 Metadata Design (Important)

Each chunk should include:

```json
{
  "document_id": "...",
  "doc_type": "contract | case_law | policy",
  "jurisdiction": "india",
  "source": "pdf",
  "section": "optional",
  "created_at": "...",
  "text": "..."
}
```

---

## 🧠 Core Modules (Reusable)

Located in `/core`

---

### ✂️ chunking/

* Recursive chunking
* Paragraph-based splitting
* Overlap support

---

### 🔗 embeddings/

* Batch embedding
* Model abstraction
* Query vs document embedding handling

---

### 🧹 reranking/

* Cross-encoder models
* Score normalization
* Top-K reduction

---

### 🧾 prompts/

* Strict grounding prompts
* Context formatting
* Instruction templates

---

## ⚙️ Infrastructure Layer

Located in `/infrastructure`

---

### 🗄️ vector-db/

* Qdrant client
* Index management
* Search + filtering logic

---

### ⚙️ config/

* Model configs
* Feature flags (global vs filtered mode)
* Environment variables

---

## 🧪 Scripts

Located in `/scripts`

* `ingest_batch.py` → bulk ingestion
* `reindex.py` → re-embedding
* `evaluate.py` → retrieval + answer evaluation

---

## 🔍 Retrieval Strategy (Key Difference)

```text
1. Retrieve top 30–50 chunks (high recall)
2. Rerank results
3. Select top 5–10
4. Send to LLM
```

---

## ⚠️ Known Challenges

* Global search introduces noise
* Chunk quality directly impacts retrieval
* Reranker adds latency
* Large datasets require tuning

---

## 🚀 Future Enhancements

* Hybrid search (BM25 + vector)
* Query classification
* Domain-aware routing
* Feedback loops / evaluation pipeline
* Multi-tenant filtering (user_id)
* Streaming responses
* Caching layer

---

## 🔥 Design Principles

1. **Global-first Retrieval**

   * Query entire knowledge base by default

2. **Separation of Concerns**

   * Ingestion ≠ Retrieval ≠ Generation

3. **Data-Centric Design**

   * Retrieval quality > model size

4. **Pluggability**

   * Swap models without system rewrite

---

## 🧾 Summary

This system is a **global knowledge retrieval platform** where:

* Documents are continuously ingested
* Queries are independent of uploads
* Retrieval is optimized for recall + precision
* LLM is used for reasoning, not storage

> The intelligence of the system depends more on retrieval quality than model size.
