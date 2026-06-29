import os
os.environ.setdefault("PYTHONUTF8", "1")

import json
import shutil
import uuid
import datetime
import logging
from typing import List, Optional
from contextlib import asynccontextmanager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import desc

class EvaluationResult(BaseModel):
    faithfulness_score: float
    answer_relevance_score: float
    reasoning: str

class MemoryUpdate(BaseModel):
    memory: str



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
    # _auto_index_folder() is removed because indexing on 0.1 CPU blocks server startup and causes Render timeout. Files are now handled via IndexedDB anyway.
    yield

app = FastAPI(
    title="TheSuperRAG API",
    description="Self-Healing RAG backend.",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
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
        logger.error(f"Failed to save chat: {e}", exc_info=True)
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
async def chat_stream(http_req: Request, request: ChatRequest):
    api_key = http_req.headers.get("x-api-key")
    provider = http_req.headers.get("x-provider", "groq")
    model = http_req.headers.get("x-model", request.llm_model)
    
    rag_system = app.state.rag_system
    async def event_generator():
        from database import UserProfile
        db = SessionLocal()
        user_profile = db.query(UserProfile).filter(UserProfile.id == "default_user").first()
        user_memory = user_profile.memory if user_profile else ""
        db.close()
        
        inputs = {
            "chat_history": request.history,
            "user_query": request.query,
            "current_search_query": request.query,
            "temperature": request.temperature,
            "user_memory": user_memory,
            "api_key": api_key,
            "provider": provider,
            "model": model
        }
        final = {"generation": "", "retrieved_docs": [], "confidence": {}}
        current_query = request.query

        async for event in rag_system.app.astream_events(inputs, version="v2"):
            kind = event["event"]
            node_name = event.get("metadata", {}).get("langgraph_node", "")
            
            if kind == "on_chat_model_stream" and node_name == "generate":
                chunk_text = event["data"]["chunk"].content
                if chunk_text: yield _sse({"type": "token", "content": chunk_text})
            elif kind == "decomposed":
                yield _sse({"type": "decomposed", "sub_queries": event.get("sub_queries", [])})
            elif kind == "tool_start":
                yield _sse({"type": "tool_start", "tool": event.get("tool"), "query": event.get("query")})
            elif kind == "tool_done":
                yield _sse({"type": "tool_done", "tool": event.get("tool"), "result_count": event.get("result_count")})
            elif kind == "on_chain_end" and node_name in ["smart_router", "retrieve", "generate", "rewrite_query"]:
                node_output = event.get("data", {}).get("output", {})
                if not isinstance(node_output, dict): continue
                if node_name == "smart_router":
                    gen = node_output.get("generation", "")
                    if gen and gen.lower() != "proceed":
                        yield _sse({"type": "final", "message": gen, "docs": [], "confidence": {}})
                        save_chat_to_db(request.session_id, request.query, gen, [], {})
                        yield "data: [DONE]\n\n"
                        return
                elif node_name == "retrieve":
                    final["retrieved_docs"] = node_output.get("retrieved_docs", [])
                    final["confidence"] = node_output.get("confidence", {})
                    yield _sse({"type": "metadata", "confidence": final["confidence"].get("score", 0), "sources": final["retrieved_docs"]})
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
async def upload_document(
    file: Optional[UploadFile] = File(None),
    url: Optional[str] = Form(None),
    session_id: Optional[str] = Form(None)
):
    if url:
        chunks = app.state.doc_store.index_file(url, url, session_id=session_id)
        already_indexed = url in app.state.doc_store.get_indexed_files()
        if chunks == 0 and not already_indexed:
            raise HTTPException(status_code=400, detail="Failed to extract text from URL or no content found.")
        return {"status": "success", "file": url, "chunks_indexed": chunks}
        
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="Must provide either a file or a url.")

    if not file.filename.lower().endswith(('.pdf', '.txt', '.md', '.csv', '.xlsx', '.docx')):
        raise HTTPException(status_code=400, detail="Unsupported file format.")

    save_path = os.path.join(DATA_FOLDER, file.filename)
    os.makedirs(DATA_FOLDER, exist_ok=True)
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    chunks = app.state.doc_store.index_file(save_path, file.filename, session_id=session_id)
    
    if os.path.exists(save_path):
        os.remove(save_path)
        
    already_indexed = file.filename in app.state.doc_store.get_indexed_files()
    if chunks == 0 and not already_indexed:
        raise HTTPException(status_code=400, detail="Failed to parse document or no text found.")
        
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
        "documents": app.state.doc_store.get_indexed_files(),
        "initialized": True,
        "init_in_progress": False,
        "init_error": None
    }

