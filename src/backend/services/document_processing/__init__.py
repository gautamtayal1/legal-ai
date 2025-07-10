"""
Document Processing Services

This module contains all services related to document processing including:
- Text extraction from various file formats
- Document structure analysis
- Legal content extraction
- Intelligent chunking
- Embedding generation
- Vector database operations
- Search indexing

The processing pipeline is designed to handle legal documents with high accuracy
and proper citation tracking.
"""

from .pipeline import DocumentProcessingPipeline
from .text_extraction import TextExtractionService
from .structure_analysis import StructureAnalysisService
from .legal_extraction import LegalContentExtractor
from .chunking import LegalChunkingService
from .embedding import EmbeddingService
from .vector_store import VectorStoreService
from .search_indexing import SearchIndexingService

__all__ = [
    "DocumentProcessingPipeline",
    "TextExtractionService", 
    "StructureAnalysisService",
    "LegalContentExtractor",
    "LegalChunkingService",
    "EmbeddingService",
    "VectorStoreService",
    "SearchIndexingService"
] 