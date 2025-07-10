"""
Embedding Generation Services

Handles vector embedding generation for document chunks:
- Text-to-vector conversion using various embedding models
- Batch processing for efficient embedding generation
- Model management and selection
- Embedding quality validation
- Caching for performance optimization
"""

from .base import EmbeddingService
from .openai_embeddings import OpenAIEmbeddingService
from .huggingface_embeddings import HuggingFaceEmbeddingService
from .embedding_cache import EmbeddingCache
from .batch_processor import BatchEmbeddingProcessor

__all__ = [
    "EmbeddingService",
    "OpenAIEmbeddingService",
    "HuggingFaceEmbeddingService", 
    "EmbeddingCache",
    "BatchEmbeddingProcessor"
] 