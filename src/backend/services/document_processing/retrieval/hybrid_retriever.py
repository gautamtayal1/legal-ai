"""
Hybrid retrieval service combining vector similarity and keyword search.
Implements Step 13 from architecture: Semantic + Keyword Search
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from langchain.schema import Document
from langchain.retrievers import EnsembleRetriever
from langchain.retrievers.multi_vector import MultiVectorRetriever
from langchain_core.vectorstores import VectorStore
from langchain_core.stores import BaseStore
from langchain_core.retrievers import BaseRetriever
from langchain_openai import OpenAIEmbeddings

from ..embedding.vector_storage_service import VectorStorageService
from ..search_engine.elasticsearch_service import ElasticsearchService
from .query_processor import QueryProcessor, ProcessedQuery


@dataclass
class SearchResult:
    """Represents a search result with score and metadata."""
    content: str
    score: float
    document_id: str
    chunk_id: str
    metadata: Dict[str, Any]
    source: str  # 'vector' or 'keyword' or 'hybrid'
    highlights: Optional[Dict[str, List[str]]] = None


@dataclass
class HybridSearchConfig:
    """Configuration for hybrid search."""
    vector_weight: float = 0.6
    keyword_weight: float = 0.4
    max_results: int = 20
    min_score_threshold: float = 0.1
    rerank_top_k: int = 10
    enable_reciprocal_rank_fusion: bool = True


class LangChainElasticsearchRetriever(BaseRetriever):
    """Custom LangChain retriever for Elasticsearch."""
    
    def __init__(self, elasticsearch_service: ElasticsearchService, k: int = 10):
        super().__init__()
        self.elasticsearch_service = elasticsearch_service
        self.k = k
    
    async def _aget_relevant_documents(self, query: str) -> List[Document]:
        """Get relevant documents from Elasticsearch."""
        results = await self.elasticsearch_service.search_text(query, size=self.k)
        
        documents = []
        for result in results:
            doc = Document(
                page_content=result["content"],
                metadata={
                    **result["metadata"],
                    "score": result["score"],
                    "source": "elasticsearch"
                }
            )
            documents.append(doc)
        
        return documents
    
    def _get_relevant_documents(self, query: str) -> List[Document]:
        """Sync version for compatibility."""
        return asyncio.run(self._aget_relevant_documents(query))


class HybridRetriever:
    """
    Hybrid retrieval service that combines vector similarity search with keyword search.
    Uses LangChain's EnsembleRetriever for optimal result combination.
    """
    
    def __init__(self, 
                 vector_service: VectorStorageService,
                 elasticsearch_service: ElasticsearchService,
                 query_processor: QueryProcessor,
                 config: Optional[HybridSearchConfig] = None):
        self.vector_service = vector_service
        self.elasticsearch_service = elasticsearch_service
        self.query_processor = query_processor
        self.config = config or HybridSearchConfig()
        self.logger = logging.getLogger(__name__)
        
        # Initialize embeddings (should match vector service)
        self.embeddings = OpenAIEmbeddings()
        
        # Create LangChain retrievers
        self.vector_retriever = self.vector_service.vectorstore.as_retriever(
            search_kwargs={"k": self.config.max_results}
        )
        
        self.keyword_retriever = LangChainElasticsearchRetriever(
            elasticsearch_service=self.elasticsearch_service,
            k=self.config.max_results
        )
        
        # Create ensemble retriever
        self.ensemble_retriever = EnsembleRetriever(
            retrievers=[self.vector_retriever, self.keyword_retriever],
            weights=[self.config.vector_weight, self.config.keyword_weight]
        )

    async def search(self, 
                    query: str, 
                    document_ids: Optional[List[str]] = None,
                    max_results: Optional[int] = None) -> List[SearchResult]:
        """
        Perform hybrid search using LangChain's EnsembleRetriever.
        
        Args:
            query: The search query
            document_ids: Optional list of document IDs to filter by
            max_results: Maximum number of results to return
            
        Returns:
            List of SearchResult objects ranked by relevance
        """
        try:
            # Process query for optimization
            processed_query = await self.query_processor.process_query(query)
            
            # Get search strategy
            search_strategy = self.query_processor.get_search_strategy(processed_query)
            
            # Update ensemble weights based on strategy
            if search_strategy["vector_search_weight"] != self.config.vector_weight:
                self.ensemble_retriever.weights = [
                    search_strategy["vector_search_weight"],
                    search_strategy["keyword_search_weight"]
                ]
            
            # Perform ensemble search
            max_results = max_results or self.config.max_results
            
            # Use primary query and search variations
            all_results = []
            
            # Search with main query
            documents = await self.ensemble_retriever.ainvoke(processed_query.original_query)
            all_results.extend(self._convert_documents_to_results(documents, "hybrid"))
            
            # Search with expanded terms for better recall
            for variation in processed_query.search_variations[:3]:  # Limit to top 3 variations
                if variation != processed_query.original_query:
                    var_documents = await self.ensemble_retriever.ainvoke(variation)
                    all_results.extend(self._convert_documents_to_results(var_documents, "hybrid"))
            
            # Remove duplicates and apply filters
            unique_results = self._deduplicate_results(all_results)
            
            # Apply document ID filter if specified
            if document_ids:
                unique_results = [r for r in unique_results if r.document_id in document_ids]
            
            # Apply minimum score threshold
            filtered_results = [
                r for r in unique_results 
                if r.score >= self.config.min_score_threshold
            ]
            
            # Sort by score and limit results
            sorted_results = sorted(filtered_results, key=lambda x: x.score, reverse=True)
            final_results = sorted_results[:max_results]
            
            self.logger.info(f"Hybrid search returned {len(final_results)} results for query: {query}")
            
            return final_results
            
        except Exception as e:
            self.logger.error(f"Hybrid search failed: {str(e)}")
            return []

    async def search_with_reranking(self,
                                   query: str,
                                   document_ids: Optional[List[str]] = None,
                                   max_results: Optional[int] = None) -> List[SearchResult]:
        """
        Perform hybrid search with reciprocal rank fusion reranking.
        
        Args:
            query: The search query
            document_ids: Optional list of document IDs to filter by
            max_results: Maximum number of results to return
            
        Returns:
            List of SearchResult objects with improved ranking
        """
        try:
            # Get separate results from both retrievers
            vector_results = await self._vector_search(query, document_ids)
            keyword_results = await self._keyword_search(query, document_ids)
            
            # Apply reciprocal rank fusion
            if self.config.enable_reciprocal_rank_fusion:
                fused_results = self._reciprocal_rank_fusion(vector_results, keyword_results)
            else:
                # Simple weighted combination
                fused_results = self._weighted_combination(vector_results, keyword_results)
            
            # Apply filters and limits
            max_results = max_results or self.config.max_results
            filtered_results = [
                r for r in fused_results 
                if r.score >= self.config.min_score_threshold
            ]
            
            final_results = filtered_results[:max_results]
            
            self.logger.info(f"Reranked search returned {len(final_results)} results for query: {query}")
            
            return final_results
            
        except Exception as e:
            self.logger.error(f"Reranked search failed: {str(e)}")
            return []

    async def _vector_search(self, query: str, document_ids: Optional[List[str]] = None) -> List[SearchResult]:
        """Perform vector similarity search."""
        try:
            # Get query embedding
            query_embedding = await self.embeddings.aembed_query(query)
            
            # Search vector database
            vector_results = await self.vector_service.search_similar(
                query_embedding=query_embedding,
                n_results=self.config.max_results,
                document_id=document_ids[0] if document_ids and len(document_ids) == 1 else None
            )
            
            # Convert to SearchResult objects
            search_results = []
            for result in vector_results:
                search_result = SearchResult(
                    content=result["content"],
                    score=result["similarity"],
                    document_id=result["metadata"].get("document_id", ""),
                    chunk_id=result["id"],
                    metadata=result["metadata"],
                    source="vector"
                )
                search_results.append(search_result)
            
            return search_results
            
        except Exception as e:
            self.logger.error(f"Vector search failed: {str(e)}")
            return []

    async def _keyword_search(self, query: str, document_ids: Optional[List[str]] = None) -> List[SearchResult]:
        """Perform keyword search using Elasticsearch."""
        try:
            # Search Elasticsearch
            es_results = await self.elasticsearch_service.search_text(
                query=query,
                size=self.config.max_results,
                document_id=document_ids[0] if document_ids and len(document_ids) == 1 else None
            )
            
            # Convert to SearchResult objects
            search_results = []
            for result in es_results:
                search_result = SearchResult(
                    content=result["content"],
                    score=result["score"] / 100.0,  # Normalize ES score
                    document_id=result["metadata"].get("document_id", ""),
                    chunk_id=result["id"],
                    metadata=result["metadata"],
                    source="keyword",
                    highlights=result.get("highlights", {})
                )
                search_results.append(search_result)
            
            return search_results
            
        except Exception as e:
            self.logger.error(f"Keyword search failed: {str(e)}")
            return []

    def _convert_documents_to_results(self, documents: List[Document], source: str) -> List[SearchResult]:
        """Convert LangChain documents to SearchResult objects."""
        results = []
        
        for doc in documents:
            result = SearchResult(
                content=doc.page_content,
                score=doc.metadata.get("score", 0.0),
                document_id=doc.metadata.get("document_id", ""),
                chunk_id=doc.metadata.get("chunk_id", ""),
                metadata=doc.metadata,
                source=source
            )
            results.append(result)
        
        return results

    def _deduplicate_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """Remove duplicate results based on chunk_id."""
        seen_ids = set()
        unique_results = []
        
        for result in results:
            if result.chunk_id not in seen_ids:
                seen_ids.add(result.chunk_id)
                unique_results.append(result)
        
        return unique_results

    def _reciprocal_rank_fusion(self, 
                              vector_results: List[SearchResult], 
                              keyword_results: List[SearchResult],
                              k: int = 60) -> List[SearchResult]:
        """
        Apply reciprocal rank fusion to combine results from different sources.
        
        Args:
            vector_results: Results from vector search
            keyword_results: Results from keyword search
            k: Parameter for RRF (typically 60)
            
        Returns:
            Fused and ranked results
        """
        # Create rank maps
        vector_ranks = {result.chunk_id: i + 1 for i, result in enumerate(vector_results)}
        keyword_ranks = {result.chunk_id: i + 1 for i, result in enumerate(keyword_results)}
        
        # Combine all unique results
        all_results = {}
        for result in vector_results + keyword_results:
            if result.chunk_id not in all_results:
                all_results[result.chunk_id] = result
        
        # Calculate RRF scores
        for chunk_id, result in all_results.items():
            rrf_score = 0.0
            
            # Add vector score
            if chunk_id in vector_ranks:
                rrf_score += 1.0 / (k + vector_ranks[chunk_id])
            
            # Add keyword score
            if chunk_id in keyword_ranks:
                rrf_score += 1.0 / (k + keyword_ranks[chunk_id])
            
            # Update result score
            result.score = rrf_score
            result.source = "hybrid"
        
        # Sort by RRF score
        return sorted(all_results.values(), key=lambda x: x.score, reverse=True)

    def _weighted_combination(self, 
                            vector_results: List[SearchResult], 
                            keyword_results: List[SearchResult]) -> List[SearchResult]:
        """
        Combine results using weighted scores.
        
        Args:
            vector_results: Results from vector search
            keyword_results: Results from keyword search
            
        Returns:
            Combined and ranked results
        """
        # Create score maps
        vector_scores = {result.chunk_id: result.score for result in vector_results}
        keyword_scores = {result.chunk_id: result.score for result in keyword_results}
        
        # Combine all unique results
        all_results = {}
        for result in vector_results + keyword_results:
            if result.chunk_id not in all_results:
                all_results[result.chunk_id] = result
        
        # Calculate weighted scores
        for chunk_id, result in all_results.items():
            weighted_score = 0.0
            
            # Add weighted vector score
            if chunk_id in vector_scores:
                weighted_score += self.config.vector_weight * vector_scores[chunk_id]
            
            # Add weighted keyword score
            if chunk_id in keyword_scores:
                weighted_score += self.config.keyword_weight * keyword_scores[chunk_id]
            
            # Update result score
            result.score = weighted_score
            result.source = "hybrid"
        
        # Sort by weighted score
        return sorted(all_results.values(), key=lambda x: x.score, reverse=True)

    def update_weights(self, vector_weight: float, keyword_weight: float):
        """Update the weights for vector and keyword search."""
        self.config.vector_weight = vector_weight
        self.config.keyword_weight = keyword_weight
        
        # Update ensemble retriever weights
        self.ensemble_retriever.weights = [vector_weight, keyword_weight]
        
        self.logger.info(f"Updated search weights: vector={vector_weight}, keyword={keyword_weight}")

    async def get_search_stats(self) -> Dict[str, Any]:
        """Get statistics about the search indices."""
        try:
            # Get vector store stats
            vector_stats = await self.vector_service.get_collection_stats()
            
            # Get Elasticsearch stats
            es_stats = await self.elasticsearch_service.get_index_stats()
            
            return {
                "vector_store": vector_stats,
                "elasticsearch": es_stats,
                "config": {
                    "vector_weight": self.config.vector_weight,
                    "keyword_weight": self.config.keyword_weight,
                    "max_results": self.config.max_results,
                    "min_score_threshold": self.config.min_score_threshold
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get search stats: {str(e)}")
            return {}