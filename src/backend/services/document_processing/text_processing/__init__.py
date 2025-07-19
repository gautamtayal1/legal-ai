"""
Text processing service - clean and normalize text for chunking.
"""

from typing import Union, List, Optional
from .base import ProcessingResult, TextProcessor
from .cleaners import WhitespaceNormalizer, EncodingCleaner, LineBreakNormalizer, BasicTextCleaner

class TextProcessingService:
    """Main text processing service."""
    
    def __init__(self, processors: Optional[List[TextProcessor]] = None):
        """Initialize with default or custom processors."""
        if processors is None:
            self.processors = [
                EncodingCleaner(),
                WhitespaceNormalizer(),
                LineBreakNormalizer(),
                BasicTextCleaner()
            ]
        else:
            self.processors = processors
    
    def process(self, text: str) -> ProcessingResult:
        """Process text through all processors."""
        if not text or not text.strip():
            return ProcessingResult(
                text="",
                original_length=len(text),
                processed_length=0,
                error="Empty or whitespace-only text"
            )
        
        original_length = len(text)
        current_text = text
        processor_results = []
        
        for processor in self.processors:
            try:
                result = processor.process(current_text)
                if result.error:
                    return ProcessingResult(
                        text=current_text,
                        original_length=original_length,
                        processed_length=len(current_text),
                        error=f"Error in {processor.name}: {result.error}"
                    )
                
                current_text = result.text
                processor_results.append({
                    "processor": processor.name,
                    "input_length": result.original_length,
                    "output_length": result.processed_length,
                    "compression_ratio": result.compression_ratio
                })
                
            except Exception as e:
                return ProcessingResult(
                    text=current_text,
                    original_length=original_length,
                    processed_length=len(current_text),
                    error=f"Exception in {processor.name}: {str(e)}"
                )
        
        return ProcessingResult(
            text=current_text,
            original_length=original_length,
            processed_length=len(current_text),
            metadata={
                "processors_applied": len(self.processors),
                "processor_results": processor_results,
                "total_compression_ratio": len(current_text) / original_length if original_length > 0 else 0
            }
        )
    
    def process_batch(self, texts: List[str]) -> List[ProcessingResult]:
        """Process multiple texts."""
        return [self.process(text) for text in texts]
    
    def get_processor_names(self) -> List[str]:
        """Get list of processor names."""
        return [p.name for p in self.processors]

_service = TextProcessingService()

def process_text(text: str) -> ProcessingResult:
    """Process text using default service."""
    return _service.process(text)

def process_text_batch(texts: List[str]) -> List[ProcessingResult]:
    """Process multiple texts using default service."""
    return _service.process_batch(texts)

def get_available_processors() -> List[str]:
    """Get list of available processors."""
    return _service.get_processor_names()

__all__ = [
    'process_text', 
    'process_text_batch', 
    'get_available_processors',
    'TextProcessingService', 
    'ProcessingResult',
    'TextProcessor'
]