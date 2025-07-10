"""
Embeddings Service

Main embeddings service that coordinates with document processing:
- Provides high-level embedding API for the application
- Manages embedding models and caching
- Interfaces with document processing embedding services
- Handles batch processing and optimization
"""

from ..document_processing.embedding import (
    EmbeddingService,
    OpenAIEmbeddingService,
    HuggingFaceEmbeddingService,
    EmbeddingCache,
    BatchEmbeddingProcessor
)

# Re-export for backwards compatibility and clean API
__all__ = [
    "EmbeddingService",
    "OpenAIEmbeddingService", 
    "HuggingFaceEmbeddingService",
    "EmbeddingCache",
    "BatchEmbeddingProcessor"
] 