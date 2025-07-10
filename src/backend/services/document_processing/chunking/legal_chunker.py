from typing import Dict, List, Optional, Any, Tuple
from langchain_text_splitters import RecursiveCharacterTextSplitter
import uuid
import re

from .base import ChunkingService, ChunkConfig, DocumentChunk


class LegalChunker(ChunkingService):
    def __init__(self, config: ChunkConfig):
        super().__init__(config)
        self._setup_legal_patterns()
        self._setup_splitters()
    
    def _setup_legal_patterns(self):
        self.section_patterns = [
            r'(?:^|\n)(?:SECTION|Section|SEC\.|Sec\.)\s+\d+',
            r'(?:^|\n)(?:ARTICLE|Article|ART\.|Art\.)\s+\d+',
            r'(?:^|\n)(?:CHAPTER|Chapter|CHAP\.|Chap\.)\s+\d+',
            r'(?:^|\n)(?:PART|Part)\s+\d+',
            r'(?:^|\n)\d+\.\s+[A-Z]',
            r'(?:^|\n)\([a-z]\)',
            r'(?:^|\n)\([0-9]+\)',
            r'(?:^|\n)[A-Z]\.',
        ]
        
        self.legal_separators = [
            r'(?:^|\n)(?:WHEREAS|THEREFORE|NOW, THEREFORE|IN WITNESS WHEREOF)',
            r'(?:^|\n)(?:DEFINITIONS|INTERPRETATIONS|RECITALS)',
            r'(?:^|\n)(?:SCHEDULES?|EXHIBITS?|APPENDICES|ANNEXES?)',
            r'(?:^|\n)(?:PARTIES|PARTY)',
            r'(?:^|\n)(?:EFFECTIVE DATE|TERM|TERMINATION)',
            r'(?:^|\n)(?:GOVERNING LAW|JURISDICTION|DISPUTE RESOLUTION)',
        ]
        
        self.definition_patterns = [
            r'(?:^|\n)["""]([^"""]+)["""] means',
            r'(?:^|\n)"([^"]+)" means',
            r'(?:^|\n)([A-Z][A-Z\s]+) means',
            r'(?:^|\n)For purposes of this [^,]+,\s*["""]([^"""]+)["""]',
        ]
    
    def _setup_splitters(self):
        legal_separators = [
            "\n\n\n",
            "\n\n",
            r"(?=\n(?:SECTION|Section|SEC\.|Sec\.)\s+\d+)",
            r"(?=\n(?:ARTICLE|Article|ART\.|Art\.)\s+\d+)",
            r"(?=\n(?:CHAPTER|Chapter|CHAP\.|Chap\.)\s+\d+)",
            r"(?=\n\d+\.\s+[A-Z])",
            r"(?=\n\([a-z]\))",
            r"(?=\n\([0-9]+\))",
            "\n",
            ". ",
            " ",
            ""
        ]
        
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
            length_function=len,
            separators=legal_separators,
            keep_separator=True,
            is_separator_regex=True
        )
    
    def chunk_text(self, text: str, document_id: str, metadata: Optional[Dict[str, Any]] = None) -> List[DocumentChunk]:
        if not text.strip():
            return []
            
        metadata = metadata or {}
        
        if self.config.preserve_legal_structure:
            chunks = self._legal_aware_chunk(text, document_id, metadata)
        else:
            chunks = self._standard_chunk(text, document_id, metadata)
        
        chunks = self._enhance_legal_metadata(chunks, text)
        return self.validate_chunks(chunks)
    
    def _legal_aware_chunk(self, text: str, document_id: str, metadata: Dict[str, Any]) -> List[DocumentChunk]:
        sections = self._identify_sections(text)
        chunks = []
        
        for i, (section_title, section_content, start_pos) in enumerate(sections):
            if len(section_content) > self.config.max_chunk_size:
                section_chunks = self._chunk_large_section(
                    section_content, section_title, document_id, metadata, start_pos
                )
                chunks.extend(section_chunks)
            else:
                chunk = DocumentChunk(
                    id=str(uuid.uuid4()),
                    content=section_content,
                    metadata={
                        **metadata,
                        "chunking_method": "legal_aware",
                        "chunk_type": "legal_section",
                        "section_title": section_title
                    },
                    start_position=start_pos,
                    end_position=start_pos + len(section_content),
                    chunk_index=len(chunks),
                    document_id=document_id,
                    parent_section=section_title
                )
                chunks.append(chunk)
        
        return chunks
    
    def _identify_sections(self, text: str) -> List[Tuple[str, str, int]]:
        sections = []
        
        combined_pattern = '|'.join(self.section_patterns)
        matches = list(re.finditer(combined_pattern, text, re.MULTILINE))
        
        if not matches:
            return [("Document", text, 0)]
        
        for i, match in enumerate(matches):
            section_start = match.start()
            section_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            
            section_title = match.group().strip()
            section_content = text[section_start:section_end].strip()
            
            sections.append((section_title, section_content, section_start))
        
        return sections
    
    def _chunk_large_section(self, section_content: str, section_title: str, 
                           document_id: str, metadata: Dict[str, Any], section_start: int) -> List[DocumentChunk]:
        chunk_texts = self.splitter.split_text(section_content)
        chunks = []
        
        current_position = 0
        for i, chunk_text in enumerate(chunk_texts):
            chunk = DocumentChunk(
                id=str(uuid.uuid4()),
                content=chunk_text,
                metadata={
                    **metadata,
                    "chunking_method": "legal_aware",
                    "chunk_type": "legal_subsection",
                    "section_title": section_title,
                    "subsection_index": i
                },
                start_position=section_start + current_position,
                end_position=section_start + current_position + len(chunk_text),
                chunk_index=i,
                document_id=document_id,
                parent_section=section_title
            )
            chunks.append(chunk)
            current_position += len(chunk_text)
        
        return chunks
    
    def _standard_chunk(self, text: str, document_id: str, metadata: Dict[str, Any]) -> List[DocumentChunk]:
        chunk_texts = self.splitter.split_text(text)
        chunks = []
        
        current_position = 0
        for i, chunk_text in enumerate(chunk_texts):
            start_pos = text.find(chunk_text, current_position)
            if start_pos == -1:
                start_pos = current_position
            
            chunk = DocumentChunk(
                id=str(uuid.uuid4()),
                content=chunk_text,
                metadata={
                    **metadata,
                    "chunking_method": "legal_standard",
                    "chunk_type": "standard"
                },
                start_position=start_pos,
                end_position=start_pos + len(chunk_text),
                chunk_index=i,
                document_id=document_id
            )
            chunks.append(chunk)
            current_position = start_pos + len(chunk_text)
        
        return chunks
    
    def _enhance_legal_metadata(self, chunks: List[DocumentChunk], full_text: str) -> List[DocumentChunk]:
        for chunk in chunks:
            legal_context = self._extract_legal_context(chunk.content, full_text)
            chunk.legal_context = legal_context
            
            if legal_context:
                chunk.metadata.update({
                    "contains_definitions": len(legal_context.get("definitions", [])) > 0,
                    "contains_obligations": len(legal_context.get("obligations", [])) > 0,
                    "contains_parties": len(legal_context.get("parties", [])) > 0,
                    "definition_count": len(legal_context.get("definitions", [])),
                    "obligation_count": len(legal_context.get("obligations", [])),
                    "party_count": len(legal_context.get("parties", []))
                })
        
        return chunks
    
    def _extract_legal_context(self, chunk_text: str, full_text: str) -> Dict[str, Any]:
        context = {
            "definitions": re.findall(r'"([^"]+)" means', chunk_text, re.IGNORECASE),
            "obligations": bool(re.search(r'\b(?:shall|must|will|agree to)\b', chunk_text, re.IGNORECASE)),
            "parties": re.findall(r'\b(?:Company|Corporation|Licensor|Licensee)\b', chunk_text, re.IGNORECASE),
            "references": re.findall(r'(?:Section|Article)\s+\d+', chunk_text, re.IGNORECASE)
        }
        return context
    
    def chunk_document(self, document: Dict[str, Any]) -> List[DocumentChunk]:
        text = document.get("content", "")
        document_id = document.get("id", str(uuid.uuid4()))
        metadata = document.get("metadata", {})
        
        return self.chunk_text(text, document_id, metadata)