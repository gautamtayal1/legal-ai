"""
Simple text file extraction.
"""

from pathlib import Path
import chardet
from .base import TextExtractor, ExtractionResult

class PlainTextExtractor(TextExtractor):
    
    def extract(self, file_path: Path) -> ExtractionResult:
        try:
            # Detect encoding
            with open(file_path, 'rb') as file:
                raw = file.read()
                encoding = chardet.detect(raw)['encoding'] or 'utf-8'
            
            # Read text
            with open(file_path, 'r', encoding=encoding, errors='replace') as file:
                text = file.read()
            
            return ExtractionResult(
                text=text,
                metadata={
                    "encoding": encoding,
                    "size": len(text),
                    "method": "chardet"
                }
            )
            
        except Exception as e:
            return ExtractionResult("", error=f"Text extraction failed: {e}") 