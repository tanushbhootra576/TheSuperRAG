import os
os.environ.setdefault("PYTHONUTF8", "1")

import json
import shutil
import uuid
import datetime
from typing import List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, HTTPException, UploadFile, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import SessionLocal, ChatSession, ChatMessage
from graph import RAGGraph
from ingest import DocumentStore

DATA_FOLDER = "DATA"
COLLECTION_NAME = "super_rag"

@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(DATA_FOLDER, exist_ok=True)
    app.state.doc_store = DocumentStore(folder_path=DATA_FOLDER, collection_name=COLLECTION_NAME)
    app.state.rag_system = RAGGraph(doc_store=app.state.doc_store)
    app.state.doc_store._auto_index_folder()
    yield

app = FastAPI(
    title="TheSuperRAG API",
    description="Self-Healing RAG backend.",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class ChatRequest(BaseModel):
    query: str
    history: List[dict] = []
    selected_documents: List[str] = []
    session_id: Optional[str] = None
    llm_model: str = "llama-3.1-8b-instant"
    temperature: float = 0.0
    use_cross_encoder: bool = True

class SessionUpdate(BaseModel):
    title: str

def save_chat_to_db(session_id: str, query: str, response: str, docs: list, confidence: dict):
    if not session_id: return
    try:
        db = SessionLocal()
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            session = ChatSession(id=session_id, title=query[:40])
            db.add(session)
        elif session.title == "New Chat":
            session.title = query[:40]
        session.updated_at = datetime.datetime.utcnow()
        db.add(ChatMessage(session_id=session_id, role="user", content=query))
        db.add(ChatMessage(session_id=session_id, role="assistant", content=response, docs=docs, confidence=confidence))
        db.commit()
    except Exception as e:
        print("Failed to save chat:", e)
    finally:
        db.close()

def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload)}\n\n"

@app.get("/sessions")
def get_sessions(db: Session = Depends(get_db)):
    sessions = db.query(ChatSession).order_by(ChatSession.updated_at.desc()).all()
    return {"sessions": [{"id": s.id, "title": s.title, "updated_at": s.updated_at} for s in sessions]}

@app.post("/sessions")
def create_session(db: Session = Depends(get_db)):
    session_id = str(uuid.uuid4())
    db.add(ChatSession(id=session_id, title="New Chat"))
    db.commit()
    return {"id": session_id, "title": "New Chat"}

@app.get("/sessions/{session_id}/messages")
async def get_session_messages(session_id: str, db: Session = Depends(get_db)):
    messages = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).all()
    return {"messages": [{"role": m.role, "content": m.content, "confidence": m.confidence, "docs": m.docs} for m in messages]}

@app.delete("/sessions/{session_id}")
def delete_session(session_id: str, db: Session = Depends(get_db)):
    db_session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if db_session:
        db.delete(db_session)
        db.commit()
    return {"status": "success"}

@app.put("/sessions/{session_id}")
def update_session(session_id: str, payload: SessionUpdate, db: Session = Depends(get_db)):
    db_session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if db_session:
        db_session.title = payload.title
        db.commit()
        return {"status": "success", "title": db_session.title}
    return {"status": "not_found"}

@app.post("/chat")
async def chat_stream(request: ChatRequest):
    rag_system = app.state.rag_system
    async def event_generator():
        inputs = {
            "chat_history": request.history,
            "user_query": request.query,
            "current_search_query": request.query,
            "temperature": request.temperature
        }
        final = {"generation": "", "retrieved_docs": [], "confidence": {}}
        current_query = request.query

        async for event in rag_system.app.astream_events(inputs, version="v2"):
            kind, node_name = event["event"], event.get("metadata", {}).get("langgraph_node", "")
            if kind == "on_chat_model_stream" and node_name == "generate":
                chunk_text = event["data"]["chunk"].content
                if chunk_text: yield _sse({"type": "token", "content": chunk_text})
            elif kind == "on_chain_end" and node_name in ["smart_router", "retrieve", "generate", "rewrite_query"]:
                node_output = event["data"].get("output", {})
                if not isinstance(node_output, dict): continue
                if node_name == "smart_router":
                    gen = node_output.get("generation", "")
                    if gen.lower() != "proceed":
                        yield _sse({"type": "final", "message": gen, "docs": [], "confidence": {}})
                        save_chat_to_db(request.session_id, request.query, gen, [], {})
                        yield "data: [DONE]\n\n"
                        return
                elif node_name == "retrieve":
                    final["retrieved_docs"] = node_output.get("retrieved_docs", [])
                    final["confidence"] = node_output.get("confidence", {})
                    yield _sse({"type": "status", "message": f" Hybrid search + re-ranking: \"{current_query}\""})
                elif node_name == "generate":
                    final["generation"] = node_output.get("generation", "")
                elif node_name == "rewrite_query":
                    current_query = node_output.get("current_search_query", current_query)
                    yield _sse({"type": "status", "message": f" Self-Heal: Rewrote query -> \"{current_query}\"", "event": "heal"})
            elif kind == "on_chain_start" and node_name == "smart_router":
                yield _sse({"type": "status", "message": " Contextualising query with conversation history..."})
            elif kind == "on_chain_start" and node_name == "generate":
                yield _sse({"type": "status", "message": " Drafting answer with source citations..."})

        if "information missing" in final["generation"].lower():
            final["generation"] = "No verifiable answer could be found for your query. Please verify the relevant documents."

        yield _sse({"type": "final", "message": final["generation"], "docs": final["retrieved_docs"], "confidence": final["confidence"]})
        save_chat_to_db(request.session_id, request.query, final["generation"], final["retrieved_docs"], final["confidence"])
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/documents")
async def list_documents():
    return {"documents": app.state.doc_store.get_indexed_files()}

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(('.pdf', '.txt', '.md', '.csv', '.xlsx', '.docx')):
        raise HTTPException(status_code=400, detail="Unsupported file format.")

    save_path = os.path.join(DATA_FOLDER, file.filename)
    os.makedirs(DATA_FOLDER, exist_ok=True)
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    chunks = app.state.doc_store.index_file(save_path, file.filename)
    return {"status": "success", "file": file.filename, "chunks_indexed": chunks}

@app.delete("/documents/{filename}")
async def delete_document(filename: str):
    if not app.state.doc_store.delete_file(filename):
        raise HTTPException(status_code=404, detail=f"'{filename}' was not found in the index.")
    
    disk_path = os.path.join(DATA_FOLDER, filename)
    if os.path.exists(disk_path): os.remove(disk_path)
    return {"status": "success"}

@app.get("/status")
async def get_status():
    return {
        "hybrid_search": app.state.doc_store.hybrid_enabled,
        "documents": app.state.doc_store.get_indexed_files()
    }
