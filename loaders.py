import os
from pathlib import Path
from typing import List, Union
from langchain_core.documents import Document

class DocumentLoader:
    @classmethod
    def load(cls, source: Union[str, Path]) -> List[Document]:
        source_str = str(source)
        is_web = source_str.startswith("http://") or source_str.startswith("https://")
        
        if is_web:
            if "youtube.com" in source_str or "youtu.be" in source_str:
                from langchain_community.document_loaders import YoutubeLoader
                loader = YoutubeLoader.from_youtube_url(source_str, add_video_info=False)
            else:
                from langchain_community.document_loaders import WebBaseLoader
                loader = WebBaseLoader(source_str)
        else:
            path = Path(source)
            if not path.exists():
                raise FileNotFoundError(f"File not found: {source}")
                
            ext = path.suffix.lower()
            if ext == ".pdf":
                from langchain_community.document_loaders import PyPDFLoader
                loader = PyPDFLoader(str(path))
            elif ext == ".csv":
                from langchain_community.document_loaders import CSVLoader
                loader = CSVLoader(str(path))
            elif ext in [".txt", ".md"]:
                from langchain_community.document_loaders import TextLoader
                loader = TextLoader(str(path), encoding="utf-8")
            elif ext == ".docx":
                from langchain_community.document_loaders import Docx2txtLoader
                loader = Docx2txtLoader(str(path))
            elif ext == ".xlsx":
                from langchain_community.document_loaders import UnstructuredExcelLoader
                loader = UnstructuredExcelLoader(str(path))
            elif ext == ".pptx":
                from langchain_community.document_loaders import UnstructuredPowerPointLoader
                loader = UnstructuredPowerPointLoader(str(path))
            else:
                raise ValueError(f"Unsupported file extension: {ext}")
                
        docs = loader.load()
        
        # Normalize metadata for ingest.py
        for i, doc in enumerate(docs):
            if is_web:
                doc.metadata["source_file"] = source_str
                doc.metadata["file_type"] = "youtube" if "youtu" in source_str else "web"
                doc.metadata["page_number"] = 1
            else:
                doc.metadata["source_file"] = path.name
                doc.metadata["file_type"] = ext[1:]
                doc.metadata["page_number"] = doc.metadata.get("page", i + 1)
                
        return docs
