# TheSuperRAG

TheSuperRAG is a blazing-fast, serverless, and Self-Healing Retrieval-Augmented Generation (RAG) backend with hybrid search, cross-encoder re-ranking, exact citations, and local browser-based document storage. 

It provides an advanced AI document chat interface using **Next.js**, **FastAPI**, **LangGraph**, and **Qdrant**. The UI is built with a striking animated Bauhaus aesthetic using **Framer Motion**.

## 🚀 Key Architectural Upgrades

- **Zero-Storage Privacy (Stateless):** Your files never touch the server disk. Documents are stored locally in your browser's IndexedDB and processed exclusively in-memory on the backend.
- **PyTorch-Free Performance (FastEmbed):** We completely removed PyTorch and heavy machine learning dependencies. The backend uses `FastEmbed` to run both the dense embedding model and the cross-encoder via ONNX runtime, saving >300MB of RAM and booting 5x faster.
- **BYOK (Bring Your Own Key):** Users can enter their own API keys (Groq, OpenAI, Anthropic, Gemini) from the frontend. The server is completely unauthenticated and API-agnostic.
- **Self-Healing RAG:** Leverages LangGraph to continuously validate retrieved context. If the AI doesn't find the answer, it rewrites its own query and searches again.
- **Framer Motion UI:** The landing page and chat interfaces feature high-end micro-animations and responsive aesthetics.

## Features

- **Hybrid Search & Re-ranking:** Combines dense (Vector) and sparse (BM25) embeddings for exact keyword matches and semantic meaning, re-ranked with a Cross-Encoder.
- **Agentic Query Decomposition:** Automatically breaks down complex multi-hop questions into parallel sub-queries.
- **Live Tool Streaming UI:** Visualizes background tool execution and query decomposition in real-time in the frontend via SSE.
- **YouTube & Web Indexing (Local):** Paste YouTube URLs to instantly transcribe and ingest them into the knowledge base (Requires running locally due to Cloud IP bans).
- **Streaming Citations:** Streams back text responses while providing interactive references and source snippets.

## Architecture

```mermaid
graph TD
    A[User Browser (Next.js)] -->|Files stored in IndexedDB| B
    B[User Request] --> C[FastAPI Server]
    C -->|Stateless In-Memory Qdrant| D[FastEmbed ONNX Embeddings]
    D --> E{LangGraph Agent Router}
    E -->|Self-Correction| E
    E --> F[Cross-Encoder Reranker]
    F --> G[LLM Generation (Groq/OpenAI)]
    G -->|Streaming SSE| A
```

## Project Structure

- `server.py`: FastAPI server handling document upload, management, and SSE streaming chat endpoints.
- `frontend/`: Next.js frontend application with Framer Motion animations.
- `ingest.py`: Handles vector database in-memory storage (Qdrant) and FastEmbed dense models.
- `reranker.py`: FastEmbed TextCrossEncoder logic.
- `graph.py`: LangGraph setup for self-healing RAG logic.
- `database.py`: SQLAlchemy setup to track chat sessions.

## Deployment (Production Ready)

The simplest and most robust way to run TheSuperRAG in a production environment is using Docker Compose.

### Requirements
- Docker
- Docker Compose

### 1. Configure Environment Variables
Create a `.env` file in the root directory and add your API keys:
```bash
GROQ_API_KEY=your_groq_api_key
```

### 2. Run with Docker Compose
To build and start both the backend and frontend in production mode, simply run:
```bash
docker-compose up -d --build
```

- **Backend API**: `http://localhost:8000/docs`
- **Frontend App**: `http://localhost:3000`

## Running Locally (Development Mode)

1. Clone the repository:
   ```bash
   git clone https://github.com/tanushbhootra576/TheSuperRAG.git
   cd TheSuperRAG
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # On Windows
   .\venv\Scripts\activate
   # On Linux/macOS
   source venv/bin/activate
   ```

3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Start the FastAPI Backend
```bash
uvicorn server:app --reload --host 127.0.0.1 --port 8000
```

5. Start the Frontend (Next.js)
```bash
cd frontend
npm install
npm run dev
```

## Citation
If you use this software, please cite it using the included `CITATION.cff` file.

## License
This project is licensed under the MIT License.
