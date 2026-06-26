import enum
import uuid
from typing import List, Optional
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter, TokenTextSplitter
from langchain_experimental.text_splitter import SemanticChunker
from langchain_huggingface import HuggingFaceEmbeddings

class ChunkingStrategy(enum.Enum):
    SEMANTIC = "semantic"
    RECURSIVE = "recursive"
    SLIDING_WINDOW = "sliding_window"
    PASS_THROUGH = "pass_through"

class Chunker:
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    def auto_select_strategy(self, file_type: str) -> ChunkingStrategy:
        ext = file_type.lower()
        if ext == "pdf":
            return ChunkingStrategy.SLIDING_WINDOW
        elif ext in ["docx", "md", "pptx"]:
            return ChunkingStrategy.SEMANTIC
        elif ext in ["csv", "xlsx"]:
            return ChunkingStrategy.PASS_THROUGH
        else:
            return ChunkingStrategy.RECURSIVE

    def chunk(self, docs: List[Document], strategy: Optional[str] = None) -> List[Document]:
        if not docs:
            return []
            
        file_type = docs[0].metadata.get("file_type", "txt")
        
        if not strategy:
            strat = self.auto_select_strategy(file_type)
        else:
            try:
                strat = ChunkingStrategy(strategy.lower())
            except ValueError:
                strat = self.auto_select_strategy(file_type)

        if strat == ChunkingStrategy.PASS_THROUGH:
            return docs
        elif strat == ChunkingStrategy.SEMANTIC:
            return self._chunk_semantic(docs)
        elif strat == ChunkingStrategy.RECURSIVE:
            return self._chunk_recursive(docs, file_type)
        elif strat == ChunkingStrategy.SLIDING_WINDOW:
            return self._chunk_sliding_window(docs)
        else:
            return docs

    def _chunk_semantic(self, docs: List[Document]) -> List[Document]:
        splitter = SemanticChunker(self.embeddings, breakpoint_threshold_type="percentile")
        return splitter.split_documents(docs)

    def _chunk_recursive(self, docs: List[Document], file_type: str) -> List[Document]:
        if file_type == "md":
            separators = ["\n## ", "\n### ", "\n\n", "\n", " ", ""]
        elif file_type in ["py", "js", "ts"]:
            separators = ["\n\ndef ", "\n\nclass ", "\n\nfunction ", "\n\n", "\n", " ", ""]
        else:
            separators = ["\n\n", "\n", " ", ""]
            
        splitter = RecursiveCharacterTextSplitter(
            separators=separators,
            chunk_size=750,
            chunk_overlap=120
        )
        return splitter.split_documents(docs)

    def _chunk_sliding_window(self, docs: List[Document]) -> List[Document]:
        splitter = TokenTextSplitter(
            chunk_size=512,
            chunk_overlap=int(512 * 0.2)
        )
        return splitter.split_documents(docs)
