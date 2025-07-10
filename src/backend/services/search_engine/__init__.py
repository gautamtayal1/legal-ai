"""
Search Engine Service

Main search service that provides unified search capabilities:
- Hybrid search combining semantic and keyword search
- Document retrieval and ranking
- Multi-round search with cross-reference expansion
- Legal-specific search optimizations
- Citation and context management
"""

from ..document_processing.search_indexing import (
    SearchIndexingService,
    ElasticsearchIndexer,
    LegalTextAnalyzer,
    BooleanSearchEngine,
    HybridSearchEngine,
    IndexManager
)

from ..document_processing.vector_store import (
    VectorStoreService,
    SimilaritySearchEngine
)

# Re-export for clean API
__all__ = [
    "SearchIndexingService",
    "ElasticsearchIndexer",
    "LegalTextAnalyzer", 
    "BooleanSearchEngine",
    "HybridSearchEngine",
    "IndexManager",
    "VectorStoreService",
    "SimilaritySearchEngine"
] 