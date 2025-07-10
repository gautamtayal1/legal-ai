"""
Simple background processing for documents.
"""

import logging
from typing import Optional
from .text_extraction import extract_text

logger = logging.getLogger(__name__)

def start_processing_background(document_id: int) -> bool:
    """
    Start background processing for a document.
    
    For now, this is a simple synchronous implementation.
    Later can be replaced with Celery for true background processing.
    """
    try:
        logger.info(f"Starting background processing for document {document_id}")
        
        # TODO: Get document details from database
        # TODO: Download file from S3
        # TODO: Extract text
        # TODO: Update document status
        
        logger.info(f"Background processing queued for document {document_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to start processing for document {document_id}: {e}")
        return False

def process_document_sync(document_id: int, file_path: str) -> bool:
    """
    Synchronously process a document (for testing).
    """
    try:
        logger.info(f"Processing document {document_id} from {file_path}")
        
        result = extract_text(file_path)
        
        if result.error:
            logger.error(f"Text extraction failed: {result.error}")
            return False
        
        logger.info(f"Successfully extracted {len(result.text)} characters")
        return True
        
    except Exception as e:
        logger.error(f"Document processing failed: {e}")
        return False 