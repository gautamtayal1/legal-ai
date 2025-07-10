from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import uuid

from .base import DocumentChunk


@dataclass
class OverlapConfig:
    overlap_size: int = 200
    overlap_strategy: str = "sentence_aware"  # "sentence_aware", "word_aware", "character"
    min_overlap_size: int = 50
    max_overlap_size: int = 500
    preserve_sentence_boundaries: bool = True
    preserve_word_boundaries: bool = True


class OverlapManager:
    def __init__(self, config: OverlapConfig):
        self.config = config
    
    def add_overlap_to_chunks(self, chunks: List[DocumentChunk], full_text: str) -> List[DocumentChunk]:
        if len(chunks) <= 1:
            return chunks
        
        overlapped_chunks = []
        
        for i, chunk in enumerate(chunks):
            overlapped_chunk = self._create_overlapped_chunk(chunk, chunks, i, full_text)
            overlapped_chunks.append(overlapped_chunk)
        
        return overlapped_chunks
    
    def _create_overlapped_chunk(self, chunk: DocumentChunk, all_chunks: List[DocumentChunk], 
                               index: int, full_text: str) -> DocumentChunk:
        content = chunk.content
        
        prefix_overlap = self._get_prefix_overlap(chunk, all_chunks, index, full_text)
        suffix_overlap = self._get_suffix_overlap(chunk, all_chunks, index, full_text)
        
        if prefix_overlap or suffix_overlap:
            new_content = f"{prefix_overlap}{content}{suffix_overlap}".strip()
            
            new_chunk = DocumentChunk(
                id=chunk.id,
                content=new_content,
                metadata={
                    **chunk.metadata,
                    "has_overlap": True,
                    "prefix_overlap_length": len(prefix_overlap),
                    "suffix_overlap_length": len(suffix_overlap),
                    "original_content_length": len(content),
                    "overlap_strategy": self.config.overlap_strategy
                },
                start_position=chunk.start_position - len(prefix_overlap) if prefix_overlap else chunk.start_position,
                end_position=chunk.end_position + len(suffix_overlap) if suffix_overlap else chunk.end_position,
                chunk_index=chunk.chunk_index,
                document_id=chunk.document_id,
                parent_section=chunk.parent_section,
                legal_context=chunk.legal_context
            )
            
            return new_chunk
        
        return chunk
    
    def _get_prefix_overlap(self, current_chunk: DocumentChunk, all_chunks: List[DocumentChunk], 
                          index: int, full_text: str) -> str:
        if index == 0:
            return ""
        
        previous_chunk = all_chunks[index - 1]
        
        overlap_start = max(0, current_chunk.start_position - self.config.overlap_size)
        overlap_end = current_chunk.start_position
        
        if overlap_start >= overlap_end:
            return ""
        
        potential_overlap = full_text[overlap_start:overlap_end]
        
        if self.config.overlap_strategy == "sentence_aware":
            return self._get_sentence_aware_overlap(potential_overlap, is_prefix=True)
        elif self.config.overlap_strategy == "word_aware":
            return self._get_word_aware_overlap(potential_overlap, is_prefix=True)
        else:
            return potential_overlap
    
    def _get_suffix_overlap(self, current_chunk: DocumentChunk, all_chunks: List[DocumentChunk], 
                          index: int, full_text: str) -> str:
        if index == len(all_chunks) - 1:
            return ""
        
        next_chunk = all_chunks[index + 1]
        
        overlap_start = current_chunk.end_position
        overlap_end = min(len(full_text), current_chunk.end_position + self.config.overlap_size)
        
        if overlap_start >= overlap_end:
            return ""
        
        potential_overlap = full_text[overlap_start:overlap_end]
        
        if self.config.overlap_strategy == "sentence_aware":
            return self._get_sentence_aware_overlap(potential_overlap, is_prefix=False)
        elif self.config.overlap_strategy == "word_aware":
            return self._get_word_aware_overlap(potential_overlap, is_prefix=False)
        else:
            return potential_overlap
    
    def _get_sentence_aware_overlap(self, text: str, is_prefix: bool) -> str:
        if not text.strip():
            return ""
        
        sentence_endings = ['.', '!', '?', ';\n', '.\n']
        
        if is_prefix:
            for ending in sentence_endings:
                last_pos = text.rfind(ending)
                if last_pos > 0:
                    return text[last_pos + 1:].strip()
            return self._get_word_aware_overlap(text, is_prefix)
        else:
            for ending in sentence_endings:
                first_pos = text.find(ending)
                if first_pos > 0:
                    return text[:first_pos + 1].strip()
            return self._get_word_aware_overlap(text, is_prefix)
    
    def _get_word_aware_overlap(self, text: str, is_prefix: bool) -> str:
        if not text.strip():
            return ""
        
        words = text.split()
        
        if len(words) <= 1:
            return text
        
        if is_prefix:
            return ' '.join(words[1:])
        else:
            return ' '.join(words[:-1])
    
    def calculate_overlap_quality(self, chunks: List[DocumentChunk]) -> Dict[str, Any]:
        if len(chunks) <= 1:
            return {"quality_score": 1.0, "overlap_coverage": 0.0}
        
        total_overlaps = 0
        successful_overlaps = 0
        total_overlap_length = 0
        
        for chunk in chunks:
            if chunk.metadata.get("has_overlap", False):
                total_overlaps += 1
                prefix_len = chunk.metadata.get("prefix_overlap_length", 0)
                suffix_len = chunk.metadata.get("suffix_overlap_length", 0)
                
                if prefix_len > 0 or suffix_len > 0:
                    successful_overlaps += 1
                    total_overlap_length += prefix_len + suffix_len
        
        quality_score = successful_overlaps / total_overlaps if total_overlaps > 0 else 0.0
        avg_overlap_length = total_overlap_length / successful_overlaps if successful_overlaps > 0 else 0.0
        
        return {
            "quality_score": quality_score,
            "overlap_coverage": successful_overlaps / len(chunks),
            "avg_overlap_length": avg_overlap_length,
            "total_overlaps": total_overlaps,
            "successful_overlaps": successful_overlaps
        }
    
