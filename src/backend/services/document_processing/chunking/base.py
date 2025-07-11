from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class ChunkingStrategy(Enum):
    SEMANTIC = "semantic"
    LEGAL = "legal"
    FIXED_SIZE = "fixed_size"
    RECURSIVE = "recursive"

@dataclass
class ChunkConfig:
    chunk_size: int = 1000
    chunk_overlap: int = 200
    strategy: ChunkingStrategy = ChunkingStrategy.SEMANTIC
    preserve_legal_structure: bool = True
    min_chunk_size: int = 100
    max_chunk_size: int = 4000
    separators: Optional[List[str]] = None
    legal_section_markers: Optional[List[str]] = None


@dataclass
class DocumentChunk:
    id: str
    content: str
    metadata: Dict[str, Any]
    start_position: int
    end_position: int
    chunk_index: int
    document_id: str
    parent_section: Optional[str] = None
    legal_context: Optional[Dict[str, Any]] = None


class ChunkingService(ABC):
    def __init__(self, config: ChunkConfig):
        self.config = config
        
    @abstractmethod
    def chunk_text(self, text: str, document_id: str, metadata: Optional[Dict[str, Any]] = None) -> List[DocumentChunk]:
        pass
    
    @abstractmethod 
    def chunk_document(self, document: Dict[str, Any]) -> List[DocumentChunk]:
        pass
    
    def validate_chunks(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        validated_chunks = []
        for chunk in chunks:
            if len(chunk.content.strip()) >= self.config.min_chunk_size:
                validated_chunks.append(chunk)
        return validated_chunks
    
    def get_chunk_statistics(self, chunks: List[DocumentChunk]) -> Dict[str, Any]:
        if not chunks:
            return {}
            
        chunk_lengths = [len(chunk.content) for chunk in chunks]
        return {
            "total_chunks": len(chunks),
            "avg_chunk_length": sum(chunk_lengths) / len(chunk_lengths),
            "min_chunk_length": min(chunk_lengths),
            "max_chunk_length": max(chunk_lengths),
            "total_content_length": sum(chunk_lengths)
        }