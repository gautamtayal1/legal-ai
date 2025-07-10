"""
Base classes for text processing.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from pathlib import Path

@dataclass
class ProcessingResult:
    """Result of text processing operations."""
    text: str
    original_length: int
    processed_length: int
    error: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    @property
    def compression_ratio(self) -> float:
        """Calculate how much the text was compressed/cleaned."""
        if self.original_length == 0:
            return 0.0
        return self.processed_length / self.original_length

class TextProcessor(ABC):
    """Base class for text processors."""
    
    @abstractmethod
    def process(self, text: str) -> ProcessingResult:
        """Process text and return result."""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the processor."""
        pass