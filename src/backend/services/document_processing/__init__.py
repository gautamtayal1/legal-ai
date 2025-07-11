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

from .text_extraction import TextExtractionService, extract_text, extract_text_batch, is_supported, ExtractionResult
from .embedding import EmbeddingService, EmbeddingConfig, VectorStorageService, VectorStorageConfig
from .search_engine import ElasticsearchService, ElasticsearchConfig

__all__ = [
    # Text extraction
    "TextExtractionService",
    "extract_text", 
    "extract_text_batch",
    "is_supported",
    "ExtractionResult",
    
    # Embedding services
    "EmbeddingService",
    "EmbeddingConfig",
    "VectorStorageService", 
    "VectorStorageConfig",
    
    # Search engine
    "ElasticsearchService",
    "ElasticsearchConfig"
] 