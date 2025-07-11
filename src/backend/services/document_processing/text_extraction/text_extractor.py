"""
Simple text file extraction.
"""

from pathlib import Path
import chardet
import aiofiles
import asyncio
from .base import TextExtractor, ExtractionResult

class PlainTextExtractor(TextExtractor):
    
    def extract(self, file_path: Path) -> ExtractionResult:
        # Sync wrapper for backward compatibility
        return asyncio.run(self.extract_async(file_path))
    
    async def extract_async(self, file_path: Path) -> ExtractionResult:
        try:
            # Detect encoding using async file I/O
            async with aiofiles.open(file_path, 'rb') as file:
                raw = await file.read()
                encoding = chardet.detect(raw)['encoding'] or 'utf-8'
            
            # Read text using async file I/O
            async with aiofiles.open(file_path, 'r', encoding=encoding, errors='replace') as file:
                text = await file.read()
            
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