import uuid
import logging
import os
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import httpx

from ..chunking.base import DocumentChunk


@dataclass
class VectorStorageConfig:
    host: str = os.getenv("CHROMADB_HOST", "localhost")
    port: int = int(os.getenv("CHROMADB_PORT", "8000"))
    collection_name: str = "legal_documents"
    distance_metric: str = "cosine"
    max_results: int = 50


class VectorStorageService:
    def __init__(self, config: Optional[VectorStorageConfig] = None):
        self.config = config or VectorStorageConfig()
        self.logger = logging.getLogger(__name__)
        self.base_url = f"http://{self.config.host}:{self.config.port}/api/v1"
        self._collection_initialized = False
    
    async def _ensure_collection_exists(self):
        """Ensure the collection exists, create if it doesn't"""
        async with httpx.AsyncClient() as client:
            try:
                # Try to get collection
                response = await client.get(f"{self.base_url}/collections/{self.config.collection_name}")
                if response.status_code == 200:
                    self.logger.info(f"Collection {self.config.collection_name} exists")
                    return
            except Exception:
                pass
            
            try:
                # Create collection if it doesn't exist
                response = await client.post(
                    f"{self.base_url}/collections",
                    json={
                        "name": self.config.collection_name,
                        "metadata": {"hnsw:space": self.config.distance_metric}
                    }
                )
                if response.status_code in [200, 201]:
                    self.logger.info(f"Created collection {self.config.collection_name}")
                else:
                    self.logger.error(f"Failed to create collection: {response.text}")
            except Exception as e:
                self.logger.error(f"Error creating collection: {str(e)}")

    async def store_embeddings(self, embedded_chunks: List[Dict[str, Any]]) -> bool:
        """Store embeddings asynchronously using HTTP API"""
        # Ensure collection exists before storing
        if not self._collection_initialized:
            await self._ensure_collection_exists()
            self._collection_initialized = True
            
        try:
            ids = []
            embeddings = []
            documents = []
            metadatas = []
            
            for item in embedded_chunks:
                chunk = item["chunk"]
                embedding = item["embedding"]
                metadata = item.get("metadata", {})
                
                chunk_id = chunk.id or str(uuid.uuid4())
                
                ids.append(chunk_id)
                embeddings.append(embedding)
                documents.append(chunk.content)
                
                chunk_metadata = {
                    "document_id": chunk.document_id,
                    "chunk_index": chunk.chunk_index,
                    "start_position": chunk.start_position,
                    "end_position": chunk.end_position,
                    "content_length": len(chunk.content),
                    "parent_section": chunk.parent_section or "",
                    **metadata,
                    **chunk.metadata
                }
                
                if chunk.legal_context:
                    chunk_metadata.update({
                        "has_legal_context": True,
                        "legal_context": str(chunk.legal_context)
                    })
                
                metadatas.append(chunk_metadata)
            
            # Async HTTP call to ChromaDB
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/collections/{self.config.collection_name}/add",
                    json={
                        "ids": ids,
                        "embeddings": embeddings,
                        "documents": documents,
                        "metadatas": metadatas
                    }
                )
                
                if response.status_code in [200, 201]:
                    self.logger.info(f"Stored {len(embedded_chunks)} embeddings successfully")
                    return True
                else:
                    self.logger.error(f"Failed to store embeddings: {response.text}")
                    return False
            
        except Exception as e:
            self.logger.error(f"Failed to store embeddings: {str(e)}")
            return False

    async def search_similar(self, 
                    query_embedding: List[float], 
                    n_results: Optional[int] = None,
                    document_id: Optional[str] = None,
                    filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search similar embeddings asynchronously"""
        # Ensure collection exists before searching
        if not self._collection_initialized:
            await self._ensure_collection_exists()
            self._collection_initialized = True
            
        n_results = n_results or min(10, self.config.max_results)
        
        where_clause = {}
        if document_id:
            where_clause["document_id"] = document_id
        if filters:
            where_clause.update(filters)
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/collections/{self.config.collection_name}/query",
                    json={
                        "query_embeddings": [query_embedding],
                        "n_results": n_results,
                        "where": where_clause if where_clause else None,
                        "include": ["documents", "metadatas", "distances"]
                    }
                )
                
                if response.status_code == 200:
                    results = response.json()
                    
                    search_results = []
                    for i in range(len(results["ids"][0])):
                        search_results.append({
                            "id": results["ids"][0][i],
                            "content": results["documents"][0][i],
                            "metadata": results["metadatas"][0][i],
                            "distance": results["distances"][0][i],
                            "similarity": 1 - results["distances"][0][i]
                        })
                    
                    return search_results
                else:
                    self.logger.error(f"Search failed: {response.text}")
                    return []
            
        except Exception as e:
            self.logger.error(f"Failed to search similar chunks: {str(e)}")
            return []

    async def delete_document(self, document_id: str) -> bool:
        """Delete document chunks asynchronously"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/collections/{self.config.collection_name}/delete",
                    json={
                        "where": {"document_id": document_id}
                    }
                )
                
                if response.status_code == 200:
                    self.logger.info(f"Deleted all chunks for document {document_id}")
                    return True
                else:
                    self.logger.error(f"Failed to delete document: {response.text}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Failed to delete document chunks: {str(e)}")
            return False

    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics asynchronously"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/collections/{self.config.collection_name}/count"
                )
                
                if response.status_code == 200:
                    count = response.json()
                    return {
                        "total_chunks": count,
                        "collection_name": self.config.collection_name,
                        "distance_metric": self.config.distance_metric
                    }
                else:
                    self.logger.error(f"Failed to get stats: {response.text}")
                    return {}
                    
        except Exception as e:
            self.logger.error(f"Failed to get collection stats: {str(e)}")
            return {}

    async def list_documents(self) -> List[str]:
        """List all document IDs asynchronously"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/collections/{self.config.collection_name}/get",
                    json={
                        "include": ["metadatas"]
                    }
                )
                
                if response.status_code == 200:
                    results = response.json()
                    
                    document_ids = set()
                    for metadata in results["metadatas"]:
                        if "document_id" in metadata:
                            document_ids.add(metadata["document_id"])
                    
                    return list(document_ids)
                else:
                    self.logger.error(f"Failed to list documents: {response.text}")
                    return []
                    
        except Exception as e:
            self.logger.error(f"Failed to list documents: {str(e)}")
            return []

    # Keep synchronous methods for backward compatibility but call async versions
    def store_embeddings_sync(self, embedded_chunks: List[Dict[str, Any]]) -> bool:
        """Sync wrapper for backward compatibility"""
        return asyncio.run(self.store_embeddings(embedded_chunks))
    
    def search_similar_sync(self, query_embedding: List[float], **kwargs) -> List[Dict[str, Any]]:
        """Sync wrapper for backward compatibility"""
        return asyncio.run(self.search_similar(query_embedding, **kwargs))