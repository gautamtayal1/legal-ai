"""
Unified Document Service

This service acts as the main orchestrator for document processing,
connecting the API layer with the document processing pipeline.
"""

import logging
import os
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from .document_pipeline import DocumentPipeline
from .document_processing.text_extraction import extract_text
from .document_processing.text_processing import process_text
from ..models.document import Document, ProcessingStatus
from ..utils.s3_service import download_file
from ..core.database import get_db

logger = logging.getLogger(__name__)


class DocumentService:
    def __init__(self, openai_api_key: str):
        """Initialize the document service with required dependencies."""
        self.pipeline = DocumentPipeline(
            openai_api_key=openai_api_key
        )
        
    def process_document(self, document_id: int) -> bool:
        """
        Process a document asynchronously.
        This would be the main entry point called by the API.
        """
        try:
            logger.info(f"Starting processing for document {document_id}")
            db = next(get_db())
            
            try:
                document = db.query(Document).filter(Document.id == document_id).first()
                if not document:
                    logger.error(f"Document {document_id} not found in database")
                    return False
                
                document.processing_status = ProcessingStatus.PROCESSING
                db.commit()
                
                file_content = self._download_document(document.document_url)
                if not file_content:
                    self._update_document_error(db, document, "Failed to download file from S3")
                    return False
                
                extraction_result = self._extract_text(file_content, document.filename)
                if extraction_result.error:
                    self._update_document_error(db, document, f"Text extraction failed: {extraction_result.error}")
                    return False
                
                # Process and clean the extracted text
                processing_result = process_text(extraction_result.text)
                if processing_result.error:
                    self._update_document_error(db, document, f"Text processing failed: {processing_result.error}")
                    return False
                
                pipeline_doc = {
                    "id": str(document.id),
                    "title": document.filename,
                    "content": processing_result.text,
                    "metadata": {
                        "filename": document.filename,
                        "file_type": document.file_type,
                        "file_size": document.file_size,
                        "thread_id": document.thread_id,
                        "user_id": document.user_id,
                        "extraction_metadata": extraction_result.metadata,
                        "processing_metadata": processing_result.metadata
                    }
                }
                
                import asyncio
                result = asyncio.run(self.pipeline.process_document(pipeline_doc))
                
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
                document = db.query(Document).filter(Document.id == document_id).first()
                if document:
                    self._update_document_error(db, document, f"Processing error: {str(e)}")
                db.close()
            except:
                pass
            return False
    
    def _download_document(self, s3_url: str) -> Optional[bytes]:
        """Download document content from S3."""
        try:
            # Extract S3 key from URL
            # This is a simplified extraction - you might need to adjust based on your S3 URL format
            if "//" in s3_url:
                key_part = s3_url.split("//")[1]
                if "/" in key_part:
                    s3_key = "/".join(key_part.split("/")[1:])  # Remove bucket name
                else:
                    logger.error(f"Cannot extract S3 key from URL: {s3_url}")
                    return None
            else:
                s3_key = s3_url
            
            return download_file(s3_key)
        except Exception as e:
            logger.error(f"Failed to download file from S3: {str(e)}")
            return None
    
    def _extract_text(self, file_content: bytes, filename: str):
        """Extract text from file content."""
        # Save content to temporary file for extraction
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=f"_{filename}", delete=False) as temp_file:
            temp_file.write(file_content)
            temp_path = temp_file.name
        
        try:
            return extract_text(temp_path)
        finally:
            # Clean up temp file
            try:
                os.unlink(temp_path)
            except:
                pass
    
    def _update_document_error(self, db: Session, document: Document, error_message: str):
        """Update document with error status and message."""
        document.processing_status = ProcessingStatus.ERROR
        document.error_message = error_message
        db.commit()
        logger.error(f"Document {document.id} processing failed: {error_message}")
    
    def search_documents(self, query: str, user_id: str, thread_id: Optional[str] = None) -> Dict[str, Any]:
        """Search documents for a user."""
        filters = {"user_id": user_id}
        if thread_id:
            filters["thread_id"] = thread_id
            
        import asyncio
        return asyncio.run(self.pipeline.search_documents(query, filters=filters))
    
    def get_document_stats(self, document_id: str) -> Dict[str, Any]:
        """Get processing statistics for a document."""
        return self.pipeline.get_document_stats(document_id)


def start_processing_background(document_id: int) -> bool:
    """
    Entry point for background processing.
    This function will be called by the API.
    """
    try:
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            logger.error("OPENAI_API_KEY not found in environment variables")
            return False
        
        service = DocumentService(openai_api_key)
        return service.process_document(document_id)
        
    except Exception as e:
        logger.error(f"Failed to start processing for document {document_id}: {str(e)}")
        return False 