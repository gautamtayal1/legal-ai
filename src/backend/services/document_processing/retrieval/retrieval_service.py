import os
import asyncio
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import openai

from .query_processor import QueryProcessor, ProcessedQuery
from ..embedding.embedding_service import EmbeddingService
from ..embedding.vector_storage_service import VectorStorageService
from ..search_engine.elasticsearch_service import ElasticsearchService

@dataclass
class RetrievalConfig:
    vector_weight: float = 0.6
    keyword_weight: float = 0.4
    max_search_results: int = 20
    max_context_chunks: int = 10
    openai_model: str = "gpt-4o-mini"
    max_tokens: int = 2000
    temperature: float = 0.1


@dataclass 
class SearchResult:
    id: str
    content: str
    metadata: Dict[str, Any]
    score: float = 0.0
    highlights: Dict[str, List[str]] = None


@dataclass
class RetrievalResult:
    query: str
    answer: str
    sources_used: List[str]
    processing_time: float
    query_intent: str
    warnings: List[str]
    search_results: List[SearchResult]


class RetrievalService:
    def __init__(self, 
                 vector_service: VectorStorageService,
                 elasticsearch_service: ElasticsearchService,
                 config: Optional[RetrievalConfig] = None):
        
        self.config = config or RetrievalConfig()
        self.logger = logging.getLogger(__name__)
        
        # Services
        self.vector_service = vector_service
        self.elasticsearch_service = elasticsearch_service
        self.query_processor = QueryProcessor()
        
        # Initialize embedding service for query embedding
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
            
        self.embedding_service = EmbeddingService(openai_api_key)
        
        # Initialize OpenAI client for answer generation
        openai.api_key = openai_api_key
        self.openai_client = openai.OpenAI(api_key=openai_api_key)
        
        self.logger.info("RetrievalService initialized successfully")
    
    async def retrieve_answer(self, 
                            query: str, 
                            document_ids: Optional[List[str]] = None) -> RetrievalResult:
        """
        Args:
            query: User's natural language question
            document_ids: Optional list of document IDs to search within
            
        Returns:
            RetrievalResult with answer, and metadata
        """
        start_time = datetime.now()
        warnings = []
        
        try:
            self.logger.info(f"Step 12: Processing query: {query[:100]}...")
            processed_query = self.query_processor.process_query(query)
            
            self.logger.info("Step 13: Performing hybrid search...")
            search_results = await self._hybrid_search(processed_query, document_ids)
            
            if not search_results:
                warnings.append("No relevant content found for this query")
                return self._create_empty_result(query, processed_query, warnings, start_time)
            
            self.logger.info("Step 14: Generating answer with LLM...")
            answer = await self._generate_answer(
                processed_query, search_results
            )
            
            self.logger.info("Step 15: Formatting response...")
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return RetrievalResult(
                query=query,
                answer=answer,
                sources_used=list(set(r.metadata.get('document_id', '') for r in search_results)),
                processing_time=processing_time,
                query_intent=processed_query.intent.value,
                warnings=warnings,
                search_results=search_results[:self.config.max_context_chunks]
            )
            
        except Exception as e:
            self.logger.error(f"Retrieval failed: {str(e)}")
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return RetrievalResult(
                query=query,
                answer=f"I encountered an error while processing your question: {str(e)}",
                sources_used=[],
                processing_time=processing_time,
                query_intent="error",
                warnings=[f"Error: {str(e)}"],
                search_results=[]
            )
    
    
    
    async def _generate_answer(self, 
                             processed_query: ProcessedQuery, 
                             search_results: List[SearchResult]) -> str:
        """
        Generate answer using LLM with retrieved context.
        
        """
        try:
            context_pieces = []
            
            for i, result in enumerate(search_results[:self.config.max_context_chunks], 1):
                context_pieces.append(f"[{i}] {result.content}")
            
            context = "\n\n".join(context_pieces)
            
            prompt = self._create_answer_prompt(processed_query, context)
            
            response = self.openai_client.chat.completions.create(
                model=self.config.openai_model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt(processed_query.intent)},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                stream=True
            )
            
            for chunk in response:
                delta = chunk.choices[0].delta.content
                if delta:
                    # Add flush to ensure immediate streaming
                    yield delta
                    await asyncio.sleep(0)  # Allow other tasks to run
            
        except Exception as e:
            self.logger.error(f"Answer generation failed: {str(e)}")
            yield f"I apologize, but I encountered an error generating an answer: {str(e)}"
    
    async def _hybrid_search(self, 
                           processed_query: ProcessedQuery, 
                           document_ids: Optional[List[str]] = None) -> List[SearchResult]:
        """Perform hybrid search combining vector similarity and keyword matching"""
        try:
            query_embedding = await self.embedding_service.embed_query(
                processed_query.processed_query
            )
            
            filters = None
            if document_ids and len(document_ids) == 1:
                filters = {"document_id": document_ids[0]}
            
            vector_results, keyword_results = await asyncio.gather(
                self.vector_service.search_similar(
                    query_embedding=query_embedding,
                    n_results=self.config.max_search_results,
                    filters=filters
                ),
                self.elasticsearch_service.search_text(
                    query=processed_query.processed_query,
                    size=self.config.max_search_results,
                    document_id=document_ids[0] if document_ids and len(document_ids) == 1 else None,
                    filters=filters if not document_ids else None
                )
            )
            
            search_results = []
            
            # Process vector results and filter by document_ids if needed
            for result in vector_results:
                # If we have multiple document IDs, filter here
                if document_ids and len(document_ids) > 1:
                    result_doc_id = result.get("metadata", {}).get("document_id")
                    if result_doc_id not in document_ids:
                        continue
                
                search_result = SearchResult(
                    id=result.get("id", ""),
                    content=result.get("content", ""),
                    metadata=result.get("metadata", {}),
                    score=result.get("similarity", 0.0)
                )
                search_results.append(search_result)
            
            keyword_dict = {r.get("id", ""): r for r in keyword_results}
            
            for search_result in search_results:
                if search_result.id in keyword_dict:
                    keyword_result = keyword_dict[search_result.id]
                    keyword_score = keyword_result.get("score", 0.0)
                    search_result.highlights = keyword_result.get("highlights", {}) 
                    normalized_vector = min(1.0, search_result.score)
                    normalized_keyword = min(1.0, keyword_score / 10.0) if keyword_score > 0 else 0.0
                    search_result.score = (
                        normalized_vector * self.config.vector_weight +
                        normalized_keyword * self.config.keyword_weight
                    )
                    del keyword_dict[search_result.id]
            
            for keyword_result in keyword_dict.values():
                # Filter by document_ids if needed
                if document_ids and len(document_ids) > 1:
                    result_doc_id = keyword_result.get("metadata", {}).get("document_id")
                    if result_doc_id not in document_ids:
                        continue
                
                keyword_score = keyword_result.get("score", 0.0)
                normalized_keyword = min(1.0, keyword_score / 10.0) if keyword_score > 0 else 0.0
                search_result = SearchResult(
                    id=keyword_result.get("id", ""),
                    content=keyword_result.get("content", ""),
                    metadata=keyword_result.get("metadata", {}),
                    score=normalized_keyword * self.config.keyword_weight,
                    highlights=keyword_result.get("highlights", {})
                )
                search_results.append(search_result)
            
            search_results.sort(key=lambda x: x.score, reverse=True)
            
            self.logger.info(f"Hybrid search returned {len(search_results)} results")
            return search_results[:self.config.max_context_chunks]
            
        except Exception as e:
            self.logger.error(f"Hybrid search failed: {str(e)}")
            return []
    
    def _create_answer_prompt(self, processed_query: ProcessedQuery, context: str) -> str:
        return f"""Based on the following legal document context, please answer the user's question accurately and comprehensively.

User's Question: {processed_query.original_query}

Query Intent: {processed_query.intent.value}

Legal Context:
{context}

Instructions:
1. Answer based ONLY on the provided context
2. If the context doesn't contain enough information, say so clearly
3. For legal queries, be precise and provide clear explanations
4. If there are conflicting information, mention the discrepancy
5. Keep the answer concise but complete

Answer:"""
    
    def _get_system_prompt(self, intent) -> str:
        """Get system prompt based on query intent"""
        base_prompt = """You are Inquire, a legal AI assistant helping users understand legal documents. You provide accurate answers based on the provided document context."""
        
        intent_specific = {
            "definition": " Focus on providing clear definitions and explanations of terms.",
            "obligation": " Focus on identifying who must do what, under what conditions, and by when. Be very specific about obligations and responsibilities.",
            "timeline": " Focus on deadlines, time periods, and temporal requirements. Be precise about dates and timeframes.",
            "party": " Focus on identifying the parties involved and their roles in the agreement.",
            "termination": " Focus on termination conditions, notice requirements, and procedures for ending the agreement.",
            "payment": " Focus on payment terms, amounts, schedules, and financial obligations.",
            "liability": " Focus on liability provisions, indemnification, and risk allocation between parties."
        }
        
        return base_prompt + intent_specific.get(intent.value, " Provide comprehensive, clear answers.")
    
    
    
    def _create_empty_result(self, 
                           query: str, 
                           processed_query: ProcessedQuery, 
                           warnings: List[str], 
                           start_time: datetime) -> RetrievalResult:
        """Create an empty result when no content is found"""
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return RetrievalResult(
            query=query,
            answer="I couldn't find relevant information in the available documents to answer your question. Please try rephrasing your question or ensure the relevant documents have been uploaded and processed.",
            citations=[],
            sources_used=[],
            processing_time=processing_time,
            query_intent=processed_query.intent.value,
            warnings=warnings,
            search_results=[]
        )
    
    async def search_only(self, 
                        query: str, 
                        document_ids: Optional[List[str]] = None) -> List[SearchResult]:
        """
        Perform search without answer generation.
        Returns raw search results for the search endpoint.
        """
        processed_query = self.query_processor.process_query(query)
        return await self._hybrid_search(processed_query, document_ids)
    
    
    
    def update_config(self, config: RetrievalConfig):
        """Update retrieval configuration"""
        self.config = config
        self.logger.info("Retrieval configuration updated")
    
