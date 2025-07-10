"""
Simple base classes for text extraction.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional, List, Union
from pathlib import Path

@dataclass
class ExtractionResult:
    text: str
    error: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class TextExtractor(ABC):
    """Simple base for extractors."""
    
    @abstractmethod
    def extract(self, file_path: Path) -> ExtractionResult:
        pass 