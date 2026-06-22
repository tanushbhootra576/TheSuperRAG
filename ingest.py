"""
ingest.py -- DocumentStore for TheSuperRAG.

Manages a local Qdrant vector collection with:
  - Hybrid search: dense (all-MiniLM-L6-v2) + sparse BM25 (Qdrant/bm25)
  - Incremental upsert: only index new files, never re-index existing ones
  - Page-number metadata: every chunk knows its source file and page
  - Document deletion: remove a file's chunks without touching others
  - Document listing: enumerate all indexed source files
  - Auto-migration: detects legacy (dense-only) collections and rebuilds them

Hybrid search dramatically improves recall for exact keyword matches
(e.g., "Article 4.2", "Section 3(b)(ii)") while retaining semantic quality.
"""
import os
from typing import List, Optional, Callable

from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from qdrant_client import QdrantClient, models
from qdrant_client.models import (
    Distance,
    VectorParams,
    SparseVectorParams,
    SparseIndexParams,
)
import fitz  # PyMuPDF
import base64
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from langchain_core.documents import Document
from pydantic import BaseModel, Field
from database import SessionLocal, GraphNode, GraphEdge

load_dotenv()

# ── Configuration ────────────────────────────────────────────────────────────
DENSE_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
SPARSE_MODEL = "Qdrant/bm25"
VECTOR_SIZE = 384          # all-MiniLM-L6-v2 output dimension
CHUNK_SIZE = 750
CHUNK_OVERLAP = 120
DB_VERSION = "v2_hybrid"   # Written to disk; triggers re-index on format change


