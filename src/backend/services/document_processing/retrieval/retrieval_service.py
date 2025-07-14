"""
Main retrieval service that orchestrates query processing, hybrid search, and answer generation.
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from ..embedding.vector_storage_service import VectorStorageService
from ..search_engine.elasticsearch_service import ElasticsearchService
from .query_processor import QueryProcessor
from .hybrid_retriever import HybridRetriever, HybridSearchConfig
from .answer_generator import AnswerGenerator


@dataclass
class RetrievalConfig:
    """Configuration for the retrieval service."""
    max_search_results: int = 20
    min_score_threshold: float = 0.1
    vector_weight: float = 0.6
    keyword_weight: float = 0.4
    llm_model: str = "gpt-4"
    llm_temperature: float = 0.1
    enable_reranking: bool = True
    generate_followup_questions: bool = True


@dataclass
class RetrievalResult:
    """Complete result from the retrieval pipeline."""
    query: str
    answer: str
    confidence: float
    citations: List[Dict[str, Any]]
    sources_used: int
    processing_time: float
    query_intent: str
    warnings: List[str]
    followup_questions: List[str]
    search_results: List[Dict[str, Any]]


class RetrievalService:
    """
    Main retrieval service that orchestrates the complete retrieval pipeline.
    Handles query processing, hybrid search, and answer generation.
    """
    
    def __init__(self, 
                 vector_service: VectorStorageService,
                 elasticsearch_service: ElasticsearchService,
                 config: Optional[RetrievalConfig] = None):
        self.vector_service = vector_service
        self.elasticsearch_service = elasticsearch_service
        self.config = config or RetrievalConfig()
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.query_processor = QueryProcessor()
        
        # Configure hybrid retriever
        hybrid_config = HybridSearchConfig(
            vector_weight=self.config.vector_weight,
            keyword_weight=self.config.keyword_weight,
            max_results=self.config.max_search_results,
            min_score_threshold=self.config.min_score_threshold,
            enable_reciprocal_rank_fusion=self.config.enable_reranking
        )
        
        self.hybrid_retriever = HybridRetriever(
            vector_service=vector_service,
            elasticsearch_service=elasticsearch_service,
            query_processor=self.query_processor,
            config=hybrid_config
        )
        
        # Initialize answer generator
        self.answer_generator = AnswerGenerator(
            model_name=self.config.llm_model,
            temperature=self.config.llm_temperature
        )
        
        self.logger.info("Retrieval service initialized successfully")

    async def retrieve_answer(self, 
                            query: str,
                            document_ids: Optional[List[str]] = None) -> RetrievalResult:
        """
        Complete retrieval pipeline: query processing → hybrid search → answer generation.
        
        Args:
            query: User's natural language query
            document_ids: Optional list of document IDs to search within
            
        Returns:
            RetrievalResult with complete answer and metadata
        """
        try:
            import time
            start_time = time.time()
            
            self.logger.info(f"Starting retrieval for query: {query}")
            
            # Step 12: Query Preprocessing
            processed_query = await self.query_processor.process_query(query)
            
            # Step 13: Semantic + Keyword Search
            if self.config.enable_reranking:
                search_results = await self.hybrid_retriever.search_with_reranking(
                    query=query,
                    document_ids=document_ids,
                    max_results=self.config.max_search_results
                )
            else:
                search_results = await self.hybrid_retriever.search(
                    query=query,
                    document_ids=document_ids,
                    max_results=self.config.max_search_results
                )
            
            # Step 14: LLM Answer Generation
            generated_answer = await self.answer_generator.generate_answer(
                query=query,
                search_results=search_results,
                processed_query=processed_query
            )
            
            # Generate follow-up questions if enabled
            followup_questions = []
            if self.config.generate_followup_questions:
                followup_questions = await self.answer_generator.generate_follow_up_questions(
                    query=query,
                    generated_answer=generated_answer
                )
            
            # Calculate total processing time
            total_time = time.time() - start_time
            
            # Create result
            result = RetrievalResult(
                query=query,
                answer=generated_answer.answer,
                confidence=generated_answer.confidence,
                citations=generated_answer.citations,
                sources_used=generated_answer.sources_used,
                processing_time=total_time,
                query_intent=processed_query.intent.value,
                warnings=generated_answer.warnings,
                followup_questions=followup_questions,
                search_results=[
                    {
                        "content": r.content,
                        "score": r.score,
                        "document_id": r.document_id,
                        "chunk_id": r.chunk_id,
                        "source": r.source,
                        "metadata": r.metadata
                    } for r in search_results
                ]
            )
            
            self.logger.info(f"Retrieval completed in {total_time:.2f}s: "
                           f"confidence={result.confidence:.2f}, "
                           f"sources={result.sources_used}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Retrieval failed: {str(e)}")
            
            # Return error result
            return RetrievalResult(
                query=query,
                answer="I apologize, but I encountered an error while processing your query. Please try again.",
                confidence=0.0,
                citations=[],
                sources_used=0,
                processing_time=0.0,
                query_intent="general",
                warnings=["Error occurred during retrieval"],
                followup_questions=[],
                search_results=[]
            )

    async def search_only(self, 
                         query: str,
                         document_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Perform only search without answer generation.
        
        Args:
            query: User's search query
            document_ids: Optional list of document IDs to search within
            
        Returns:
            List of search results
        """
        try:
            search_results = await self.hybrid_retriever.search(
                query=query,
                document_ids=document_ids,
                max_results=self.config.max_search_results
            )
            
            return [
                {
                    "content": r.content,
                    "score": r.score,
                    "document_id": r.document_id,
                    "chunk_id": r.chunk_id,
                    "source": r.source,
                    "metadata": r.metadata,
                    "highlights": r.highlights
                } for r in search_results
            ]
            
        except Exception as e:
            self.logger.error(f"Search failed: {str(e)}")
            return []

    async def get_similar_content(self, 
                                content: str,
                                document_ids: Optional[List[str]] = None,
                                max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Find content similar to the provided text.
        
        Args:
            content: Text to find similar content for
            document_ids: Optional list of document IDs to search within
            max_results: Maximum number of results to return
            
        Returns:
            List of similar content results
        """
        try:
            # Use the content as a query
            search_results = await self.hybrid_retriever.search(
                query=content,
                document_ids=document_ids,
                max_results=max_results
            )
            
            return [
                {
                    "content": r.content,
                    "score": r.score,
                    "document_id": r.document_id,
                    "chunk_id": r.chunk_id,
                    "source": r.source,
                    "metadata": r.metadata
                } for r in search_results
            ]
            
        except Exception as e:
            self.logger.error(f"Similar content search failed: {str(e)}")
            return []

    async def get_document_summary(self, 
                                 document_id: str,
                                 max_chunks: int = 5) -> Dict[str, Any]:
        """
        Get a summary of a specific document.
        
        Args:
            document_id: The document ID to summarize
            max_chunks: Maximum number of chunks to use for summary
            
        Returns:
            Dictionary containing document summary
        """
        try:
            # Search for top chunks from the document
            search_results = await self.hybrid_retriever.search(
                query="summary overview main points",
                document_ids=[document_id],
                max_results=max_chunks
            )
            
            if not search_results:
                return {
                    "document_id": document_id,
                    "summary": "No content found for this document.",
                    "confidence": 0.0,
                    "chunks_used": 0
                }
            
            # Generate summary using answer generator
            summary_query = f"Provide a comprehensive summary of the main points and key provisions in this document."
            
            # Create a mock processed query for summary
            from .query_processor import ProcessedQuery, QueryIntent
            processed_query = ProcessedQuery(
                original_query=summary_query,
                intent=QueryIntent.GENERAL,
                entities=[],
                expanded_terms=[],
                legal_concepts=[],
                search_variations=[],
                confidence=0.8
            )
            
            generated_answer = await self.answer_generator.generate_answer(
                query=summary_query,
                search_results=search_results,
                processed_query=processed_query
            )
            
            return {
                "document_id": document_id,
                "summary": generated_answer.answer,
                "confidence": generated_answer.confidence,
                "chunks_used": len(search_results),
                "citations": generated_answer.citations
            }
            
        except Exception as e:
            self.logger.error(f"Document summary generation failed: {str(e)}")
            return {
                "document_id": document_id,
                "summary": "Error generating document summary.",
                "confidence": 0.0,
                "chunks_used": 0
            }

    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health of all retrieval components.
        
        Returns:
            Dictionary with health status of each component
        """
        try:
            # Check Elasticsearch health
            es_health = await self.elasticsearch_service.health_check()
            
            # Check vector store health (get stats)
            vector_stats = await self.vector_service.get_collection_stats()
            vector_health = len(vector_stats) > 0
            
            # Check search stats
            search_stats = await self.hybrid_retriever.get_search_stats()
            
            return {
                "elasticsearch": {
                    "healthy": es_health,
                    "stats": await self.elasticsearch_service.get_index_stats()
                },
                "vector_store": {
                    "healthy": vector_health,
                    "stats": vector_stats
                },
                "search_service": {
                    "healthy": len(search_stats) > 0,
                    "stats": search_stats
                },
                "overall_health": es_health and vector_health
            }
            
        except Exception as e:
            self.logger.error(f"Health check failed: {str(e)}")
            return {
                "elasticsearch": {"healthy": False},
                "vector_store": {"healthy": False},
                "search_service": {"healthy": False},
                "overall_health": False,
                "error": str(e)
            }

    def update_config(self, config: RetrievalConfig):
        """Update the retrieval configuration."""
        self.config = config
        
        # Update hybrid retriever weights
        self.hybrid_retriever.update_weights(
            vector_weight=config.vector_weight,
            keyword_weight=config.keyword_weight
        )
        
        # Update hybrid retriever config
        self.hybrid_retriever.config.max_results = config.max_search_results
        self.hybrid_retriever.config.min_score_threshold = config.min_score_threshold
        self.hybrid_retriever.config.enable_reciprocal_rank_fusion = config.enable_reranking
        
        self.logger.info("Retrieval configuration updated")

    async def batch_retrieve(self, 
                           queries: List[str],
                           document_ids: Optional[List[str]] = None) -> List[RetrievalResult]:
        """
        Process multiple queries in batch.
        
        Args:
            queries: List of queries to process
            document_ids: Optional list of document IDs to search within
            
        Returns:
            List of RetrievalResult objects
        """
        try:
            # Process queries concurrently
            tasks = [
                self.retrieve_answer(query, document_ids)
                for query in queries
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out exceptions and return successful results
            successful_results = [
                result for result in results
                if isinstance(result, RetrievalResult)
            ]
            
            self.logger.info(f"Batch retrieval completed: {len(successful_results)}/{len(queries)} successful")
            
            return successful_results
            
        except Exception as e:
            self.logger.error(f"Batch retrieval failed: {str(e)}")
            return []