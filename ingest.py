"""
ingest.py - DocumentStore for TheSuperRAG.

Manages a local Qdrant vector collection with:
  - Hybrid search: dense (all-MiniLM-L6-v2) + sparse BM25 (Qdrant/bm25)
  - Incremental upsert: only index new files, never re-index existing ones
  - Document deletion: remove a file's chunks without touching others
"""
import os
from typing import List, Optional, Callable
import logging

logger = logging.getLogger(__name__)


from dotenv import load_dotenv
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from qdrant_client import QdrantClient, models
from qdrant_client.models import (
    Distance,
    VectorParams,
    SparseVectorParams,
    SparseIndexParams,
)
from loaders import DocumentLoader
from chunker import Chunker
from langchain_core.documents import Document

load_dotenv()

# - Configuration -
DENSE_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
SPARSE_MODEL = "Qdrant/bm25"
VECTOR_SIZE = 384
DB_VERSION = "v2_hybrid"

class DocumentStore:
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

        logger.info("Loading dense embedding model (all-MiniLM-L6-v2) via FastEmbed...")
        self.dense_embeddings = FastEmbedEmbeddings(model_name=DENSE_MODEL, threads=1)
        self.client = QdrantClient(location=":memory:")

        self._migrate_if_needed()
        self._ensure_collection()
        self._vector_store = self._build_vector_store()

    def _current_db_version(self) -> str:
        if not os.path.exists(self._version_file):
            return "unknown"
        with open(self._version_file, "r") as f:
            return f.read().strip()

    def _write_db_version(self):
        with open(self._version_file, "w") as f:
            f.write(DB_VERSION)

    def _migrate_if_needed(self):
        if self._current_db_version() != DB_VERSION:
            existing = {c.name for c in self.client.get_collections().collections}
            if self.collection_name in existing:
                self.client.delete_collection(self.collection_name)
            self._write_db_version()

    def _ensure_collection(self):
        existing = {c.name for c in self.client.get_collections().collections}
        if self.collection_name not in existing:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config={
                    "dense": VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE)
                },
                sparse_vectors_config={
                    "sparse": SparseVectorParams(index=SparseIndexParams(on_disk=False))
                },
            )

    def _build_vector_store(self):
        try:
            from langchain_qdrant import QdrantVectorStore, RetrievalMode
            try:
                from langchain_qdrant import FastEmbedSparse
            except ImportError:
                from langchain_qdrant.sparse_embeddings import FastEmbedSparse

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
            self._hybrid_enabled = True
            return vs
        except Exception:
            from langchain_qdrant import QdrantVectorStore
            self._hybrid_enabled = False
            return QdrantVectorStore(
                client=self.client,
                collection_name=self.collection_name,
                embedding=self.dense_embeddings,
                vector_name="dense",
            )

    def _enrich_chunks(self, chunks: List[Document], file_name: str, raw_docs: List[Document]):
        return # Disabled to prevent 429 Rate Limit issues on BYOK setups

    def _redact_pii(self, text: str) -> str:
        import re
        # Basic Email Redaction
        text = re.sub(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', '[REDACTED_EMAIL]', text)
        # Basic SSN Redaction
        text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[REDACTED_SSN]', text)
        # Phone numbers
        text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[REDACTED_PHONE]', text)
        return text

    def _auto_index_folder(self, on_progress: Optional[Callable] = None):
        already_indexed = set(self.get_indexed_files())
        supported_exts = {".pdf", ".docx", ".txt", ".md", ".csv", ".xlsx", ".pptx"}
        all_files = [f for f in os.listdir(self.folder_path) if os.path.splitext(f.lower())[1] in supported_exts]
        new_files = [f for f in all_files if f not in already_indexed]

        if new_files:
            for file_name in new_files:
                chunks = self.index_file(os.path.join(self.folder_path, file_name), file_name)
                if chunks > 0 and on_progress:
                    on_progress({"type": "document_indexed", "file": file_name, "chunks": chunks})

    def get_indexed_files(self) -> List[str]:
        try:
            existing = {c.name for c in self.client.get_collections().collections}
            if self.collection_name not in existing:
                return []
            result, _ = self.client.scroll(collection_name=self.collection_name, limit=10_000, with_payload=True, with_vectors=False)
            files = set(point.payload.get("metadata", {}).get("source_file") for point in result if point.payload.get("metadata", {}).get("source_file"))
            return sorted(files)
        except Exception:
            return []

    def index_file(self, file_path: str, file_name: str, strategy: Optional[str] = None, tags: Optional[List[str]] = None, author: Optional[str] = None, session_id: Optional[str] = None) -> int:
        already = set(self.get_indexed_files())
        if file_name in already:
            return 0

        try:
            raw_docs = DocumentLoader.load(file_path)
            for doc in raw_docs:
                if tags: doc.metadata["tags"] = tags
                if author: doc.metadata["author"] = author
                if session_id: doc.metadata["session_id"] = session_id

            chunker = Chunker()
            chunks = chunker.chunk(raw_docs, strategy)
            if not chunks: return 0

            self._enrich_chunks(chunks, file_name, raw_docs)

            for chunk in chunks:
                chunk.page_content = self._redact_pii(chunk.page_content)
                chunk.metadata["page_number"] = chunk.metadata.get("page_number", chunk.metadata.get("page", "N/A"))
                chunk.metadata["source_file"] = file_name
                chunk.metadata["category"] = chunk.metadata.get("category", "text")

            self._vector_store.add_documents(chunks)
            return len(chunks)
        except Exception as e:
            logger.error(f"Error indexing file {file_name}: {e}")
            return 0

    def delete_file(self, file_name: str) -> bool:
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.FilterSelector(
                    filter=models.Filter(must=[models.FieldCondition(key="metadata.source_file", match=models.MatchValue(value=file_name))])
                ),
            )
            return True
        except Exception:
            return False

    def get_retriever(self, qdrant_filter: Optional[models.Filter] = None, k: int = 10):
        search_kwargs = {"k": k}
        if qdrant_filter: search_kwargs["filter"] = qdrant_filter
        return self._vector_store.as_retriever(search_kwargs=search_kwargs)

    def is_empty(self) -> bool:
        try:
            info = self.client.get_collection(self.collection_name)
            return (info.points_count or 0) == 0
        except Exception:
            return True

    @property
    def hybrid_enabled(self) -> bool:
        return getattr(self, "_hybrid_enabled", False)