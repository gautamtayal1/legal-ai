import time
import asyncio
from sqlalchemy.orm import Session
from models.document import Document
from core.database import get_db

async def process_document_async(document_id: int):
    """Process document with live status updates"""
    
    # Get database session
    db = next(get_db())
    
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            return
        
        # Step 1: Start processing
        document.processing_status = "processing"
        db.commit()
        await asyncio.sleep(2)  # Simulate work
        
        # Step 2: Extract text
        document.processing_status = "extracting" 
        db.commit()
        await asyncio.sleep(3)  # Simulate extraction
        
        # Step 3: Chunk document
        document.processing_status = "chunking"
        db.commit()
        await asyncio.sleep(2)  # Simulate chunking
        
        # Step 4: Generate embeddings
        document.processing_status = "embedding"
        db.commit()
        await asyncio.sleep(3)  # Simulate embedding generation
        
        # Step 5: Complete
        document.processing_status = "ready"
        db.commit()
        
    except Exception as e:
        # Mark as failed
        document.processing_status = "failed"
        document.error_message = str(e)    
        db.commit()
    finally:
        db.close()

def start_processing_background(document_id: int):
    """Start document processing in background"""
    import threading
    
    def run_async():
        asyncio.run(process_document_async(document_id))
    
    thread = threading.Thread(target=run_async)
    thread.daemon = True
    thread.start() 