class DocumentStore:
    """
    Persistent, hybrid-search document store backed by local Qdrant.

    A single instance should be shared across the application lifetime.
    Thread-safe for reads; writes are serialised by the calling code.
    """

    def __init__(
        self,
        folder_path: str = "DATA",
        collection_name: str = "super_rag",
    ):
        self.folder_path = os.path.abspath(folder_path)
        self.collection_name = collection_name
        self.qdrant_path = os.path.join(self.folder_path, "qdrant_db")
        self._version_file = os.path.join(self.qdrant_path, ".db_version")

        os.makedirs(self.qdrant_path, exist_ok=True)
        os.makedirs(self.folder_path, exist_ok=True)

        # ── Load embedding models ─────────────────────────────────────────
        print("  [*] Loading dense embedding model (all-MiniLM-L6-v2)...")
        self.dense_embeddings = HuggingFaceEmbeddings(model_name=DENSE_MODEL)

        # ── Qdrant client ─────────────────────────────────────────────────
        self.client = QdrantClient(path=self.qdrant_path)

        # ── Migrate if this is a legacy (dense-only) collection ───────────
        self._migrate_if_needed()

        # ── Ensure the hybrid collection exists ───────────────────────────
        self._ensure_collection()

        # ── Build the LangChain vector store wrapper ──────────────────────
        self._vector_store = self._build_vector_store()


    # ── Private helpers ───────────────────────────────────────────────────────

    def _current_db_version(self) -> str:
        if not os.path.exists(self._version_file):
            return "unknown"
        with open(self._version_file, "r") as f:
            return f.read().strip()

    def _write_db_version(self):
        with open(self._version_file, "w") as f:
            f.write(DB_VERSION)

    def _migrate_if_needed(self):
        """Drop and recreate collection if the DB format is outdated."""
        if self._current_db_version() != DB_VERSION:
            print("  [*] Migrating to hybrid-search format (one-time operation)...")
            existing = {c.name for c in self.client.get_collections().collections}
            if self.collection_name in existing:
                self.client.delete_collection(self.collection_name)
                print(f"    Dropped legacy collection '{self.collection_name}'.")
            self._write_db_version()

    def _ensure_collection(self):
        """Create the hybrid Qdrant collection if it does not exist."""
        existing = {c.name for c in self.client.get_collections().collections}
        if self.collection_name not in existing:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config={
                    "dense": VectorParams(
                        size=VECTOR_SIZE,
                        distance=Distance.COSINE,
                    )
                },
                sparse_vectors_config={
                    "sparse": SparseVectorParams(
                        index=SparseIndexParams(on_disk=False)
                    )
                },
            )
            print(f"  [+] Created hybrid collection: '{self.collection_name}'")

    def _build_vector_store(self):
        """Build the LangChain QdrantVectorStore with hybrid retrieval mode."""
        try:
            from langchain_qdrant import QdrantVectorStore, RetrievalMode
            try:
                from langchain_qdrant import FastEmbedSparse
            except ImportError:
                from langchain_qdrant.sparse_embeddings import FastEmbedSparse

            print("  [>] Loading sparse BM25 model (Qdrant/bm25)...")
            sparse = FastEmbedSparse(model_name=SPARSE_MODEL)

            vs = QdrantVectorStore(
                client=self.client,
                collection_name=self.collection_name,
                embedding=self.dense_embeddings,
                sparse_embedding=sparse,
                retrieval_mode=RetrievalMode.HYBRID,
                vector_name="dense",
                sparse_vector_name="sparse",
            )
            print("  [OK] Hybrid vector store ready (dense + BM25 sparse).")
            self._hybrid_enabled = True
            return vs
        except Exception as e:
            print(f"  [!] Hybrid mode unavailable ({e}), falling back to dense-only search.")
            from langchain_qdrant import QdrantVectorStore
            self._hybrid_enabled = False
            return QdrantVectorStore(
                client=self.client,
                collection_name=self.collection_name,
                embedding=self.dense_embeddings,
                vector_name="dense",
            )

    def _auto_index_folder(self, on_progress: Optional[Callable] = None):
        """Index all PDFs in folder_path that are not yet in the collection."""
        already_indexed = set(self.get_indexed_files())
        pdf_files = [
            f for f in os.listdir(self.folder_path)
            if f.lower().endswith(".pdf")
        ]
        new_files = [f for f in pdf_files if f not in already_indexed]

        if new_files:
            print(f"  [>] Auto-indexing {len(new_files)} new PDF(s)...")
            for file_name in new_files:
                chunks = self.index_file(
                    os.path.join(self.folder_path, file_name), file_name
                )
                if chunks > 0 and on_progress:
                    on_progress({
                        "type": "document_indexed",
                        "file": file_name,
                        "chunks": chunks
                    })
        elif not pdf_files:
            print("  [!] No PDFs found in DATA/. Add PDFs then call /init.")

    # ── Public API ────────────────────────────────────────────────────────────

    def get_indexed_files(self) -> List[str]:
        """Return a sorted list of all source filenames currently indexed."""
        try:
            existing = {c.name for c in self.client.get_collections().collections}
            if self.collection_name not in existing:
                return []

            result, _ = self.client.scroll(
                collection_name=self.collection_name,
                limit=10_000,
                with_payload=True,
                with_vectors=False,
            )
            files: set = set()
            for point in result:
                src = point.payload.get("metadata", {}).get("source_file")
                if src:
                    files.add(src)
            return sorted(files)
        except Exception as e:
            print(f"[DocumentStore] get_indexed_files error: {e}")
            return []

    def index_file(self, file_path: str, file_name: str) -> int:
        """
        Parse a PDF and upsert its chunks into the collection.

        Skips the file if it is already indexed.
        Returns the number of chunks added (0 on skip or error).
        """
        already = set(self.get_indexed_files())
        if file_name in already:
            print(f"  [skip] '{file_name}' already indexed.")
            return 0

        try:
            print(f"  [>] Parsing: {file_name}")
            # PyPDFLoader: lightweight, uses pypdf, gives page_number natively
            loader = PyPDFLoader(file_path)
            raw_docs = loader.load()

            splitter = RecursiveCharacterTextSplitter(
                chunk_size=CHUNK_SIZE,
                chunk_overlap=CHUNK_OVERLAP,
            )
            chunks = splitter.split_documents(raw_docs)

            if not chunks:
                print(f"  [!] No content extracted from '{file_name}'.")
                return 0

            # ── Vision / Multi-Modal Extraction ──────────────────────────────
            print(f"  [>] Extracting images/charts using Vision Model for: {file_name}")
            try:
                vision_docs = self._extract_image_descriptions(file_path, file_name)
                if vision_docs:
                    print(f"  [+] Added {len(vision_docs)} image descriptions for {file_name}")
                    chunks.extend(vision_docs)
            except Exception as e:
                print(f"  [!] Vision extraction skipped/failed: {e}")

            for chunk in chunks:
                # PyPDFLoader gives page_number as doc.metadata['page'] (0-indexed)
                page = chunk.metadata.get(
                    "page_number",
                    chunk.metadata.get("page", "N/A")
                )
                chunk.metadata["page_number"] = page
                chunk.metadata["source_file"] = file_name
                chunk.metadata["category"] = chunk.metadata.get("category", "text")

            # ── GraphRAG Extraction ──────────────────────────────────────────
            print(f"  [>] Extracting Knowledge Graph entities for: {file_name}")
            try:
                self._extract_and_save_graph(chunks, file_name)
            except Exception as e:
                print(f"  [!] Graph extraction failed: {e}")

            # ── Add to Qdrant ────────────────────────────────────────────────
            self._vector_store.add_documents(chunks)
            print(f"  [OK] Indexed {len(chunks)} chunks from '{file_name}'")
            return len(chunks)

        except Exception as e:
            print(f"  [X] Error indexing '{file_name}': {e}")
            return 0

    def delete_file(self, file_name: str) -> bool:
        """
        Remove all chunks belonging to `file_name` from the collection.
        Does NOT delete the file from disk (handled by the API layer).
        """
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.FilterSelector(
                    filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="metadata.source_file",
                                match=models.MatchValue(value=file_name),
                            )
                        ]
                    )
                ),
            )
            print(f"  [OK] Deleted all chunks for '{file_name}'")
            return True
        except Exception as e:
            print(f"  [X] Error deleting '{file_name}': {e}")
            return False

    def get_retriever(
        self,
        selected_docs: Optional[List[str]] = None,
        k: int = 10,
    ):
        """
        Return a LangChain retriever.

        Args:
            selected_docs: If provided, retrieval is filtered to these files only.
                           Pass None or [] to search the entire collection.
            k:             Number of candidates to retrieve before re-ranking.
        """
        qdrant_filter = None
        if selected_docs:
            qdrant_filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key="metadata.source_file",
                        match=models.MatchAny(any=selected_docs),
                    )
                ]
            )

        search_kwargs: dict = {"k": k}
        if qdrant_filter:
            search_kwargs["filter"] = qdrant_filter

        return self._vector_store.as_retriever(search_kwargs=search_kwargs)

    # ── GraphRAG Extraction Logic ────────────────────────────────────────────

    def _extract_and_save_graph(self, chunks: List[Document], file_name: str):
        class Node(BaseModel):
            id: str = Field(description="Unique name of the entity")
            label: str = Field(description="Type: PERSON, ORGANIZATION, LAW, LOCATION, CONCEPT")

        class Edge(BaseModel):
            source: str = Field(description="Source entity ID")
            target: str = Field(description="Target entity ID")
            relation: str = Field(description="Relationship type, like 'REGULATES', 'PART_OF'")

        class KnowledgeGraph(BaseModel):
            nodes: List[Node] = Field(default_factory=list)
            edges: List[Edge] = Field(default_factory=list)

        groq_key = os.getenv("GROQ_API_KEY")
        if not groq_key: return

        llm = ChatGroq(
            model_name="llama-3.1-8b-instant",
            temperature=0.0,
            groq_api_key=groq_key
        ).with_structured_output(KnowledgeGraph)

        db = SessionLocal()
        
        # Process a subset of chunks to avoid massive token usage/rate limits for this demo.
        # In production, you might batch this or process all chunks.
        sample_chunks = chunks[:20] 

        for chunk in sample_chunks:
            try:
                graph: KnowledgeGraph = llm.invoke(
                    f"Extract entities and relationships from this text:\n\n{chunk.page_content}"
                )
                if not graph: continue

                for n in graph.nodes:
                    existing_node = db.query(GraphNode).filter(GraphNode.id == n.id).first()
                    if not existing_node:
                        db.add(GraphNode(id=n.id, label=n.label, source_file=file_name))
                
                for e in graph.edges:
                    db.add(GraphEdge(
                        source=e.source, 
                        target=e.target, 
                        relation=e.relation, 
                        source_file=file_name
                    ))
                db.commit()
            except Exception as ex:
                db.rollback()
                pass
        
        db.close()

    # ── Vision Logic ─────────────────────────────────────────────────────────

    def _extract_image_descriptions(self, file_path: str, file_name: str) -> List[Document]:
        """Extracts images using PyMuPDF and describes them using Groq Vision."""
        groq_key = os.getenv("GROQ_API_KEY")
        if not groq_key:
            return []
            
        try:
            vision_llm = ChatGroq(
                model_name="llama-3.2-11b-vision-preview",
                temperature=0.0,
                groq_api_key=groq_key
            )
        except Exception:
            return []

        doc = fitz.open(file_path)
        image_docs = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            image_list = page.get_images(full=True)
            
            for img_index, img in enumerate(image_list):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                
                # Encode base64
                b64_image = base64.b64encode(image_bytes).decode("utf-8")
                
                # Describe image
                message = HumanMessage(
                    content=[
                        {"type": "text", "text": "Describe this image, chart, or table in detail. Extract any relevant text or data points. If it's just a decorative graphic or logo, reply strictly with 'SKIP'."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"}}
                    ]
                )
                try:
                    response = vision_llm.invoke([message])
                    description = response.content.strip()
                    if "SKIP" not in description.upper() and len(description) > 10:
                        image_docs.append(Document(
                            page_content=f"[Image/Chart/Table Description]: {description}",
                            metadata={
                                "source_file": file_name,
                                "page_number": page_num + 1,
                                "type": "image_description"
                            }
                        ))
                except Exception as e:
                    print(f"      [!] Vision failed for p{page_num+1} img {img_index}: {e}")
                    
        return image_docs

    def is_empty(self) -> bool:
        """Return True if the collection has no indexed documents."""
        try:
            info = self.client.get_collection(self.collection_name)
            return (info.points_count or 0) == 0
        except Exception:
            return True

    @property
    def hybrid_enabled(self) -> bool:
        """Whether hybrid (dense + sparse) search is active."""
        return getattr(self, "_hybrid_enabled", False)