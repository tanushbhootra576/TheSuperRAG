"""
server.py -- FastAPI Backend for TheSuperRAG.

New endpoints vs v1:
  POST   /init              -- initialise DocumentStore + RAGGraph + AutoIndexer
  POST   /chat              -- streaming SSE chat (now includes citations & confidence)
  GET    /status            -- system status + indexed document list
  GET    /documents         -- list all indexed documents
  POST   /upload            -- drag-and-drop PDF upload + immediate indexing
  DELETE /documents/{file}  -- remove a document from the index and disk
  GET    /events            -- SSE stream for auto-indexing notifications

Security note: allow_origins is restricted to localhost:3000.
               Change to your production domain before deploying.
"""
import os
os.environ.setdefault("PYTHONUTF8", "1")  # Force UTF-8 stdout on Windows

import asyncio
import json
import shutil
import threading
import threading
from typing import List, Optional
import uuid

from fastapi import FastAPI, File, HTTPException, UploadFile, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import SessionLocal, ChatSession, ChatMessage
from graph import RAGGraph
from ingest import DocumentStore

# ── Constants ─────────────────────────────────────────────────────────────────
DATA_FOLDER = "DATA"
COLLECTION_NAME = "super_rag"

# ── App Setup ─────────────────────────────────────────────────────────────────
app = FastAPI(
    title="TheSuperRAG API",
    description=(
        "Self-Healing RAG backend with hybrid search, re-ranking, "
        "citations, confidence scoring, and live document management."
    ),
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Global State ──────────────────────────────────────────────────────────────
doc_store: DocumentStore = None
rag_system: RAGGraph = None
initialized: bool = False
_init_error: str = None
_init_in_progress: bool = False
_init_lock = threading.Lock()

# SSE queue for push notifications (auto-indexing events)
_event_queue: asyncio.Queue = asyncio.Queue(maxsize=100)

# ── DB Dependency ─────────────────────────────────────────────────────────────
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ── Request / Response Models ─────────────────────────────────────────────────
class ChatRequest(BaseModel):
    query: str
    history: List[dict] = []
    selected_documents: List[str] = []   # [] = search all indexed docs
    session_id: Optional[str] = None     # For persistent chat
    llm_model: str = "llama-3.1-8b-instant"
    temperature: float = 0.0
    use_cross_encoder: bool = True


# ── Lifecycle ─────────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    os.makedirs(DATA_FOLDER, exist_ok=True)


@app.on_event("shutdown")
async def shutdown_event():
    pass

# ── Helper ────────────────────────────────────────────────────────────────────
import datetime

def save_chat_to_db(session_id: str, query: str, response: str, docs: list, confidence: dict):
    if not session_id:
        return
    try:
        db = SessionLocal()
        # Ensure session exists
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            session = ChatSession(id=session_id, title=query[:40] + ("..." if len(query)>40 else ""))
            db.add(session)
        elif session.title == "New Chat":
            session.title = query[:40] + ("..." if len(query)>40 else "")
        session.updated_at = datetime.datetime.utcnow()

        user_msg = ChatMessage(session_id=session_id, role="user", content=query)
        asst_msg = ChatMessage(
            session_id=session_id, role="assistant", content=response,
            docs=docs, confidence=confidence
        )
        db.add(user_msg)
        db.add(asst_msg)
        db.commit()
        db.close()
    except Exception as e:
        print("Failed to save chat to DB:", e)

def _push_event(event: dict):
    """Thread-safe push to the SSE queue from watchdog threads."""
    try:
        loop = asyncio.get_event_loop()
        loop.call_soon_threadsafe(_event_queue.put_nowait, event)
    except Exception:
        pass


def _do_init():
    """Heavy init work — runs in a thread pool so the event loop stays free."""
    global doc_store, rag_system, initialized, _init_error, _init_in_progress
    with _init_lock:
        if initialized:
            return
        _init_in_progress = True
        _init_error = None
        try:
            ds = DocumentStore(folder_path=DATA_FOLDER, collection_name=COLLECTION_NAME)
            rg = RAGGraph(doc_store=ds)
            doc_store = ds
            rag_system = rg
            initialized = True
        except Exception as e:
            _init_error = str(e)
            import traceback; traceback.print_exc()
        finally:
            _init_in_progress = False

        # If we successfully initialized, trigger the auto-index of existing PDFs
        # while yielding progress events to the SSE stream so the UI can toast them.
        if initialized and doc_store:
            try:
                doc_store._auto_index_folder(on_progress=_push_event)
            except Exception as e:
                import traceback; traceback.print_exc()


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/sessions")
def get_sessions(db: Session = Depends(get_db)):
    """List all chat sessions."""
    sessions = db.query(ChatSession).order_by(ChatSession.updated_at.desc()).all()
    return {"sessions": [{"id": s.id, "title": s.title, "updated_at": s.updated_at} for s in sessions]}

@app.post("/sessions")
def create_session(db: Session = Depends(get_db)):
    """Create a new chat session."""
    session_id = str(uuid.uuid4())
    db_session = ChatSession(id=session_id, title="New Chat")
    db.add(db_session)
    db.commit()
    return {"id": session_id, "title": "New Chat"}

@app.get("/sessions/{session_id}/messages")
async def get_session_messages(session_id: str, db: Session = Depends(get_db)):
    messages = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).all()
    return {"messages": [
        {
            "role": m.role,
            "content": m.content,
            "confidence": m.confidence,
            "docs": m.docs
        }
        for m in messages
    ]}

