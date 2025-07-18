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
from services.document_processing.retrieval import RetrievalService, RetrievalConfig
from services.document_processing.embedding.vector_storage_service import VectorStorageService
from services.document_processing.search_engine.elasticsearch_service import ElasticsearchService
import logging
import asyncio

router = APIRouter(
    prefix="/query",
    tags=["query"],
)

logger = logging.getLogger(__name__)

def _convert_search_results_to_dict(search_results):
    """Helper function to convert SearchResult objects to dictionaries"""
    results_dict = []
    for result in search_results:
        results_dict.append({
            "id": result.id,
            "content": result.content,
            "metadata": result.metadata,
            "similarity_score": result.similarity_score,
            "keyword_score": result.keyword_score,
            "combined_score": result.combined_score,
            "highlights": result.highlights or {}
        })
    return results_dict

def _convert_similar_results_to_dict(search_results):
    """Helper function to convert SearchResult objects to dictionaries for similar content"""
    results_dict = []
    for result in search_results:
        results_dict.append({
            "id": result.id,
            "content": result.content,
            "metadata": result.metadata,
            "similarity_score": result.similarity_score,
            "combined_score": result.combined_score
        })
    return results_dict

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
    sources_used: List[str]
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

@router.post("", response_model=QueryResponse)
async def ask_question(
    request: QueryRequest,
    db: Session = Depends(get_db),
    retrieval_service: RetrievalService = Depends(get_retrieval_service)
):
    """
    Ask a natural language question about legal documents.
    """
    try:
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
        
        if request.max_results != 20:
            config = RetrievalConfig(
                max_search_results=request.max_results,
                generate_followup_questions=request.include_followup
            )
            retrieval_service.update_config(config)
        
        result = await retrieval_service.retrieve_answer(
            query=request.query,
            document_ids=request.document_ids
        )
        
        search_results_dict = _convert_search_results_to_dict(result.search_results)
        
        response = QueryResponse(
            query=result.query,
            answer=result.answer,
            confidence=result.confidence,
            sources_used=result.sources_used,
            processing_time=result.processing_time,
            query_intent=result.query_intent,
            warnings=result.warnings,
            followup_questions=result.followup_questions,
            search_results=search_results_dict
        )
        
        logger.info(f"Question answered successfully: {request.query[:50]}...")
        
        db.add(Message(
            query=request.query,
            answer=result.answer,
            confidence=result.confidence,
            sources_used=result.sources_used,
            processing_time=result.processing_time,
        ))
        return response
        
    except Exception as e:
        logger.error(f"Question answering failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to answer question: {str(e)}")

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