from typing import List, Optional
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

class Chunker:
    def chunk(self, docs: List[Document], strategy: Optional[str] = None) -> List[Document]:
        if not docs:
            return []
            
        file_type = docs[0].metadata.get("file_type", "txt")
        
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