@app.get("/graph")
async def get_knowledge_graph(db: Session = Depends(get_db)):
    from database import GraphNode, GraphEdge
    nodes = db.query(GraphNode).all()
    edges = db.query(GraphEdge).all()

    # Format for react-force-graph
    out_nodes = [{"id": n.id, "label": n.label, "group": n.label} for n in nodes]
    valid_node_ids = {n.id for n in nodes}

    # The LLM sometimes hallucinates edges to nodes it didn't explicitly extract.
    # react-force-graph crashes if an edge targets a non-existent node.
    for e in edges:
        if e.source not in valid_node_ids:
            out_nodes.append({"id": e.source, "label": "UNKNOWN", "group": "UNKNOWN"})
            valid_node_ids.add(e.source)
        if e.target not in valid_node_ids:
            out_nodes.append({"id": e.target, "label": "UNKNOWN", "group": "UNKNOWN"})
            valid_node_ids.add(e.target)

    return {
        "nodes": out_nodes,
        "links": [{"source": e.source, "target": e.target, "label": e.relation} for e in edges]
    }

# ── RAG / Chat ────────────────────────────────────────────────────────────────   

@app.delete("/sessions/{session_id}")
def delete_session(session_id: str, db: Session = Depends(get_db)):
    db_session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if db_session:
        db.delete(db_session)
        db.commit()
    return {"status": "success"}

from pydantic import BaseModel
class SessionUpdate(BaseModel):
    title: str

@app.put("/sessions/{session_id}")
def update_session(session_id: str, payload: SessionUpdate, db: Session = Depends(get_db)):
    db_session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if db_session:
        db_session.title = payload.title
        db.commit()
        return {"status": "success", "title": db_session.title}
    return {"status": "not_found"}

@app.post("/init")
async def initialize_system():
    """
    Kick off the initialisation in a background thread and return immediately.
    Poll GET /status to check progress.
    """
    global _init_in_progress

    if initialized:
        return {
            "status": "success",
            "message": "System already initialised.",
            "documents": doc_store.get_indexed_files(),
            "hybrid_search": doc_store.hybrid_enabled,
        }

    if _init_in_progress:
        return {"status": "pending", "message": "Initialisation already in progress..."}

    # Run in background thread — returns immediately to the browser
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, _do_init)

    return {"status": "pending", "message": "Initialisation started. Poll /status for progress."}


