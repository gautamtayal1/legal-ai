from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, Form, Query
from sqlalchemy.orm import Session
from core.database import get_db
from models.thread import Thread
from pydantic import BaseModel
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(
    prefix="/threads",
    tags=["threads"],
)

class ThreadCreate(BaseModel):
    id: str
    user_id: str
    title: str

class ThreadUpdate(BaseModel):
    title: str

class ThreadAutoName(BaseModel):
    thread_id: str
    user_id: str

@router.get("")
async def list_threads(db: Session = Depends(get_db)):
    """Get all threads from the database."""
    threads = db.query(Thread).all()
    return [
        {
            "id": thread.id,
            "title": thread.title,
            "created_at": thread.created_at,
            "updated_at": thread.updated_at
        }
        for thread in threads
    ]

@router.post("")
async def create_thread(thread_data: ThreadCreate, db: Session = Depends(get_db)):
    """Create a new thread."""
    thread = Thread(
        id=thread_data.id, 
        user_id=thread_data.user_id, 
        title=thread_data.title
    )
    db.add(thread)
    db.commit()
    db.refresh(thread)
    return thread
    
@router.get("/{user_id}")
async def get_thread_by_user_id(user_id: str, db: Session = Depends(get_db)):
    """Get all threads for a specific user."""
    threads = db.query(Thread).filter(Thread.user_id == user_id).all()
    if not threads:
        raise HTTPException(status_code=404, detail="No threads found for this user")
    return threads

@router.put("/{thread_id}")
async def update_thread(thread_id: str, thread_update: ThreadUpdate, user_id: str = Query(...), db: Session = Depends(get_db)):
    """Update a thread's title."""
    thread = db.query(Thread).filter(
        Thread.id == thread_id,
        Thread.user_id == user_id
    ).first()
    
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    thread.title = thread_update.title
    db.commit()
    db.refresh(thread)
    return thread

@router.delete("/{thread_id}")
async def delete_thread(thread_id: str, user_id: str = Query(...), db: Session = Depends(get_db)):
    """Delete a thread and all its associated data."""
    thread = db.query(Thread).filter(
        Thread.id == thread_id,
        Thread.user_id == user_id
    ).first()
    
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    # Delete the thread (cascade should handle related data)
    db.delete(thread)
    db.commit()
    return {"message": "Thread deleted successfully"}

@router.post("/{thread_id}/auto-name")
async def auto_name_thread(thread_id: str, user_id: str = Query(...), db: Session = Depends(get_db)):
    """Auto-generate a name for a thread based on its documents."""
    from models.document import Document
    from services.document_processing.retrieval.retrieval_service import RetrievalService
    from services.document_processing.embedding.vector_storage_service import VectorStorageService
    from services.document_processing.search_engine.elasticsearch_service import ElasticsearchService
    import openai
    
    # Verify thread exists and user has access
    thread = db.query(Thread).filter(
        Thread.id == thread_id,
        Thread.user_id == user_id
    ).first()
    
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    # Get documents for this thread
    documents = db.query(Document).filter(
        Document.thread_id == thread_id,
        Document.processing_status == "ready"
    ).all()
    
    if not documents:
        raise HTTPException(status_code=400, detail="No ready documents found for this thread")
    
    try:
        # Get document summaries/content using retrieval service
        vector_service = VectorStorageService()
        es_service = ElasticsearchService()
        retrieval_service = RetrievalService(vector_service, es_service)
        
        # Get sample content from documents
        doc_ids = [str(doc.id) for doc in documents]
        sample_query = retrieval_service.query_processor.process_query("What is this document about?")
        search_results = await retrieval_service._hybrid_search(sample_query, doc_ids)
        
        # Prepare content for naming
        content_summary = ""
        for result in search_results[:3]:  # Use top 3 results
            content_summary += result.content[:200] + "... "
        
        # Get document filenames for context
        doc_names = [doc.filename for doc in documents]
        
        # Generate name using OpenAI
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that creates short, descriptive names for document collections. Generate a 2-4 word name that captures the main topic or purpose of the documents."
                },
                {
                    "role": "user",
                    "content": f"Create a 2-4 word name for a document collection containing these files: {', '.join(doc_names)}. Sample content: {content_summary}. The name should be concise and professional."
                }
            ],
            max_tokens=20,
            temperature=0.3
        )
        
        suggested_name = response.choices[0].message.content.strip()
        
        # Update thread title
        thread.title = suggested_name
        db.commit()
        db.refresh(thread)
        
        return {"message": "Thread name updated successfully", "new_name": suggested_name}
        
    except Exception as e:
        # Fallback to a generic name based on document count
        if len(documents) == 1:
            fallback_name = f"Document Analysis"
        else:
            fallback_name = f"{len(documents)} Documents"
        
        thread.title = fallback_name
        db.commit()
        db.refresh(thread)
        
        return {"message": "Thread name updated with fallback", "new_name": fallback_name}