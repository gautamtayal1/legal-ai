 """
Retrieval Service - Steps 12-15: Complete Retrieval Pipeline

Implements:
- Step 12: Query Preprocessing
- Step 13: Semantic + Keyword Search  
- Step 14: LLM Answer Generation
- Step 15: Response Formatting

Uses LangChain where possible while maintaining customization.
"""
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
    enable_reranking: bool = True
    generate_followup_questions: bool = True
    openai_model: str = "gpt-4o-mini"
    max_tokens: int = 1000
    temperature: float = 0.1


@dataclass 
class SearchResult:
    id: str
    content: str
    metadata: Dict[str, Any]
    similarity_score: float = 0.0
    keyword_score: float = 0.0
    combined_score: float = 0.0
    highlights: Dict[str, List[str]] = None


@dataclass
class RetrievalResult:
    query: str
    answer: str
    confidence: float
    citations: List[Dict[str, Any]]
    sources_used: List[str]
    processing_time: float
    query_intent: str
    warnings: List[str]
    followup_questions: List[str]
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
        Main retrieval method implementing the complete pipeline (Steps 12-15).
        
        Args:
            query: User's natural language question
            document_ids: Optional list of document IDs to search within
            
        Returns:
            RetrievalResult with answer, citations, and metadata
        """
        start_time = datetime.now()
        warnings = []
        
        try:
            # Step 12: Query Preprocessing
            self.logger.info(f"Step 12: Processing query: {query[:100]}...")
            processed_query = self.query_processor.process_query(query)
            
            # Step 13: Semantic + Keyword Search
            self.logger.info("Step 13: Performing hybrid search...")
            search_results = await self._hybrid_search(processed_query, document_ids)
            
            if not search_results:
                warnings.append("No relevant content found for this query")
                return self._create_empty_result(query, processed_query, warnings, start_time)
            
            # Step 14: LLM Answer Generation
            self.logger.info("Step 14: Generating answer with LLM...")
            answer, confidence, citations = await self._generate_answer(
                processed_query, search_results
            )
            
            # Step 15: Response Formatting
            self.logger.info("Step 15: Formatting response...")
            followup_questions = []
            if self.config.generate_followup_questions:
                followup_questions = await self._generate_followup_questions(
                    processed_query, answer
                )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return RetrievalResult(
                query=query,
                answer=answer,
                confidence=confidence,
                citations=citations,
                sources_used=list(set(r.metadata.get('document_id', '') for r in search_results)),
                processing_time=processing_time,
                query_intent=processed_query.intent.value,
                warnings=warnings,
                followup_questions=followup_questions,
                search_results=search_results[:self.config.max_context_chunks]
            )
            
        except Exception as e:
            self.logger.error(f"Retrieval failed: {str(e)}")
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return RetrievalResult(
                query=query,
                answer=f"I encountered an error while processing your question: {str(e)}",
                confidence=0.0,
                citations=[],
                sources_used=[],
                processing_time=processing_time,
                query_intent="error",
                warnings=[f"Error: {str(e)}"],
                followup_questions=[],
                search_results=[]
            )
    
    async def _hybrid_search(self, 
                           processed_query: ProcessedQuery, 
                           document_ids: Optional[List[str]] = None) -> List[SearchResult]:
        """
        Perform hybrid search combining vector similarity and keyword matching.
        
        This implements Step 13: Semantic + Keyword Search from the architecture.
        """
        try:
            # Convert query to embedding for vector search
            query_embedding = await self.embedding_service.embed_query(
                processed_query.processed_query
            )
            
            # Prepare search filters
            filters = {}
            if document_ids:
                filters["document_id"] = {"$in": document_ids}
            
            # Run searches in parallel
            vector_results, keyword_results = await asyncio.gather(
                # Vector/semantic search
                self.vector_service.search_similar(
                    query_embedding=query_embedding,
                    n_results=self.config.max_search_results,
                    filters=filters
                ),
                # Keyword search
                self.elasticsearch_service.search_text(
                    query=processed_query.processed_query,
                    size=self.config.max_search_results,
                    document_id=document_ids[0] if document_ids and len(document_ids) == 1 else None,
                    filters=filters if not document_ids else None
                )
            )
            
            # Convert results to SearchResult objects
            search_results = []
            
            # Process vector results
            for result in vector_results:
                search_result = SearchResult(
                    id=result.get("id", ""),
                    content=result.get("content", ""),
                    metadata=result.get("metadata", {}),
                    similarity_score=result.get("similarity", 0.0),
                    keyword_score=0.0
                )
                search_results.append(search_result)
            
            # Process keyword results and merge with vector results
            keyword_dict = {r.get("id", ""): r for r in keyword_results}
            
            for search_result in search_results:
                if search_result.id in keyword_dict:
                    keyword_result = keyword_dict[search_result.id]
                    search_result.keyword_score = keyword_result.get("score", 0.0)
                    search_result.highlights = keyword_result.get("highlights", {})
                    # Remove from keyword dict to avoid duplicates
                    del keyword_dict[search_result.id]
            
            # Add remaining keyword-only results
            for keyword_result in keyword_dict.values():
                search_result = SearchResult(
                    id=keyword_result.get("id", ""),
                    content=keyword_result.get("content", ""),
                    metadata=keyword_result.get("metadata", {}),
                    similarity_score=0.0,
                    keyword_score=keyword_result.get("score", 0.0),
                    highlights=keyword_result.get("highlights", {})
                )
                search_results.append(search_result)
            
            # Calculate combined scores and rank
            for result in search_results:
                # Normalize scores (simple min-max normalization)
                normalized_vector = min(1.0, result.similarity_score)
                normalized_keyword = min(1.0, result.keyword_score / 10.0) if result.keyword_score > 0 else 0.0
                
                result.combined_score = (
                    normalized_vector * self.config.vector_weight +
                    normalized_keyword * self.config.keyword_weight
                )
            
            # Sort by combined score
            search_results.sort(key=lambda x: x.combined_score, reverse=True)
            
            # Apply reranking if enabled
            if self.config.enable_reranking:
                search_results = self._reciprocal_rank_fusion(search_results)
            
            self.logger.info(f"Hybrid search returned {len(search_results)} results")
            return search_results[:self.config.max_context_chunks]
            
        except Exception as e:
            self.logger.error(f"Hybrid search failed: {str(e)}")
            return []
    
    def _reciprocal_rank_fusion(self, results: List[SearchResult]) -> List[SearchResult]:
        """Apply reciprocal rank fusion for better ranking"""
        k = 60  # RRF parameter
        
        # Create separate rankings for vector and keyword scores
        vector_ranked = sorted(results, key=lambda x: x.similarity_score, reverse=True)
        keyword_ranked = sorted(results, key=lambda x: x.keyword_score, reverse=True)
        
        # Calculate RRF scores
        rrf_scores = {}
        
        for rank, result in enumerate(vector_ranked, 1):
            if result.id not in rrf_scores:
                rrf_scores[result.id] = 0
            rrf_scores[result.id] += 1 / (k + rank)
        
        for rank, result in enumerate(keyword_ranked, 1):
            if result.id not in rrf_scores:
                rrf_scores[result.id] = 0
            rrf_scores[result.id] += 1 / (k + rank)
        
        # Update combined scores with RRF
        for result in results:
            result.combined_score = rrf_scores.get(result.id, 0)
        
        # Re-sort by RRF score
        return sorted(results, key=lambda x: x.combined_score, reverse=True)
    
    async def _generate_answer(self, 
                             processed_query: ProcessedQuery, 
                             search_results: List[SearchResult]) -> tuple[str, float, List[Dict[str, Any]]]:
        """
        Generate answer using LLM with retrieved context.
        
        This implements Step 14: LLM Answer Generation from the architecture.
        """
        try:
            # Prepare context from search results
            context_pieces = []
            citations = []
            
            for i, result in enumerate(search_results[:self.config.max_context_chunks], 1):
                context_pieces.append(f"[{i}] {result.content}")
                citations.append({
                    "id": result.id,
                    "content": result.content[:200] + "..." if len(result.content) > 200 else result.content,
                    "metadata": result.metadata,
                    "score": result.combined_score,
                    "citation_number": i
                })
            
            context = "\n\n".join(context_pieces)
            
            # Create prompt based on query intent
            prompt = self._create_answer_prompt(processed_query, context)
            
            # Generate answer with OpenAI
            response = await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: self.openai_client.chat.completions.create(
                    model=self.config.openai_model,
                    messages=[
                        {"role": "system", "content": self._get_system_prompt(processed_query.intent)},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=self.config.max_tokens,
                    temperature=self.config.temperature
                )
            )
            
            answer = response.choices[0].message.content
            
            # Calculate confidence based on context quality and LLM response
            confidence = self._calculate_answer_confidence(processed_query, search_results, answer)
            
            return answer, confidence, citations
            
        except Exception as e:
            self.logger.error(f"Answer generation failed: {str(e)}")
            return f"I apologize, but I encountered an error generating an answer: {str(e)}", 0.0, []
    
    def _create_answer_prompt(self, processed_query: ProcessedQuery, context: str) -> str:
        """Create a tailored prompt for answer generation"""
        return f"""Based on the following legal document context, please answer the user's question accurately and comprehensively.

