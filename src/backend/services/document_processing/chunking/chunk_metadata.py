from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import json
import hashlib

from .base import DocumentChunk


@dataclass
class ChunkMetadata:
    document_id: str
    chunk_id: str
    chunk_index: int
    content_hash: str
    created_at: datetime
    chunk_size: int
    chunk_type: str
    chunking_method: str
    
    # Content analysis
    word_count: int
    sentence_count: int
    paragraph_count: int
    
    # Legal-specific metadata
    contains_definitions: bool = False
    contains_obligations: bool = False
    contains_parties: bool = False
    contains_dates: bool = False
    contains_amounts: bool = False
    contains_references: bool = False
    
    # Position and context
    start_position: int = 0
    end_position: int = 0
    parent_section: Optional[str] = None
    section_level: int = 0
    
    # Quality metrics
    readability_score: Optional[float] = None
    coherence_score: Optional[float] = None
    legal_complexity_score: Optional[float] = None
    
    # Relationships
    related_chunks: List[str] = None
    cross_references: List[str] = None
    
    # Additional metadata
    custom_metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.related_chunks is None:
            self.related_chunks = []
        if self.cross_references is None:
            self.cross_references = []
        if self.custom_metadata is None:
            self.custom_metadata = {}


class ChunkMetadataManager:
    def __init__(self):
        self.metadata_cache: Dict[str, ChunkMetadata] = {}
    
    def create_metadata(self, chunk: DocumentChunk, additional_metadata: Optional[Dict[str, Any]] = None) -> ChunkMetadata:
        content_hash = self._calculate_content_hash(chunk.content)
        
        word_count = len(chunk.content.split())
        sentence_count = len([s for s in chunk.content.split('.') if s.strip()])
        paragraph_count = len([p for p in chunk.content.split('\n\n') if p.strip()])
        
        metadata = ChunkMetadata(
            document_id=chunk.document_id,
            chunk_id=chunk.id,
            chunk_index=chunk.chunk_index,
            content_hash=content_hash,
            created_at=datetime.utcnow(),
            chunk_size=len(chunk.content),
            chunk_type=chunk.metadata.get("chunk_type", "unknown"),
            chunking_method=chunk.metadata.get("chunking_method", "unknown"),
            word_count=word_count,
            sentence_count=sentence_count,
            paragraph_count=paragraph_count,
            start_position=chunk.start_position,
            end_position=chunk.end_position,
            parent_section=chunk.parent_section,
            contains_definitions=chunk.metadata.get("contains_definitions", False),
            contains_obligations=chunk.metadata.get("contains_obligations", False),
            contains_parties=chunk.metadata.get("contains_parties", False),
            contains_dates=self._contains_dates(chunk.content),
            contains_amounts=self._contains_amounts(chunk.content),
            contains_references=chunk.metadata.get("contains_references", False),
            custom_metadata=additional_metadata or {}
        )
        
        if chunk.legal_context:
            metadata.legal_complexity_score = self._calculate_legal_complexity(chunk.legal_context)
        
        self.metadata_cache[chunk.id] = metadata
        return metadata
    
    def _calculate_content_hash(self, content: str) -> str:
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def _contains_dates(self, content: str) -> bool:
        import re
        date_patterns = [
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
            r'\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{2,4}\b',
            r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{2,4}\b'
        ]
        
        for pattern in date_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True
        return False
    
    def _contains_amounts(self, content: str) -> bool:
        import re
        amount_patterns = [
            r'\$[\d,]+(?:\.\d{2})?',
            r'(?:\d{1,3}(?:,\d{3})*|\d+)(?:\.\d{2})?\s*(?:dollars?|USD|cents?)',
            r'(?:\d{1,3}(?:,\d{3})*|\d+)\s*(?:million|billion|thousand)',
        ]
        
        for pattern in amount_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True
        return False
    
    def _calculate_legal_complexity(self, legal_context: Dict[str, Any]) -> float:
        score = (len(legal_context.get("definitions", [])) * 0.3 + 
                bool(legal_context.get("obligations", False)) * 2 +
                len(legal_context.get("parties", [])) * 0.2 + 
                len(legal_context.get("references", [])) * 0.1)
        return min(score, 10.0)
    
    def update_metadata(self, chunk_id: str, updates: Dict[str, Any]) -> Optional[ChunkMetadata]:
        if chunk_id not in self.metadata_cache:
            return None
        
        metadata = self.metadata_cache[chunk_id]
        
        for key, value in updates.items():
            if hasattr(metadata, key):
                setattr(metadata, key, value)
            else:
                metadata.custom_metadata[key] = value
        
        return metadata
    
    def get_metadata(self, chunk_id: str) -> Optional[ChunkMetadata]:
        return self.metadata_cache.get(chunk_id)
    
    def get_chunks_by_criteria(self, criteria: Dict[str, Any]) -> List[ChunkMetadata]:
        matching_chunks = []
        
        for metadata in self.metadata_cache.values():
            if self._matches_criteria(metadata, criteria):
                matching_chunks.append(metadata)
        
        return matching_chunks
    
    def _matches_criteria(self, metadata: ChunkMetadata, criteria: Dict[str, Any]) -> bool:
        for key, value in criteria.items():
            if key == "min_word_count":
                if metadata.word_count < value:
                    return False
            elif key == "max_word_count":
                if metadata.word_count > value:
                    return False
            elif key == "chunk_type":
                if metadata.chunk_type != value:
                    return False
            elif key == "contains_definitions":
                if metadata.contains_definitions != value:
                    return False
            elif key == "contains_obligations":
                if metadata.contains_obligations != value:
                    return False
            elif key == "parent_section":
                if metadata.parent_section != value:
                    return False
            elif key == "min_legal_complexity":
                if (metadata.legal_complexity_score or 0) < value:
                    return False
            elif hasattr(metadata, key):
                if getattr(metadata, key) != value:
                    return False
        
        return True
    
    def export_metadata(self, chunk_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        if chunk_ids is None:
            chunk_ids = list(self.metadata_cache.keys())
        
        export_data = {}
        for chunk_id in chunk_ids:
            if chunk_id in self.metadata_cache:
                metadata = self.metadata_cache[chunk_id]
                export_data[chunk_id] = {
                    **asdict(metadata),
                    "created_at": metadata.created_at.isoformat()
                }
        
        return export_data
    
    def import_metadata(self, metadata_data: Dict[str, Any]) -> None:
        for chunk_id, data in metadata_data.items():
            if "created_at" in data:
                data["created_at"] = datetime.fromisoformat(data["created_at"])
            
            metadata = ChunkMetadata(**data)
            self.metadata_cache[chunk_id] = metadata
    
    def generate_chunk_summary(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        metadata = self.get_metadata(chunk_id)
        if not metadata:
            return None
        
        return {
            "chunk_id": chunk_id,
            "document_id": metadata.document_id,
            "chunk_index": metadata.chunk_index,
            "chunk_type": metadata.chunk_type,
            "size_info": {
                "chunk_size": metadata.chunk_size,
                "word_count": metadata.word_count,
                "sentence_count": metadata.sentence_count,
                "paragraph_count": metadata.paragraph_count
            },
            "content_flags": {
                "contains_definitions": metadata.contains_definitions,
                "contains_obligations": metadata.contains_obligations,
                "contains_parties": metadata.contains_parties,
                "contains_dates": metadata.contains_dates,
                "contains_amounts": metadata.contains_amounts,
                "contains_references": metadata.contains_references
            },
            "quality_metrics": {
                "legal_complexity_score": metadata.legal_complexity_score,
                "readability_score": metadata.readability_score,
                "coherence_score": metadata.coherence_score
            },
            "relationships": {
                "related_chunks": len(metadata.related_chunks),
                "cross_references": len(metadata.cross_references)
            }
        }