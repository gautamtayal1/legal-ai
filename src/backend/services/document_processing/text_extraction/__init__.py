"""
Text extraction service - simplified but complete.
"""

from pathlib import Path
from typing import Union, List
from .base import ExtractionResult
from .pdf_extractor import PDFExtractor
from .docx_extractor import DOCXExtractor
from .text_extractor import PlainTextExtractor

class TextExtractionService:
    def __init__(self):
        self.extractors = {
            '.pdf': PDFExtractor(),
            '.docx': DOCXExtractor(),
            '.doc': DOCXExtractor(),
            '.txt': PlainTextExtractor(),
            '.md': PlainTextExtractor(),
            '.csv': PlainTextExtractor(),
            '.log': PlainTextExtractor()
        }
    
    def extract(self, file_path: Union[str, Path]) -> ExtractionResult:
        file_path = Path(file_path)
        
        if not file_path.exists():
            return ExtractionResult("", error=f"File not found: {file_path}")
        
        ext = file_path.suffix.lower()
        extractor = self.extractors.get(ext)
        
        if not extractor:
            return ExtractionResult("", error=f"Unsupported file type: {ext}")
        
        return extractor.extract(file_path)
    
    def extract_batch(self, file_paths: List[Union[str, Path]]) -> List[ExtractionResult]:
        return [self.extract(fp) for fp in file_paths]

# Default service instance
_service = TextExtractionService()

def extract_text(file_path: Union[str, Path]) -> ExtractionResult:
    """Extract text from file."""
    return _service.extract(file_path)

def extract_batch(file_paths: List[Union[str, Path]]) -> List[ExtractionResult]:
    """Extract text from multiple files."""
    return _service.extract_batch(file_paths)

def is_supported(file_path: Union[str, Path]) -> bool:
    """Check if file type is supported."""
    ext = Path(file_path).suffix.lower()
    return ext in _service.extractors

__all__ = ['extract_text', 'extract_batch', 'is_supported', 'ExtractionResult', 'TextExtractionService'] 