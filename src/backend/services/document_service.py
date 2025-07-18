import logging
import os
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from .document_pipeline import DocumentPipeline
from .document_processing.text_extraction import extract_text
from .document_processing.text_processing import process_text
from models.document import Document, ProcessingStatus
from utils.s3_service import download_file
from core.database import get_db

logger = logging.getLogger(__name__)


class DocumentService:
    def __init__(self, openai_api_key: str):
        self.pipeline = DocumentPipeline(
            openai_api_key=openai_api_key
        )
        
    async def process_document(self, document_id: int) -> bool:
        try:
            logger.info(f"Starting processing for document {document_id}")
            db = next(get_db())
            
            try:
                document = db.query(Document).filter(Document.id == document_id).first()
                if not document:
                    logger.error(f"Document {document_id} not found in database")
                    return False
                
                document.processing_status = ProcessingStatus.EXTRACTING
                db.commit()
                logger.info(f"Document {document_id} status updated to EXTRACTING")
                
                file_content = await self._download_document(document.document_url)
                if not file_content:
                    self._update_document_error(db, document, "Failed to download file from S3")
                    return False
                
                extraction_result = await self._extract_text(file_content, document.filename)
                if extraction_result.error:
                    self._update_document_error(db, document, f"Text extraction failed: {extraction_result.error}")
                    return False
                
                document.processing_status = ProcessingStatus.PROCESSING
                db.commit()
                logger.info(f"Document {document_id} status updated to PROCESSING")
                
                processing_result = process_text(extraction_result.text)
                if processing_result.error:
                    self._update_document_error(db, document, f"Text processing failed: {processing_result.error}")
                    return False
                
                pipeline_doc = {
                    "id": document.id,
                    "title": document.filename,
                    "content": processing_result.text,
                    "metadata": {
                        "filename": document.filename,
                        "file_type": document.file_type,
                        "file_size": document.file_size,
                        "thread_id": document.thread_id,
                        "user_id": document.user_id,
                        "extraction_metadata": extraction_result.metadata,
                        "processing_status": ProcessingStatus.PROCESSING.value
                    }
                }
                
                result = await self.pipeline.process_document(pipeline_doc)
                
                if result.get("success"):
                    document.processing_status = ProcessingStatus.READY
                    document.error_message = None
                    db.commit()
                    logger.info(f"Successfully processed document {document_id}")
                    return True
                else:
                    self._update_document_error(db, document, f"Pipeline processing failed: {result.get('error', 'Unknown error')}")
                    return False
                    
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error processing document {document_id}: {str(e)}", exc_info=True)
            try:
                db = next(get_db())
                try:
                    document = db.query(Document).filter(Document.id == document_id).first()
                    if document:
                        self._update_document_error(db, document, f"Processing error: {str(e)}")
                finally:
                    db.close()
            except Exception as cleanup_error:
                logger.error(f"Failed to update error status for document {document_id}: {cleanup_error}")
            return False
    
    async def _download_document(self, s3_url: str) -> Optional[bytes]:
        try:
            if "//" in s3_url:
                key_part = s3_url.split("//")[1]
                if "/" in key_part:
                    s3_key = "/".join(key_part.split("/")[1:])
                else:
                    logger.error(f"Cannot extract S3 key from URL: {s3_url}")
                    return None
            else:
                s3_key = s3_url
            
            return await download_file(s3_key)
        except Exception as e:
            logger.error(f"Failed to download file from S3: {str(e)}")
            return None
    
    async def _extract_text(self, file_content: bytes, filename: str):
        import tempfile
        import aiofiles
        import asyncio
        from pathlib import Path
        from .document_processing.text_extraction import TextExtractionService
        
        temp_dir = tempfile.gettempdir()
        temp_filename = f"temp_{filename}_{os.getpid()}"
        temp_path = os.path.join(temp_dir, temp_filename)
        
        try:
            async with aiofiles.open(temp_path, 'wb') as temp_file:
                await temp_file.write(file_content)
            
            service = TextExtractionService()
            file_path = Path(temp_path)
            
            ext = Path(filename).suffix.lower()
            if ext:
                new_temp_path = temp_path + ext
                os.rename(temp_path, new_temp_path)
                temp_path = new_temp_path
                file_path = Path(temp_path)
            
            result = await asyncio.to_thread(service.extract, file_path)
            
            return result
            
        finally:
            try:
                os.remove(temp_path)
            except:
                pass
    
    def _update_document_error(self, db: Session, document: Document, error_message: str):
        document.processing_status = ProcessingStatus.FAILED
        document.error_message = error_message
        db.commit()
        logger.error(f"Document {document.id} processing failed: {error_message}")
    
    async def search_documents(self, query: str, user_id: str, thread_id: Optional[str] = None) -> Dict[str, Any]:
        filters = {"user_id": user_id}
        if thread_id:
            filters["thread_id"] = thread_id
            
        return await self.pipeline.search_documents(query, filters=filters)
    
    async def get_document_stats(self, document_id: str) -> Dict[str, Any]:
        return await self.pipeline.get_document_stats(document_id)

def start_processing_background(document_id: int) -> bool:
    import threading
    
    def process_in_background():
        try:
            openai_api_key = os.getenv("OPENAI_API_KEY")
            if not openai_api_key:
                logger.error("OPENAI_API_KEY not found in environment variables")
                return False
            
            service = DocumentService(openai_api_key)
            
            import asyncio
            asyncio.run(service.process_document(document_id))
            
        except Exception as e:
            logger.error(f"Background processing failed for document {document_id}: {str(e)}")
    
    thread = threading.Thread(target=process_in_background, daemon=True)
    thread.start()
    
    logger.info(f"Started background processing thread for document {document_id}")
    return True