User's Question: {processed_query.original_query}

Query Intent: {processed_query.intent.value}

Legal Context:
{context}

Instructions:
1. Answer based ONLY on the provided context
2. Include specific citations using [number] format
3. If the context doesn't contain enough information, say so clearly
4. For legal queries, be precise and cite specific sections when possible
5. If there are conflicting information, mention the discrepancy
6. Keep the answer concise but complete

Answer:"""
    
    def _get_system_prompt(self, intent) -> str:
        """Get system prompt based on query intent"""
        base_prompt = """You are a legal AI assistant helping users understand legal documents. You provide accurate, well-cited answers based on the provided document context."""
        
        intent_specific = {
            "definition": " Focus on providing clear definitions with exact references to where terms are defined in the documents.",
            "obligation": " Focus on identifying who must do what, under what conditions, and by when. Be very specific about obligations and responsibilities.",
            "timeline": " Focus on deadlines, time periods, and temporal requirements. Be precise about dates and timeframes.",
            "party": " Focus on identifying the parties involved and their roles in the agreement.",
            "termination": " Focus on termination conditions, notice requirements, and procedures for ending the agreement.",
            "payment": " Focus on payment terms, amounts, schedules, and financial obligations.",
            "liability": " Focus on liability provisions, indemnification, and risk allocation between parties."
        }
        
        return base_prompt + intent_specific.get(intent.value, " Provide comprehensive, well-cited answers.")
    
    def _calculate_answer_confidence(self, 
                                   processed_query: ProcessedQuery, 
                                   search_results: List[SearchResult], 
                                   answer: str) -> float:
        """Calculate confidence score for the generated answer"""
        confidence = 0.5  # Base confidence
        
        # Boost based on query processing confidence
        confidence += processed_query.metadata.get('confidence', 0.5) * 0.2
        
        # Boost based on search result quality
        if search_results:
            avg_score = sum(r.combined_score for r in search_results) / len(search_results)
            confidence += min(0.3, avg_score)
        
        # Boost based on answer characteristics
        if "[" in answer and "]" in answer:  # Has citations
            confidence += 0.1
        
        if len(answer) > 100:  # Substantial answer
            confidence += 0.1
        
        if "I don't have enough information" not in answer.lower():
            confidence += 0.1
        
        return min(1.0, confidence)
    
    async def _generate_followup_questions(self, 
                                         processed_query: ProcessedQuery, 
                                         answer: str) -> List[str]:
        """Generate relevant followup questions"""
        try:
            followup_prompt = f"""Based on this legal question and answer, suggest 3 relevant followup questions a user might want to ask.

