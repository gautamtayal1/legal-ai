"""
Text Extraction Services

Handles extraction of text content from various file formats:
- PDF (including OCR for scanned documents)
- Microsoft Word (DOCX)
- Plain text files
- Image files with OCR
"""

from .base import TextExtractionService
from .pdf_extractor import PDFExtractor
from .docx_extractor import DocxExtractor
from .ocr_extractor import OCRExtractor
from .text_extractor import PlainTextExtractor

__all__ = [
    "TextExtractionService",
    "PDFExtractor", 
    "DocxExtractor",
    "OCRExtractor",
    "PlainTextExtractor"
] 