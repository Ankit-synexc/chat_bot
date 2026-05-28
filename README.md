# doc_qa_system

> Intelligent, lightweight, and fully asynchronous Document Q&A Platform powered by RAG.

![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109%2B-009688.svg?logo=fastapi&logoColor=white)
![MongoDB](https://img.shields.io/badge/MongoDB_Atlas-Vector_Search-47A248.svg?logo=mongodb&logoColor=white)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## 🎯 Problem Statement
In 2026, organizations process thousands of complex documents daily, making accurate information retrieval a critical bottleneck. Standard enterprise search mechanisms fall short of understanding context, while naively querying Large Language Models (LLMs) leads to hallucinations, data exposure, and massive API costs. **doc_qa_system** solves this by implementing an ultra-efficient Retrieval-Augmented Generation (RAG) pipeline. By combining robust hybrid search (Vector + BM25) and local embedding models with high-speed LLM generation, it provides hyper-accurate, hallucination-free answers tied directly to source citations—all while running cleanly on free-tier cloud infrastructure.

## 🏗️ Architecture

![Architecture](docs/architecture.png)
*(Architecture flows: Upload PDF → LangChain Chunker → Local Embeddings (all-MiniLM-L6) → MongoDB Atlas Vector Store. Query → Hybrid Search (Vector + BM25) → Cross-Encoder Rerank → Groq Llama-3 LLM → SSE Stream back to client.)*

## ✨ Features
* **Hybrid Search Retrieval:** Merges exact-match lexical queries (BM25) and semantic vector search using Reciprocal Rank Fusion (RRF).
* **Cross-Encoder Reranking:** Re-scores the top retrieved chunks locally before LLM injection to maximize context relevance and accuracy.
* **Server-Sent Events (SSE) Streaming:** Generates LLM responses token-by-token for ultra-low perceived latency.
* **Cost-Efficient Local ML:** Uses `sentence-transformers` for embeddings and reranking locally, eliminating recurring embedding API costs.
* **Asynchronous Core:** Non-blocking FastAPI + Motor architecture ensures high concurrency without the overhead.
* **Built-in Rate Limiting:** In-memory, sliding-window rate limiting (20 requests / 60 seconds) per API key—no Redis required.
* **Smart Query Caching:** SHA-256 hashed query caching to instantly serve repeated questions and bypass the LLM entirely.

## 💻 Tech Stack

| Layer | Technology | Why? |
| --- | --- | --- |
| **Web Framework** | FastAPI (Async) | High performance, native Pydantic validation, async standard for IO-bound workloads. |
| **Database & Vector Store** | MongoDB Atlas + Motor | Unified NoSQL document store with native HNSW vector indexing. |
| **Embedding Model** | `all-MiniLM-L6-v2` | Fast, lightweight (384 dims), CPU-friendly local embeddings. |
| **Lexical Search** | `rank_bm25` | Ensures exact keyword matches (names, acronyms) aren't lost in dense vector space. |
| **Reranker** | `ms-marco-MiniLM-L-6-v2` | Significantly boosts retrieval accuracy by intelligently scoring query-document pairs. |
| **LLM Generation** | Groq API (`llama3-8b-8192`) | Blistering fast token generation speed with a generous free tier. |

## 📁 Project Structure

```text
doc_qa_system/
├── controllers/       # Request handlers bridging HTTP routers and internal services
├── ml_core/           # ML models: embedder, reranker, chunker, pdf_parser, LLM client
├── models/            # Pydantic v2 schemas for requests, responses, and DB documents
├── routers/           # FastAPI APIRouter endpoint definitions
├── services/          # Core business logic: DB ops, hybrid search algorithm, auth logic
├── utils/             # Shared helpers: rate limiting, text cleaning, file validation
├── config/            # Environment settings and MongoDB connection lifecycle
├── main.py            # FastAPI application entrypoint and lifespan hooks
└── requirements.txt   # Project dependencies
```

## 🚀 Quick Start (Local)

### Prerequisites
* Python 3.10+
* MongoDB Atlas Cluster (Free Tier M0 is fine)
* Groq API Key

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/doc_qa_system.git
   cd doc_qa_system
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment:**
   Create a `.env` file in the root directory:
   ```env
   MONGO_URI=mongodb+srv://<user>:<password>@cluster0.mongodb.net/?retryWrites=true&w=majority
   DB_NAME=doc_qa_db
   CHUNKS_COLLECTION=chunks
   HISTORY_COLLECTION=chat_history
   USERS_COLLECTION=users

   GROQ_API_KEY=gsk_your_groq_api_key_here
   GROQ_MODEL=llama3-8b-8192

   APP_NAME="doc_qa_system"
   VERSION="1.0.0"
   DEBUG=True
   ```

4. **Run the server:**
   ```bash
   uvicorn main:app --reload
   ```

5. **Generate an API Key:**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/auth/keys" \
        -H "Content-Type: application/json" \
        -d '{"name": "Local Dev Key", "description": "Key for local testing"}'
   ```
   *(Save the returned `key` as it is strictly shown only once!)*

## 📖 API Documentation

### 1. Create API Key
* **Method & Path:** `POST /api/v1/auth/keys`
* **Auth Required:** No
* **Request:**
  ```json
  {
    "name": "Production Key",
    "description": "Primary key for backend services"
  }
  ```
* **Response:**
  ```json
  {
    "key": "aBcD_eFgH...",
    "name": "Production Key",
    "created_at": "2026-05-28T10:00:00Z",
    "is_active": true
  }
  ```
* **cURL:**
  ```bash
  curl -X POST "http://localhost:8000/api/v1/auth/keys" \
       -H "Content-Type: application/json" \
       -d '{"name": "Production Key"}'
  ```

### 2. Upload Document
* **Method & Path:** `POST /api/v1/documents/upload`
* **Auth Required:** Yes
* **Request:** `multipart/form-data` (file: .pdf or .txt)
* **Response:**
  ```json
  {
    "document_id": "550e8400-e29b-41d4-a716-446655440000",
    "source_file": "annual_report.pdf",
    "total_chunks": 42,
    "uploaded_at": "2026-05-28T10:05:00Z"
  }
  ```
* **cURL:**
  ```bash
  curl -X POST "http://localhost:8000/api/v1/documents/upload" \
       -H "X-API-Key: YOUR_API_KEY" \
       -F "file=@/path/to/annual_report.pdf"
  ```

### 3. Ask Question (Standard)
* **Method & Path:** `POST /api/v1/query/ask`
* **Auth Required:** Yes
* **Request:**
  ```json
  {
    "question": "What was the Q3 revenue?",
    "top_k": 5,
    "stream": false
  }
  ```
* **Response:**
  ```json
  {
    "answer": "The Q3 revenue was $4.2 million.",
    "sources": [
      {
        "text": "...Q3 revenue hit a record $4.2 million...",
        "source_file": "annual_report.pdf",
        "page_number": 12,
        "chunk_index": 24,
        "score": 0.89
      }
    ],
    "latency_ms": 845,
    "cached": false,
    "model_used": "llama3-8b-8192"
  }
  ```
* **cURL:**
  ```bash
  curl -X POST "http://localhost:8000/api/v1/query/ask" \
       -H "X-API-Key: YOUR_API_KEY" \
       -H "Content-Type: application/json" \
       -d '{"question": "What was the Q3 revenue?"}'
  ```

### 4. Ask Question (Streaming SSE)
* **Method & Path:** `POST /api/v1/query/ask/stream`
* **Auth Required:** Yes
* **Request:**
  ```json
  {
    "question": "Summarize the key risks.",
    "stream": true
  }
  ```
* **Response:** `text/event-stream`
  ```text
  data: {"delta": "The ", "done": false}

  data: {"delta": "key ", "done": false}

  data: {"delta": "risks...", "done": false}

  data: {"delta": "", "done": true}
  ```
* **cURL:**
  ```bash
  curl -N -X POST "http://localhost:8000/api/v1/query/ask/stream" \
       -H "X-API-Key: YOUR_API_KEY" \
       -H "Content-Type: application/json" \
       -d '{"question": "Summarize the key risks.", "stream": true}'
  ```

### 5. Get History
* **Method & Path:** `GET /api/v1/history`
* **Auth Required:** Yes
* **Query Params:** `?page=1&page_size=10`
* **cURL:**
  ```bash
  curl -X GET "http://localhost:8000/api/v1/history?page=1&page_size=10" \
       -H "X-API-Key: YOUR_API_KEY"
  ```

## ☁️ Deployment Guide (Render Free Tier)

1. **MongoDB Atlas Setup:**
   - Create a free M0 cluster on MongoDB Atlas.
   - Go to Network Access and whitelist IP `0.0.0.0/0`.
   - Go to **Atlas Search** and create a **Vector Search Index** on the `chunks` collection using the exact JSON editor configuration below:
     ```json
     {
       "fields": [
         {
           "numDimensions": 384,
           "path": "embedding",
           "similarity": "cosine",
           "type": "vector"
         }
       ]
     }
     ```
     *Ensure the index name is saved exactly as `vector_index`.*

2. **Render Setup:**
   - Connect your GitHub repository to a new Render **Web Service**.
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Environment Variables:** Add all variables from your `.env` file (`MONGO_URI`, `GROQ_API_KEY`, etc.).
   - Deploy! Your live URL will look like: `https://doc-qa-system.onrender.com`.

## 🧪 Running Tests

*(Tests are integrated using Pytest)*

```bash
pytest tests/ -v
```
**Coverage:** Unit tests cover text chunking heuristics, document boundary validation, sliding window rate limiter logic, and the SHA-256 query hashing cache.

## 🎥 Demo

*Watch the system process a 100-page PDF and answer questions accurately with sources in < 1 second.*
![Demo Video](https://www.youtube.com/watch?v=placeholder)
*(Placeholder for Demo Video)*

## 📝 Blog Post

Read the full technical deep dive on how I built this on [Dev.to](https://dev.to/placeholder).

## 🤝 Contributing
Contributions are always welcome! Please open an issue first to discuss what you would like to change before submitting a PR.

## 📄 License
This project is licensed under the MIT License - see the LICENSE file for details.
