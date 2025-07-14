"""
API endpoints for document query and retrieval functionality.
Implements the retrieval API for Steps 12-14 from architecture.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from core.database import get_db
from models.document import Document, ProcessingStatus
from services.document_processing.retrieval.retrieval_service import RetrievalService, RetrievalConfig
from services.document_processing.embedding.vector_storage_service import VectorStorageService
from services.document_processing.search_engine.elasticsearch_service import ElasticsearchService
import logging
import asyncio

router = APIRouter(
    prefix="/query",
    tags=["query"],
)

logger = logging.getLogger(__name__)

# Pydantic models for request/response
class QueryRequest(BaseModel):
    query: str = Field(..., description="The user's natural language query")
    document_ids: Optional[List[str]] = Field(None, description="Optional list of document IDs to search within")
    max_results: Optional[int] = Field(20, description="Maximum number of results to return")
    include_followup: Optional[bool] = Field(True, description="Whether to generate follow-up questions")

class SearchRequest(BaseModel):
    query: str = Field(..., description="The search query")
    document_ids: Optional[List[str]] = Field(None, description="Optional list of document IDs to search within")
    max_results: Optional[int] = Field(20, description="Maximum number of results to return")

class SimilarContentRequest(BaseModel):
    content: str = Field(..., description="Text content to find similar chunks for")
    document_ids: Optional[List[str]] = Field(None, description="Optional list of document IDs to search within")
    max_results: Optional[int] = Field(10, description="Maximum number of results to return")

class BatchQueryRequest(BaseModel):
    queries: List[str] = Field(..., description="List of queries to process")
    document_ids: Optional[List[str]] = Field(None, description="Optional list of document IDs to search within")

class QueryResponse(BaseModel):
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

class SearchResponse(BaseModel):
    results: List[Dict[str, Any]]
    total_results: int
    processing_time: float

class HealthResponse(BaseModel):
    elasticsearch: Dict[str, Any]
    vector_store: Dict[str, Any]
    search_service: Dict[str, Any]
    overall_health: bool

# Global retrieval service instance
_retrieval_service = None

async def get_retrieval_service() -> RetrievalService:
    """Get or create the retrieval service instance."""
    global _retrieval_service
    
    if _retrieval_service is None:
        try:
            # Initialize services
            vector_service = VectorStorageService()
            elasticsearch_service = ElasticsearchService()
            
            # Create retrieval service
            _retrieval_service = RetrievalService(
                vector_service=vector_service,
                elasticsearch_service=elasticsearch_service
            )
            
            logger.info("Retrieval service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize retrieval service: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to initialize retrieval service")
    
    return _retrieval_service

@router.post("/ask", response_model=QueryResponse)
async def ask_question(
    request: QueryRequest,
    db: Session = Depends(get_db),
    retrieval_service: RetrievalService = Depends(get_retrieval_service)
):
    """
    Ask a natural language question about legal documents.
    
    This endpoint implements the complete retrieval pipeline:
    - Step 12: Query preprocessing
    - Step 13: Semantic + keyword search
    - Step 14: LLM answer generation
    """
    try:
        # Validate document IDs if provided
        if request.document_ids:
            doc_ids = [int(doc_id) for doc_id in request.document_ids]
            documents = db.query(Document).filter(
                Document.id.in_(doc_ids),
                Document.processing_status == ProcessingStatus.READY
            ).all()
            
            if len(documents) != len(doc_ids):
                raise HTTPException(
                    status_code=400,
                    detail="Some documents not found or not ready for querying"
                )
        
        # Update retrieval config if needed
        if request.max_results != 20:
            config = RetrievalConfig(
                max_search_results=request.max_results,
                generate_followup_questions=request.include_followup
            )
            retrieval_service.update_config(config)
        
        # Perform retrieval
        result = await retrieval_service.retrieve_answer(
            query=request.query,
            document_ids=request.document_ids
        )
        
        # Convert to response model
        response = QueryResponse(
            query=result.query,
            answer=result.answer,
            confidence=result.confidence,
            citations=result.citations,
            sources_used=result.sources_used,
            processing_time=result.processing_time,
            query_intent=result.query_intent,
            warnings=result.warnings,
            followup_questions=result.followup_questions,
            search_results=result.search_results
        )
        
        logger.info(f"Question answered successfully: {request.query[:50]}...")
        
        return response
        
    except Exception as e:
        logger.error(f"Question answering failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to answer question: {str(e)}")

@router.post("/search", response_model=SearchResponse)
async def search_documents(
    request: SearchRequest,
    db: Session = Depends(get_db),
    retrieval_service: RetrievalService = Depends(get_retrieval_service)
):
    """
    Search for relevant content in legal documents without answer generation.
    
    This endpoint performs hybrid search (semantic + keyword) and returns
    ranked results with highlights and metadata.
    """
    try:
        import time
        start_time = time.time()
        
        # Validate document IDs if provided
        if request.document_ids:
            doc_ids = [int(doc_id) for doc_id in request.document_ids]
            documents = db.query(Document).filter(
                Document.id.in_(doc_ids),
                Document.processing_status == ProcessingStatus.READY
            ).all()
            
            if len(documents) != len(doc_ids):
                raise HTTPException(
                    status_code=400,
                    detail="Some documents not found or not ready for searching"
                )
        
        # Perform search
        search_results = await retrieval_service.search_only(
            query=request.query,
            document_ids=request.document_ids
        )
        
        # Apply max results limit
        if request.max_results and len(search_results) > request.max_results:
            search_results = search_results[:request.max_results]
        
        processing_time = time.time() - start_time
        
        response = SearchResponse(
            results=search_results,
            total_results=len(search_results),
            processing_time=processing_time
        )
        
        logger.info(f"Search completed: {request.query[:50]}... -> {len(search_results)} results")
        
        return response
        
    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.post("/similar")
async def find_similar_content(
    request: SimilarContentRequest,
    db: Session = Depends(get_db),
    retrieval_service: RetrievalService = Depends(get_retrieval_service)
):
    """
    Find content similar to the provided text.
    
    This endpoint uses vector similarity search to find chunks
    that are semantically similar to the input content.
    """
    try:
        # Validate document IDs if provided
        if request.document_ids:
            doc_ids = [int(doc_id) for doc_id in request.document_ids]
            documents = db.query(Document).filter(
                Document.id.in_(doc_ids),
                Document.processing_status == ProcessingStatus.READY
            ).all()
            
            if len(documents) != len(doc_ids):
                raise HTTPException(
                    status_code=400,
                    detail="Some documents not found or not ready for searching"
                )
        
        # Find similar content
        similar_results = await retrieval_service.get_similar_content(
            content=request.content,
            document_ids=request.document_ids,
            max_results=request.max_results
        )
        
        logger.info(f"Similar content search completed: {len(similar_results)} results")
        
        return {
            "similar_content": similar_results,
            "total_results": len(similar_results)
        }
        
    except Exception as e:
        logger.error(f"Similar content search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Similar content search failed: {str(e)}")

@router.get("/document/{document_id}/summary")
async def get_document_summary(
    document_id: str,
    db: Session = Depends(get_db),
    retrieval_service: RetrievalService = Depends(get_retrieval_service)
):
    """
    Get an AI-generated summary of a specific document.
    
    This endpoint analyzes the document content and generates
    a comprehensive summary of key points and provisions.
    """
    try:
        # Validate document exists and is ready
        doc_id = int(document_id)
        document = db.query(Document).filter(
            Document.id == doc_id,
            Document.processing_status == ProcessingStatus.READY
        ).first()
        
        if not document:
            raise HTTPException(
                status_code=404,
                detail="Document not found or not ready for summarization"
            )
        
        # Generate summary
        summary_result = await retrieval_service.get_document_summary(
            document_id=document_id
        )
        
        logger.info(f"Document summary generated for document {document_id}")
        
        return summary_result
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document ID")
    except Exception as e:
        logger.error(f"Document summary generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Summary generation failed: {str(e)}")

@router.post("/batch", response_model=List[QueryResponse])
async def batch_query(
    request: BatchQueryRequest,
    db: Session = Depends(get_db),
    retrieval_service: RetrievalService = Depends(get_retrieval_service)
):
    """
    Process multiple queries in batch for efficiency.
    
    This endpoint allows processing multiple questions simultaneously,
    which can be more efficient than individual requests.
    """
    try:
        # Validate document IDs if provided
        if request.document_ids:
            doc_ids = [int(doc_id) for doc_id in request.document_ids]
            documents = db.query(Document).filter(
                Document.id.in_(doc_ids),
                Document.processing_status == ProcessingStatus.READY
            ).all()
            
            if len(documents) != len(doc_ids):
                raise HTTPException(
                    status_code=400,
                    detail="Some documents not found or not ready for querying"
                )
        
        # Process queries in batch
        results = await retrieval_service.batch_retrieve(
            queries=request.queries,
            document_ids=request.document_ids
        )
        
        # Convert to response models
        responses = [
            QueryResponse(
                query=result.query,
                answer=result.answer,
                confidence=result.confidence,
                citations=result.citations,
                sources_used=result.sources_used,
                processing_time=result.processing_time,
                query_intent=result.query_intent,
                warnings=result.warnings,
                followup_questions=result.followup_questions,
                search_results=result.search_results
            )
            for result in results
        ]
        
        logger.info(f"Batch query completed: {len(responses)}/{len(request.queries)} successful")
        
        return responses
        
    except Exception as e:
        logger.error(f"Batch query failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Batch query failed: {str(e)}")

@router.get("/health", response_model=HealthResponse)
async def health_check(
    retrieval_service: RetrievalService = Depends(get_retrieval_service)
):
    """
    Check the health of all retrieval components.
    
    This endpoint provides status information about:
    - Elasticsearch service
    - Vector database service
    - Search service overall health
    """
    try:
        health_info = await retrieval_service.health_check()
        
        response = HealthResponse(
            elasticsearch=health_info["elasticsearch"],
            vector_store=health_info["vector_store"],
            search_service=health_info["search_service"],
            overall_health=health_info["overall_health"]
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@router.get("/stats")
async def get_retrieval_stats(
    retrieval_service: RetrievalService = Depends(get_retrieval_service)
):
    """
    Get statistics about the retrieval system.
    
    This endpoint provides information about:
    - Total documents indexed
    - Vector store statistics
    - Elasticsearch index statistics
    - Search performance metrics
    """
    try:
        stats = await retrieval_service.hybrid_retriever.get_search_stats()
        
        logger.info("Retrieval statistics retrieved successfully")
        
        return {
            "retrieval_stats": stats,
            "status": "healthy" if stats else "unhealthy"
        }
        
    except Exception as e:
        logger.error(f"Failed to get retrieval stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

@router.put("/config")
async def update_retrieval_config(
    vector_weight: float = Query(0.6, description="Weight for vector search (0.0-1.0)"),
    keyword_weight: float = Query(0.4, description="Weight for keyword search (0.0-1.0)"),
    max_results: int = Query(20, description="Maximum results to return"),
    enable_reranking: bool = Query(True, description="Enable reciprocal rank fusion"),
    retrieval_service: RetrievalService = Depends(get_retrieval_service)
):
    """
    Update retrieval configuration parameters.
    
    This endpoint allows fine-tuning of the retrieval system:
    - Adjust vector vs keyword search weights
    - Set maximum result limits
    - Enable/disable result reranking
    """
    try:
        # Validate weights
        if abs(vector_weight + keyword_weight - 1.0) > 0.01:
            raise HTTPException(
                status_code=400,
                detail="Vector weight and keyword weight must sum to 1.0"
            )
        
        # Update configuration
        config = RetrievalConfig(
            vector_weight=vector_weight,
            keyword_weight=keyword_weight,
            max_search_results=max_results,
            enable_reranking=enable_reranking
        )
        
        retrieval_service.update_config(config)
        
        logger.info(f"Retrieval configuration updated: vector_weight={vector_weight}, "
                   f"keyword_weight={keyword_weight}, max_results={max_results}")
        
        return {
            "message": "Configuration updated successfully",
            "config": {
                "vector_weight": vector_weight,
                "keyword_weight": keyword_weight,
                "max_results": max_results,
                "enable_reranking": enable_reranking
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to update retrieval config: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Config update failed: {str(e)}")