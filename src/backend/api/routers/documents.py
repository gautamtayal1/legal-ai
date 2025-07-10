from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, Form
from sqlalchemy.orm import Session
from core.database import get_db
from models.document import Document, ProcessingStatus
from services.s3_service import upload_file
from services.document_processing import start_processing_background
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(
    prefix="/documents",
    tags=["documents"],
)
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
AWS_REGION = os.getenv("AWS_REGION")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

@router.get("/")
async def list_documents(db: Session = Depends(get_db)):
    """Get all documents from the database."""
    documents = db.query(Document).all()
    return [
        {
            "id": doc.id,
            "filename": doc.filename,
            "file_type": doc.file_type,
            "file_size": doc.file_size,
            "document_url": doc.document_url,
            "thread_id": doc.thread_id,
            "user_id": doc.user_id,
            "uploaded_at": doc.uploaded_at,
            "processing_status": doc.processing_status
        }
        for doc in documents
    ]

import logging

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    thread_id: str = Form(...),
    user_id: str = Form(...),
    db: Session = Depends(get_db)
):
    """Upload a document to S3 and save metadata to database."""
    logging.debug(f"Received upload request: filename={file.filename}, content_type={file.content_type}, thread_id={thread_id}, user_id={user_id}")

    # Validate file type
    allowed_types = {
        "application/pdf": "pdf",
        "text/plain": "txt",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
        "application/msword": "doc"
    }
    
    if file.content_type not in allowed_types:
        logging.warning(f"Rejected file upload: unsupported type {file.content_type}")
        raise HTTPException(
            status_code=400, 
            detail=f"File type {file.content_type} not supported. Allowed types: {list(allowed_types.keys())}"
        )
        
    file_content = await file.read()
    file_size = len(file_content)
    logging.debug(f"File size: {file_size} bytes")

    if file_size > 10 * 1024 * 1024:
        logging.warning(f"Rejected file upload: file size {file_size} exceeds 10MB limit")
        raise HTTPException(status_code=400, detail="File size exceeds 10MB limit")
    
    try:
        logging.info(f"Uploading file '{file.filename}' to S3...")
        s3_key, s3_url = upload_file(file_content, file.filename)
        logging.info(f"File uploaded to S3: key={s3_key}, url={s3_url}")
        
        document = Document(
            document_url=s3_url,
            filename=file.filename,
            file_type=allowed_types[file.content_type],
            file_size=file_size,
            thread_id=thread_id,
            user_id=user_id,
            processing_status=ProcessingStatus.PENDING,
        )
        
        db.add(document)
        db.commit()
        db.refresh(document)
        logging.info(f"Document metadata saved to DB: id={document.id}")

        # Start background processing
        logging.info(f"Starting background processing for document id={document.id}")
        start_processing_background(document.id)
        
        response = {
            "id": document.id,
            "filename": document.filename,
            "file_type": document.file_type,
            "file_size": document.file_size,
            "document_url": document.document_url,
            "uploaded_at": document.uploaded_at,
            "processing_status": document.processing_status,
            "s3_key": s3_key
        }
        logging.debug(f"Upload response: {response}")
        return response
        
    except Exception as e:
        db.rollback()
        logging.error(f"Upload failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/{doc_id}")
async def get_document(doc_id: str):
    """Fetch single document placeholder"""
    raise HTTPException(status_code=404, detail="Document not found")

@router.get("/{doc_id}/status")
async def get_document_status(doc_id: int, db: Session = Depends(get_db)):
    """Get document processing status for live updates"""
    document = db.query(Document).filter(Document.id == doc_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {
        "id": document.id,
        "processing_status": document.processing_status,
        "error_message": document.error_message,
        "is_ready": document.processing_status == "ready"
    }
