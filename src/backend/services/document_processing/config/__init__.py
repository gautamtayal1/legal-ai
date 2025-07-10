"""
Document Processing Configuration

Configuration management for all document processing services:
- Service-specific settings (embedding models, vector DB connections)
- Processing parameters (chunk sizes, overlap, etc.)
- API keys and credentials management
- Environment-specific configurations
- Feature flags and experimental settings
"""

from .base import ProcessingConfig
from .embedding_config import EmbeddingConfig
from .vector_store_config import VectorStoreConfig
from .search_config import SearchConfig
from .chunking_config import ChunkingConfig
from .extraction_config import ExtractionConfig

__all__ = [
    "ProcessingConfig",
    "EmbeddingConfig",
    "VectorStoreConfig",
    "SearchConfig",
    "ChunkingConfig",
    "ExtractionConfig"
] 