import asyncio
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from .document_processing.chunking.chunking_service import DocumentChunkingService
from .document_processing.chunking.base import ChunkingStrategy, ChunkConfig
from .document_processing.embedding.embedding_service import EmbeddingService, EmbeddingConfig
from .document_processing.embedding.vector_storage_service import VectorStorageService, VectorStorageConfig
from .document_processing.search_engine.elasticsearch_service import ElasticsearchService, ElasticsearchConfig


@dataclass
class PipelineConfig:
    chunk_config: Optional[ChunkConfig] = None
    embedding_config: Optional[EmbeddingConfig] = None
    storage_config: Optional[VectorStorageConfig] = None
    elasticsearch_config: Optional[ElasticsearchConfig] = None
    enable_overlap: bool = True
    enable_metadata: bool = True
    enable_elasticsearch: bool = True
    batch_size: int = 50


class DocumentPipeline:
    def __init__(self, 
            openai_api_key: str,
            config: Optional[PipelineConfig] = None):
        
        self.config = config or PipelineConfig()
        self.logger = logging.getLogger(__name__)
        
        self.chunking_service = DocumentChunkingService(
            chunk_config=self.config.chunk_config
        )
        
        self.embedding_service = EmbeddingService(
            api_key=openai_api_key,
            config=self.config.embedding_config
        )
        
        self.vector_storage = VectorStorageService(
            config=self.config.storage_config
        )
        
        if self.config.enable_elasticsearch:
            self.elasticsearch = ElasticsearchService(
                config=self.config.elasticsearch_config
            )
        else:
            self.elasticsearch = None
    
    async def process_document(self, 
        document: Dict[str, Any],
        strategy: Optional[ChunkingStrategy] = None) -> Dict[str, Any]:
        try:
            document_id = document.get("id", "")
            self.logger.info(f"Processing document {document_id}")
            
            chunks = await self.chunking_service.chunk_document(
                document=document,
                strategy=strategy,
                add_overlap=self.config.enable_overlap,
                create_metadata=self.config.enable_metadata
            )
            
            if not chunks:
                return {"success": False, "error": "Error chunking document"}
            
            try:
                embedded_chunks = await self.embedding_service.embed_chunks(chunks)
                if not embedded_chunks:
                    return {"success": False, "error": "Failed to generate embeddings"}
            except Exception as e:
                return {"success": False, "error": f"Embedding generation failed: {str(e)}"}
            
            try:
                if self.elasticsearch:
                    vector_success, elasticsearch_success = await asyncio.gather(
                        self.vector_storage.store_embeddings(embedded_chunks),
                        self.elasticsearch.index_chunks(chunks),
                        return_exceptions=True
                    )
                    
                    # Handle vector storage result
                    if isinstance(vector_success, Exception):
                        return {"success": False, "error": f"Vector storage failed: {str(vector_success)}"}
                    if not vector_success:
                        return {"success": False, "error": "Failed to store embeddings in vector database"}
                    
                    # Handle elasticsearch result (non-critical)
                    if isinstance(elasticsearch_success, Exception):
                        self.logger.warning(f"Elasticsearch indexing error for document {document_id}: {str(elasticsearch_success)}")
                        elasticsearch_success = False
                    elif not elasticsearch_success:
                        self.logger.warning(f"Elasticsearch indexing failed for document {document_id}, but continuing")
                        
                else:
                    # Only vector storage if Elasticsearch is disabled
                    vector_success = await self.vector_storage.store_embeddings(embedded_chunks)
                    if not vector_success:
                        return {"success": False, "error": "Failed to store embeddings in vector database"}
                    elasticsearch_success = True
                    
            except Exception as e:
                return {"success": False, "error": f"Storage operations failed: {str(e)}"}

            stats = self.chunking_service.get_chunk_statistics(chunks)
            return {
                "success": True,
                "document_id": document_id,
                "chunks_processed": len(chunks),
                "statistics": stats,
                "elasticsearch_indexed": elasticsearch_success
            }
                
        except Exception as e:
            self.logger.error(f"Pipeline error for document {document.get('id', 'unknown')}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def process_documents(self, 
                              documents: List[Dict[str, Any]],
                              strategy: Optional[ChunkingStrategy] = None) -> Dict[str, Any]:
        
        results = []
        for document in documents:
            result = await self.process_document(document, strategy)
            results.append(result)
        
        successful = sum(1 for r in results if r.get("success", False))
        total_chunks = sum(r.get("chunks_processed", 0) for r in results)
        
        return {
            "total_documents": len(documents),
            "successful_documents": successful,
            "failed_documents": len(documents) - successful,
            "total_chunks_processed": total_chunks,
            "results": results
        }
    
    async def search_documents(self, 
        query: str,
        n_results: int = 10,
        document_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        
        try:
            query_embedding = await self.embedding_service.embed_query(query)
            
            results = await self.vector_storage.search_similar(
                query_embedding=query_embedding,
                n_results=n_results,
                document_id=document_id,
                filters=filters
            )
            
            return results
            
        except Exception as e:
            self.logger.error(f"Search error: {str(e)}")
            return []
    
    async def get_document_stats(self, document_id: str) -> Dict[str, Any]:
        """Get document statistics using async operations"""
        try:
            chunks = await self.vector_storage.search_similar(
                query_embedding=[0.0] * self.embedding_service.get_embedding_dimension(),
                document_id=document_id,
                n_results=1000
            )
            
            if not chunks:
                return {"error": "Document not found"}
            
            chunk_lengths = [chunk["metadata"].get("content_length", 0) for chunk in chunks]
            legal_chunks = [chunk for chunk in chunks if chunk["metadata"].get("has_legal_context", False)]
            
            return {
                "document_id": document_id,
                "total_chunks": len(chunks),
                "legal_chunks": len(legal_chunks),
                "avg_chunk_length": sum(chunk_lengths) / len(chunk_lengths) if chunk_lengths else 0,
                "min_chunk_length": min(chunk_lengths) if chunk_lengths else 0,
                "max_chunk_length": max(chunk_lengths) if chunk_lengths else 0,
                "total_content_length": sum(chunk_lengths)
            }
            
        except Exception as e:
            self.logger.error(f"Stats error: {str(e)}")
            return {"error": str(e)}
    
    async def delete_document(self, document_id: str) -> bool:
        """Delete document using async operations"""
        vector_deleted = await self.vector_storage.delete_document(document_id)
        elasticsearch_deleted = True
        if self.elasticsearch:
            elasticsearch_deleted = await self.elasticsearch.delete_document(document_id)
        return vector_deleted and elasticsearch_deleted
    
    async def list_documents(self) -> List[str]:
        """List documents using async operations"""
        return await self.vector_storage.list_documents()
    
    async def get_pipeline_stats(self) -> Dict[str, Any]:
        """Get pipeline statistics using async operations"""
        storage_stats = await self.vector_storage.get_collection_stats()
        
        stats = {
            "embedding_model": self.embedding_service.config.model,
            "embedding_dimension": self.embedding_service.get_embedding_dimension(),
            "chunking_strategy": self.chunking_service.chunk_config.strategy.value,
            "chunk_size": self.chunking_service.chunk_config.chunk_size,
            "chunk_overlap": self.chunking_service.chunk_config.chunk_overlap,
            "elasticsearch_enabled": self.elasticsearch is not None,
            **storage_stats
        }
        
        if self.elasticsearch:
            elasticsearch_stats = await self.elasticsearch.get_index_stats()
            stats.update({"elasticsearch": elasticsearch_stats})
        
        return stats
    
    async def search_text(self, 
                   query: str,
                   size: int = 10,
                   document_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search text using async operations"""
        if not self.elasticsearch:
            return []
        
        return await self.elasticsearch.search_text(
            query=query,
            size=size,
            document_id=document_id
        )
    
    async def search_legal_content(self, 
                           query: str,
                           content_type: str = "all",
                           size: int = 10) -> List[Dict[str, Any]]:
        """Search legal content using async operations"""
        if not self.elasticsearch:
            return []
        
        return await self.elasticsearch.search_legal_content(
            query=query,
            content_type=content_type,
            size=size
        )