from typing import Dict, List, Optional, Any, Union
import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging

from .base import ChunkingService, ChunkConfig, DocumentChunk, ChunkingStrategy
from .semantic_chunker import SemanticChunker
from .legal_chunker import LegalChunker
from .overlap_manager import OverlapManager, OverlapConfig
from .chunk_metadata import ChunkMetadataManager


class DocumentChunkingService:
    def __init__(self, 
                 chunk_config: Optional[ChunkConfig] = None,
                 overlap_config: Optional[OverlapConfig] = None):
        
        self.chunk_config = chunk_config or ChunkConfig()
        self.overlap_config = overlap_config or OverlapConfig()
        
        self.logger = logging.getLogger(__name__)
        
        self.chunkers = self._initialize_chunkers()
        self.overlap_manager = OverlapManager(self.overlap_config)
        self.metadata_manager = ChunkMetadataManager()
        
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    def _initialize_chunkers(self) -> Dict[ChunkingStrategy, ChunkingService]:
        return {
            ChunkingStrategy.SEMANTIC: SemanticChunker(self.chunk_config),
            ChunkingStrategy.LEGAL: LegalChunker(self.chunk_config),
            ChunkingStrategy.RECURSIVE: SemanticChunker(self.chunk_config),
            ChunkingStrategy.FIXED_SIZE: SemanticChunker(self.chunk_config)
        }
    
    async def chunk_document(self, 
                           document: Dict[str, Any],
                           strategy: Optional[ChunkingStrategy] = None,
                           add_overlap: bool = True,
                           create_metadata: bool = True) -> List[DocumentChunk]:
        
        strategy = strategy or self.chunk_config.strategy
        
        chunker = self.chunkers[strategy]
        chunks = await self._run_chunking(chunker, document)
        
        if add_overlap and len(chunks) > 1:
            full_text = document.get("content", "")
            chunks = self.overlap_manager.add_overlap_to_chunks(chunks, full_text)
        
        if create_metadata:
            for chunk in chunks:
                self.metadata_manager.create_metadata(chunk)
        
        return chunks
    
    async def _run_chunking(self, chunker: ChunkingService, document: Dict[str, Any]) -> List[DocumentChunk]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, chunker.chunk_document, document)
    
    async def chunk_text(self, 
                        text: str,
                        document_id: str,
                        strategy: Optional[ChunkingStrategy] = None,
                        metadata: Optional[Dict[str, Any]] = None,
                        add_overlap: bool = True,
                        create_metadata: bool = True) -> List[DocumentChunk]:
        
        document = {
            "id": document_id,
            "content": text,
            "metadata": metadata or {}
        }
        
        return await self.chunk_document(document, strategy, add_overlap, create_metadata)
    
    async def chunk_multiple_documents(self, 
        documents: List[Dict[str, Any]],
        strategy: Optional[ChunkingStrategy] = None,
        add_overlap: bool = True,
        create_metadata: bool = True) -> Dict[str, List[DocumentChunk]]:
        
        tasks = []
        for document in documents:
            task = self.chunk_document(document, strategy, add_overlap, create_metadata)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        output = {}
        for i, result in enumerate(results):
            document_id = documents[i].get("id", f"doc_{i}")
            
            if isinstance(result, Exception):
                self.logger.error(f"Error chunking document {document_id}: {str(result)}")
                output[document_id] = []
            else:
                output[document_id] = result
        
        return output
    
    def get_chunk_statistics(self, chunks: List[DocumentChunk]) -> Dict[str, Any]:
        if not chunks:
            return {}
        
        chunk_lengths = [len(chunk.content) for chunk in chunks]
        chunk_types = [chunk.metadata.get("chunk_type", "unknown") for chunk in chunks]
        
        type_counts = {}
        for chunk_type in chunk_types:
            type_counts[chunk_type] = type_counts.get(chunk_type, 0) + 1
        
        legal_chunks = [chunk for chunk in chunks if chunk.legal_context]
        
        stats = {
            "total_chunks": len(chunks),
            "avg_chunk_length": sum(chunk_lengths) / len(chunk_lengths),
            "min_chunk_length": min(chunk_lengths),
            "max_chunk_length": max(chunk_lengths),
            "total_content_length": sum(chunk_lengths),
            "chunk_type_distribution": type_counts,
            "legal_chunks_count": len(legal_chunks),
            "legal_chunks_percentage": len(legal_chunks) / len(chunks) * 100
        }
        
        if legal_chunks:
            legal_stats = self._calculate_legal_statistics(legal_chunks)
            stats.update(legal_stats)
        
        return stats
    
    def _calculate_legal_statistics(self, legal_chunks: List[DocumentChunk]) -> Dict[str, Any]:
        definitions_count = sum(1 for chunk in legal_chunks 
                              if chunk.legal_context and chunk.legal_context.get("definitions"))
        
        obligations_count = sum(1 for chunk in legal_chunks 
                              if chunk.legal_context and chunk.legal_context.get("obligations"))
        
        parties_count = sum(1 for chunk in legal_chunks 
                          if chunk.legal_context and chunk.legal_context.get("parties"))
        
        references_count = sum(1 for chunk in legal_chunks 
                             if chunk.legal_context and chunk.legal_context.get("references"))
        
        return {
            "legal_content_analysis": {
                "chunks_with_definitions": definitions_count,
                "chunks_with_obligations": obligations_count,
                "chunks_with_parties": parties_count,
                "chunks_with_references": references_count,
                "definitions_percentage": definitions_count / len(legal_chunks) * 100,
                "obligations_percentage": obligations_count / len(legal_chunks) * 100,
                "parties_percentage": parties_count / len(legal_chunks) * 100,
                "references_percentage": references_count / len(legal_chunks) * 100
            }
        }
    
    def optimize_chunking_config(self, sample_text: str, target_chunk_count: int) -> ChunkConfig:
        estimated_size = len(sample_text) // target_chunk_count
        
        chunk_size = max(500, min(4000, estimated_size))
        chunk_overlap = min(chunk_size // 5, 400)
        
        return ChunkConfig(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            strategy=ChunkingStrategy.LEGAL if self._is_legal_text(sample_text) else ChunkingStrategy.SEMANTIC,
            preserve_legal_structure=self._is_legal_text(sample_text),
            min_chunk_size=100,
            max_chunk_size=chunk_size * 2
        )
    
    def _is_legal_text(self, text: str) -> bool:
        legal_indicators = [
            "whereas", "therefore", "party", "parties", "agreement", "contract",
            "section", "article", "clause", "provision", "shall", "hereby",
            "terms and conditions", "legal", "law", "court", "jurisdiction"
        ]
        
        text_lower = text.lower()
        legal_word_count = sum(1 for indicator in legal_indicators if indicator in text_lower)
        
        return legal_word_count >= 3
    
    def get_chunk_by_id(self, chunk_id: str) -> Optional[DocumentChunk]:
        metadata = self.metadata_manager.get_metadata(chunk_id)
        if metadata:
            return metadata
        return None
    
    def search_chunks(self, query: str, document_id: Optional[str] = None) -> List[DocumentChunk]:
        all_chunks = []
        
        criteria = {}
        if document_id:
            criteria["document_id"] = document_id
        
        matching_metadata = self.metadata_manager.get_chunks_by_criteria(criteria)
        
        query_lower = query.lower()
        for metadata in matching_metadata:
            if query_lower in metadata.custom_metadata.get("content", "").lower():
                all_chunks.append(metadata)
        
        return all_chunks
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=True)
    
    def __del__(self):
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)