@app.post("/chat")
async def chat_stream(request: ChatRequest):
    """
    Streaming SSE chat endpoint.

    Event types emitted:
      {"type": "status",  "message": str, "event"?: "heal"}
      {"type": "final",   "message": str, "docs": [...], "confidence": {...}}
      [DONE]
    """
    global rag_system, initialized

    if not initialized or not rag_system:
        raise HTTPException(
            status_code=503,
            detail="System not initialised. Call POST /init first.",
        )

    async def event_generator():
        inputs = {
            "chat_history": request.history,
            "user_query": request.query,
            "current_search_query": request.query,
            "retrieved_context": "",
            "retrieved_docs": [],
            "generation": "",
            "confidence": {},
            "loop_count": 0,
            "logs": [],
            "selected_documents": request.selected_documents,
            "llm_model": request.llm_model,
            "temperature": request.temperature,
            "use_cross_encoder": request.use_cross_encoder,
        }

        final = {
            "generation": "",
            "retrieved_docs": [],
            "confidence": {},
        }
        current_query = request.query

        # We use astream_events to stream tokens and node transitions
        async for event in rag_system.app.astream_events(inputs, version="v2"):
            kind = event["event"]
            
            # Identify which node or component is emitting
            node_name = event.get("metadata", {}).get("langgraph_node", "")
            
            # Stream tokens during generation
            if kind == "on_chat_model_stream" and node_name == "generate":
                chunk_text = event["data"]["chunk"].content
                if chunk_text:
                    yield _sse({"type": "token", "content": chunk_text})

            # Handle node completion to grab final state updates
            elif kind == "on_chain_end" and node_name in ["smart_router", "retrieve", "generate", "rewrite_query"]:
                node_output = event["data"].get("output", {})
                if not isinstance(node_output, dict):
                    continue
                
                if node_name == "smart_router":
                    gen = node_output.get("generation", "")
                    if gen.lower() != "proceed":
                        yield _sse({
                            "type": "final",
                            "message": gen,
                            "docs": [],
                            "confidence": {},
                        })
                        save_chat_to_db(request.session_id, request.query, gen, [], {})
                        yield "data: [DONE]\n\n"
                        return

                elif node_name == "retrieve":
                    final["retrieved_docs"] = node_output.get("retrieved_docs", [])
                    final["confidence"] = node_output.get("confidence", {})
                    hybrid_label = "Hybrid" if doc_store.hybrid_enabled else "Dense"
                    yield _sse({
                        "type": "status",
                        "message": f" {hybrid_label} search + re-ranking: \"{current_query}\"",
                    })

                elif node_name == "generate":
                    final["generation"] = node_output.get("generation", "")
                    # Token streaming happens via 'on_chat_model_stream', but we keep the full generation for saving

                elif node_name == "rewrite_query":
                    current_query = node_output.get("current_search_query", current_query)
                    yield _sse({
                        "type": "status",
                        "message": f" Self-Heal #{inputs.get('loop_count', 1)}: Rewrote query -> \"{current_query}\"",
                        "event": "heal",
                    })

            elif kind == "on_chain_start" and node_name == "smart_router":
                yield _sse({"type": "status", "message": " Contextualising query with conversation history..."})
            elif kind == "on_chain_start" and node_name == "generate":
                yield _sse({"type": "status", "message": " Drafting answer with source citations..."})

        # Graceful fallback for exhausted self-healing
        if "information missing" in final["generation"].lower():
            final["generation"] = (
                "I apologise -- after exhaustive multi-tier self-healing operations "
                "across the available document collection, no verifiable answer could "
                "be found for your query. Please verify that the relevant document has "
                "been uploaded and indexed."
            )

        yield _sse({
            "type": "final",
            "message": final["generation"],
            "docs": final["retrieved_docs"],
            "confidence": final["confidence"],
        })
        save_chat_to_db(request.session_id, request.query, final["generation"], final["retrieved_docs"], final["confidence"])
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/documents")
async def list_documents():
    """Return a list of all currently indexed document filenames."""
    if not doc_store:
        return {"documents": []}
    return {"documents": doc_store.get_indexed_files()}


@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a PDF file and index it immediately.
    If the system is not yet initialised, the file is saved and will be
    indexed automatically on the next /init call.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    save_path = os.path.join(DATA_FOLDER, file.filename)
    os.makedirs(DATA_FOLDER, exist_ok=True)

    # Stream the upload to disk
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    if doc_store:
        chunks = doc_store.index_file(save_path, file.filename)
        # Notify SSE listeners
        _push_event({
            "type": "document_indexed",
            "file": file.filename,
            "chunks": chunks,
        })
        return {
            "status": "success",
            "file": file.filename,
            "chunks_indexed": chunks,
            "message": f"Indexed {chunks} chunks from '{file.filename}'.",
        }

    return {
        "status": "saved",
        "file": file.filename,
        "message": "File saved. Will be indexed on next /init call.",
    }


@app.delete("/documents/{filename}")
async def delete_document(filename: str):
    """
    Remove a document from the vector index and delete it from disk.
    """
    if not doc_store:
        raise HTTPException(status_code=503, detail="System not initialised.")

    # Remove from vector store
    success = doc_store.delete_file(filename)
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"'{filename}' was not found in the index.",
        )

    # Remove from disk (best-effort)
    disk_path = os.path.join(DATA_FOLDER, filename)
    if os.path.exists(disk_path):
        os.remove(disk_path)

    return {
        "status": "success",
        "message": f"'{filename}' has been removed from the index and disk.",
    }


@app.get("/status")
async def get_status():
    """Health-check endpoint -- returns initialisation state and document list."""
    return {
        "initialized": initialized,
        "init_in_progress": _init_in_progress,
        "init_error": _init_error,
        "hybrid_search": doc_store.hybrid_enabled if doc_store else False,
        "documents": doc_store.get_indexed_files() if doc_store else [],
    }


@app.get("/events")
async def sse_events():
    """
    Server-Sent Events stream for real-time notifications.

    Pushes:
      {"type": "document_indexed", "file": str, "chunks": int}
      {"type": "ping"}   -- keepalive every 25s
    """
    async def generator():
        while True:
            try:
                event = await asyncio.wait_for(_event_queue.get(), timeout=25)
                yield f"data: {json.dumps(event)}\n\n"
            except asyncio.TimeoutError:
                yield 'data: {"type":"ping"}\n\n'

    return StreamingResponse(generator(), media_type="text/event-stream")


# ── Utility ───────────────────────────────────────────────────────────────────
def _sse(payload: dict) -> str:
    """Format a dict as an SSE data line."""
    return f"data: {json.dumps(payload)}\n\n"