@app.post("/init")
async def init_backend():
    return {"status": "already initialized"}

@app.get("/events")
async def get_events():
    async def dummy_events():
        yield "data: [DONE]\n\n"
    from fastapi.responses import StreamingResponse
    return StreamingResponse(dummy_events(), media_type="text/event-stream")

@app.post("/sessions/{session_id}/evaluate", response_model=EvaluationResult)
async def evaluate_session(session_id: str, http_req: Request, db: Session = Depends(get_db)):
    messages = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(desc(ChatMessage.id)).limit(2).all()
    if len(messages) < 2:
        raise HTTPException(status_code=400, detail="Not enough messages to evaluate")
        
    user_msg = next((m for m in messages if m.role == "user"), None)
    asst_msg = next((m for m in messages if m.role == "assistant"), None)
    
    if not user_msg or not asst_msg:
        raise HTTPException(status_code=400, detail="Incomplete chat turn")
        
    context = "\n".join([f"[{i+1}] {d.get('snippet', '')}" for i, d in enumerate(asst_msg.docs)]) if asst_msg.docs else "No context retrieved."
    
    api_key = http_req.headers.get("x-api-key")
    provider = http_req.headers.get("x-provider", "groq")
    model = http_req.headers.get("x-model", "llama-3.1-8b-instant")
    
    state = {"api_key": api_key, "provider": provider, "model": model}
    llm = app.state.rag_system._get_llm(state, temperature=0.0)
    
    prompt = f"""You are an expert evaluator for a RAG system.
Evaluate the following interaction based on two metrics:
1. Faithfulness: Is the answer derived ONLY from the provided context? (Score 0.0 to 1.0)
2. Answer Relevance: Does the answer directly address the user's query? (Score 0.0 to 1.0)

User Query: {user_msg.content}
Retrieved Context: {context}
System Answer: {asst_msg.content}

Return your evaluation EXACTLY in this JSON format:
{{
  "faithfulness_score": 0.9,
  "answer_relevance_score": 0.8,
  "reasoning": "Brief explanation of scores..."
}}"""
    
    try:
        res = await llm.ainvoke([HumanMessage(content=prompt)])
        content = res.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
            
        import json
        eval_data = json.loads(content, strict=False)
        return EvaluationResult(
            faithfulness_score=eval_data.get("faithfulness_score", 0.0),
            answer_relevance_score=eval_data.get("answer_relevance_score", 0.0),
            reasoning=eval_data.get("reasoning", "No reasoning provided")
        )
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        raise HTTPException(status_code=500, detail="Evaluation failed")

@app.get("/user/memory")
async def get_user_memory(db: Session = Depends(get_db)):
    from database import UserProfile
    user_profile = db.query(UserProfile).filter(UserProfile.id == "default_user").first()
    return {"memory": user_profile.memory if user_profile else ""}

@app.post("/user/memory")
@app.patch("/user/memory")
async def update_user_memory(payload: MemoryUpdate, db: Session = Depends(get_db)):
    from database import UserProfile
    user_profile = db.query(UserProfile).filter(UserProfile.id == "default_user").first()
    if not user_profile:
        user_profile = UserProfile(id="default_user", memory=payload.memory)
        db.add(user_profile)
    else:
        user_profile.memory = payload.memory
    db.commit()
    return {"status": "success", "memory": user_profile.memory}

