"""
Search Indexing Services

Manages full-text search indexing and retrieval:
- Elasticsearch indexing and search operations
- Legal-specific text analysis and tokenization
- Boolean and fuzzy search capabilities
- Index optimization for legal documents
- Hybrid search combining keyword and semantic results
"""

from .base import SearchIndexingService
from .elasticsearch_indexer import ElasticsearchIndexer
from .legal_analyzer import LegalTextAnalyzer
from .boolean_search import BooleanSearchEngine
from .hybrid_search import HybridSearchEngine
from .index_manager import IndexManager

__all__ = [
    "SearchIndexingService",
    "ElasticsearchIndexer",
    "LegalTextAnalyzer",
    "BooleanSearchEngine", 
    "HybridSearchEngine",
    "IndexManager"
] 