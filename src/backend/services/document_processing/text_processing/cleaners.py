"""
Text cleaning processors.
"""

import re
from typing import Dict, Any
from .base import TextProcessor, ProcessingResult

class WhitespaceNormalizer(TextProcessor):
    """Normalize whitespace in text."""
    
    @property
    def name(self) -> str:
        return "whitespace_normalizer"
    
    def process(self, text: str) -> ProcessingResult:
        """Normalize whitespace."""
        original_length = len(text)
        
        text = re.sub(r' +', ' ', text)
        
        text = re.sub(r'\n\s*\n+', '\n\n', text)
        
        text = text.replace('\t', ' ')
        
        text = text.strip()
        
        return ProcessingResult(
            text=text,
            original_length=original_length,
            processed_length=len(text),
            metadata={"processor": self.name}
        )

class EncodingCleaner(TextProcessor):
    """Clean encoding-related issues."""
    
    @property
    def name(self) -> str:
        return "encoding_cleaner"
    
    def process(self, text: str) -> ProcessingResult:
        """Clean encoding issues."""
        original_length = len(text)
        
        replacements = {
            '\u00a0': ' ',  
            '\u2018': "'",  
            '\u2019': "'",  
            '\u201c': '"',  
            '\u201d': '"',  
            '\u2013': '-',  
            '\u2014': '--', 
            '\u2026': '...', 
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        
        return ProcessingResult(
            text=text,
            original_length=original_length,
            processed_length=len(text),
            metadata={"processor": self.name, "replacements": len(replacements)}
        )

class LineBreakNormalizer(TextProcessor):
    """Normalize line breaks for better text flow."""
    
    @property
    def name(self) -> str:
        return "line_break_normalizer"
    
    def process(self, text: str) -> ProcessingResult:
        """Normalize line breaks."""
        original_length = len(text)
        
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        text = re.sub(r'-\s*\n\s*', '', text)
        
        text = re.sub(r'(?<=[a-zA-Z])\n(?=[a-z])', ' ', text)
        
        text = re.sub(r'(?<=[.!?:;])\n', '\n', text)
        
        return ProcessingResult(
            text=text,
            original_length=original_length,
            processed_length=len(text),
            metadata={"processor": self.name}
        )

class BasicTextCleaner(TextProcessor):
    """Basic text cleaning for legal documents."""
    
    @property
    def name(self) -> str:
        return "basic_text_cleaner"
    
    def process(self, text: str) -> ProcessingResult:
        """Basic text cleaning."""
        original_length = len(text)
        
        text = re.sub(r'[.]{3,}', '...', text)
        text = re.sub(r'[!]{2,}', '!', text)
        text = re.sub(r'[?]{2,}', '?', text)
        
        text = re.sub(r'\b[il1|]+\b', 'I', text)  
        text = re.sub(r'\b0\b', 'O', text)  
        
        text = re.sub(r'^\d+\s*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'Page \d+ of \d+', '', text, flags=re.IGNORECASE)
        
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return ProcessingResult(
            text=text,
            original_length=original_length,
            processed_length=len(text),
            metadata={"processor": self.name}
        )