"""
Document Chunking Services

Intelligent chunking specifically designed for legal documents:
- Semantic chunking that preserves legal meaning
- Section-aware chunking that respects document structure
- Overlap management for context preservation
- Legal-specific tokenization and splitting
- Metadata preservation for citations
"""

from .base import LegalChunkingService
from .semantic_chunker import SemanticChunker
from .legal_chunker import LegalDocumentChunker
from .overlap_manager import OverlapManager
from .chunk_metadata import ChunkMetadataManager

__all__ = [
    "LegalChunkingService",
    "SemanticChunker",
    "LegalDocumentChunker",
    "OverlapManager",
    "ChunkMetadataManager"
] 