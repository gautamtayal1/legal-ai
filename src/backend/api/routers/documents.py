from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...models.document import Document
from ...services.s3_service import upload_file

router = APIRouter(
    prefix="/documents",
    tags=["documents"],
)

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
            "message_id": doc.message_id,
            "user_id": doc.user_id,
            "uploaded_at": doc.uploaded_at
        }
        for doc in documents
    ]

@router.post("/upload")
async def upload_document(
    message_id: str,
    user_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload a document to S3 and save metadata to database."""
    
    # Validate file type
    allowed_types = {
        "application/pdf": "pdf",
        "text/plain": "txt",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
        "application/msword": "doc"
    }
    
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400, 
            detail=f"File type {file.content_type} not supported. Allowed types: {list(allowed_types.keys())}"
        )
    
    # Read file content
    file_content = await file.read()
    file_size = len(file_content)
    
    # Validate file size (10MB limit)
    if file_size > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds 10MB limit")
    
    try:
        # Upload to S3
        s3_key, s3_url = upload_file(file_content, file.filename)
        
        # Save metadata to database
        document = Document(
            document_url=s3_url,
            filename=file.filename,
            file_type=allowed_types[file.content_type],
            file_size=file_size,
            message_id=message_id,
            user_id=user_id
        )
        
        db.add(document)
        db.commit()
        db.refresh(document)
        
        return {
            "id": document.id,
            "filename": document.filename,
            "file_type": document.file_type,
            "file_size": document.file_size,
            "document_url": document.document_url,
            "uploaded_at": document.uploaded_at,
            "s3_key": s3_key
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/{doc_id}")
async def get_document(doc_id: str):
    """Fetch single document placeholder"""
    raise HTTPException(status_code=404, detail="Document not found")
