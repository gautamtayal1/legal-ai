from typing import Dict, List, Optional, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter, CharacterTextSplitter
import uuid
import re

from .base import ChunkingService, ChunkConfig, DocumentChunk


class SemanticChunker(ChunkingService):
    def __init__(self, config: ChunkConfig):
        super().__init__(config)
        self._setup_splitters()
    
    def _setup_splitters(self):
        self.recursive_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
            length_function=len,
            separators=self.config.separators or ["\n\n", "\n", ". ", " ", ""],
            keep_separator=True
        )
        
        self.character_splitter = CharacterTextSplitter(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
            separator="\n\n",
            keep_separator=True
        )
    
    def chunk_text(self, text: str, document_id: str, metadata: Optional[Dict[str, Any]] = None) -> List[DocumentChunk]:
        if not text.strip():
            return []
            
        metadata = metadata or {}
        
        # Use recursive chunking for better semantic boundaries
        chunks = self._recursive_chunk(text, document_id, metadata)
        
        return self.validate_chunks(chunks)
    
    def _character_chunk(self, text: str, document_id: str, metadata: Dict[str, Any]) -> List[DocumentChunk]:
        chunk_texts = self.character_splitter.split_text(text)
        chunks = []
        
        current_position = 0
        for i, chunk_text in enumerate(chunk_texts):
            start_pos = text.find(chunk_text, current_position)
            if start_pos == -1:
                start_pos = current_position
            
            chunk = DocumentChunk(
                id=str(uuid.uuid4()),
                content=chunk_text,
                metadata={
                    **metadata,
                    "chunking_method": "character",
                    "chunk_type": "character"
                },
                start_position=start_pos,
                end_position=start_pos + len(chunk_text),
                chunk_index=i,
                document_id=document_id
            )
            chunks.append(chunk)
            current_position = start_pos + len(chunk_text)
        
        return chunks
    
    def _recursive_chunk(self, text: str, document_id: str, metadata: Dict[str, Any]) -> List[DocumentChunk]:
        chunk_texts = self.recursive_splitter.split_text(text)
        chunks = []
        
        current_position = 0
        for i, chunk_text in enumerate(chunk_texts):
            start_pos = text.find(chunk_text, current_position)
            if start_pos == -1:
                start_pos = current_position
            
            chunk = DocumentChunk(
                id=str(uuid.uuid4()),
                content=chunk_text,
                metadata={
                    **metadata,
                    "chunking_method": "recursive",
                    "chunk_type": "recursive"
                },
                start_position=start_pos,
                end_position=start_pos + len(chunk_text),
                chunk_index=i,
                document_id=document_id
            )
            chunks.append(chunk)
            current_position = start_pos + len(chunk_text)
        
        return chunks
    
    def chunk_document(self, document: Dict[str, Any]) -> List[DocumentChunk]:
        text = document.get("content", "")
        document_id = document.get("id", str(uuid.uuid4()))
        metadata = document.get("metadata", {})
        
        return self.chunk_text(text, document_id, metadata)