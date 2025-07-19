
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from core.database import get_db
from models.document import Document, ProcessingStatus
from models.message import Message
from models.thread import Thread
from services.document_processing.retrieval import RetrievalService, RetrievalConfig
from services.document_processing.embedding.vector_storage_service import VectorStorageService
from services.document_processing.search_engine.elasticsearch_service import ElasticsearchService
import logging
import asyncio
import uuid
from fastapi.responses import StreamingResponse

router = APIRouter(
    prefix="/query",
    tags=["query"],
)

logger = logging.getLogger(__name__)

def _convert_search_results_to_dict(search_results):
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

_retrieval_service = None

async def get_retrieval_service() -> RetrievalService:
    global _retrieval_service
    
    if _retrieval_service is None:
        try:
            vector_service = VectorStorageService()
            elasticsearch_service = ElasticsearchService()
            
            _retrieval_service = RetrievalService(
                vector_service=vector_service,
                elasticsearch_service=elasticsearch_service
            )
            
            logger.info("Retrieval service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize retrieval service: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to initialize retrieval service")
    
    return _retrieval_service

@router.post("/stream")
async def ask_question(
    request: dict,
    db: Session = Depends(get_db),
    retrieval_service: RetrievalService = Depends(get_retrieval_service)
):
    try:
        query = None
        thread_id = None
        user_id = None
        
        if 'messages' in request:
            messages = request['messages']
            if messages:
                query = messages[-1].get('content', '')
            thread_id = request.get('thread_id')
            user_id = request.get('user_id')
        elif 'query' in request:
            query = request['query']
            thread_id = request.get('thread_id')
            user_id = request.get('user_id')
        
        if not query:
            raise HTTPException(status_code=400, detail="No query found in request")
        
        if not thread_id:
            raise HTTPException(status_code=400, detail="No thread_id found in request")
            
        if not user_id:
            raise HTTPException(status_code=400, detail="No user_id found in request")
        
        thread = db.query(Thread).filter(
            Thread.id == thread_id,
            Thread.user_id == user_id
        ).first()
        
        if not thread:
            raise HTTPException(status_code=404, detail="Thread not found")
        
        user_message = Message(
            id=str(uuid.uuid4()),
            thread_id=thread_id,
            user_id=user_id,
            content=query,
            role="user"
        )
        
        db.add(user_message)
        db.commit()
        db.refresh(user_message)
        
        documents = db.query(Document).filter(
            Document.thread_id == thread_id,
            Document.processing_status == ProcessingStatus.READY
        ).all()
        
        if not documents:
            raise HTTPException(
                status_code=400,
                detail="No ready documents found for this thread"
            )
        
        doc_ids = [str(doc.id) for doc in documents]
        logger.info(f"Found {len(documents)} ready documents for thread {thread_id}: {doc_ids}")
        
        assistant_response = ""
        
        async def generate_stream():
            nonlocal assistant_response
            try:
                processed_query = retrieval_service.query_processor.process_query(query)
                
                search_results = await retrieval_service._hybrid_search(processed_query, doc_ids)
                logger.info(f"Retrieved {len(search_results)} search results for query: {query}")
                
                async for chunk in retrieval_service._generate_answer(processed_query, search_results):
                    if chunk:
                        assistant_response += chunk
                        yield chunk
                        await asyncio.sleep(0)
                
                if assistant_response:
                    assistant_message = Message(
                        id=str(uuid.uuid4()),
                        thread_id=thread_id,
                        user_id=user_id,
                        content=assistant_response,
                        role="assistant"
                    )
                    
                    db.add(assistant_message)
                    db.commit()
                    
            except Exception as e:
                logger.error(f"Streaming failed: {str(e)}")
                yield f"Error: {str(e)}"
        
        logger.info(f"Question answered successfully: {query[:50]}...")
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain; charset=utf-8",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization",
            }
        )
        
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
    try:
        if abs(vector_weight + keyword_weight - 1.0) > 0.01:
            raise HTTPException(
                status_code=400,
                detail="Vector weight and keyword weight must sum to 1.0"
            )
        
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