"""
Document Structure Analysis Services

Analyzes legal document structure to identify:
- Sections, subsections, and hierarchical organization
- Headers, footers, and formatting patterns
- Legal document patterns (articles, clauses, schedules)
- Page numbering and document flow
- Table of contents and cross-references
"""

from .base import StructureAnalysisService
from .legal_structure_analyzer import LegalStructureAnalyzer
from .section_extractor import SectionExtractor
from .hierarchy_builder import HierarchyBuilder

__all__ = [
    "StructureAnalysisService",
    "LegalStructureAnalyzer",
    "SectionExtractor", 
    "HierarchyBuilder"
] 