Original Question: {processed_query.original_query}
Answer: {answer[:500]}...

Generate 3 specific, actionable followup questions that would help the user understand related aspects of their legal document:

1."""
            
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": followup_prompt}],
                    max_tokens=150,
                    temperature=0.3
                )
            )
            
            followup_text = response.choices[0].message.content
            # Parse the numbered questions
            questions = []
            for line in followup_text.split('\n'):
                if line.strip() and any(line.strip().startswith(f"{i}.") for i in range(1, 10)):
                    question = line.split('.', 1)[1].strip()
                    if question:
                        questions.append(question)
            
            return questions[:3]
            
        except Exception as e:
            self.logger.error(f"Followup generation failed: {str(e)}")
            return []
    
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
            confidence=0.0,
            citations=[],
            sources_used=[],
            processing_time=processing_time,
            query_intent=processed_query.intent.value,
            warnings=warnings,
            followup_questions=[],
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
    
    async def get_similar_content(self, 
                                content: str, 
                                document_ids: Optional[List[str]] = None,
                                max_results: int = 10) -> List[SearchResult]:
        """
        Find content similar to the provided text.
        """
        try:
            embedding = await self.embedding_service.embed_query(content)
            
            filters = {}
            if document_ids:
                filters["document_id"] = {"$in": document_ids}
            
            results = await self.vector_service.search_similar(
                query_embedding=embedding,
                n_results=max_results,
                filters=filters
            )
            
            search_results = []
            for result in results:
                search_results.append(SearchResult(
                    id=result.get("id", ""),
                    content=result.get("content", ""),
                    metadata=result.get("metadata", {}),
                    similarity_score=result.get("similarity", 0.0),
                    combined_score=result.get("similarity", 0.0)
                ))
            
            return search_results
            
        except Exception as e:
            self.logger.error(f"Similar content search failed: {str(e)}")
            return []
    
    async def batch_retrieve(self, 
                           queries: List[str], 
                           document_ids: Optional[List[str]] = None) -> List[RetrievalResult]:
        """
        Process multiple queries efficiently.
        """
        tasks = [self.retrieve_answer(query, document_ids) for query in queries]
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    def update_config(self, config: RetrievalConfig):
        """Update retrieval configuration"""
        self.config = config
        self.logger.info("Retrieval configuration updated")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of all retrieval components"""
        health = {
            "retrieval_service": True,
            "vector_storage": False,
            "elasticsearch": False,
            "openai": False
        }
        
        try:
            # Check vector storage
            stats = await self.vector_storage.get_collection_stats()
            health["vector_storage"] = bool(stats)
        except:
            pass
        
        try:
            # Check Elasticsearch
            es_health = await self.elasticsearch_service.health_check()
            health["elasticsearch"] = es_health
        except:
            pass
        
        try:
            # Check OpenAI
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": "test"}],
                    max_tokens=1
                )
            )
            health["openai"] = True
        except:
            pass
        
        return health