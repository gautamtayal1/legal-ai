import uuid
import logging
import os
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import chromadb
from chromadb.config import Settings

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
        
        # Use HTTP client to connect to ChromaDB Docker service
        self.client = chromadb.HttpClient(
            host=self.config.host,
            port=self.config.port,
            settings=Settings(anonymized_telemetry=False)
        )
        
        self.collection = self._get_or_create_collection()
    
    def _get_or_create_collection(self):
        try:
            return self.client.get_collection(
                name=self.config.collection_name
            )
        except Exception:
            return self.client.create_collection(
                name=self.config.collection_name,
                metadata={"hnsw:space": self.config.distance_metric}
            )
    
    def store_embeddings(self, embedded_chunks: List[Dict[str, Any]]) -> bool:
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
            
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )
            
            self.logger.info(f"Stored {len(embedded_chunks)} embeddings successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to store embeddings: {str(e)}")
            return False
    
    def search_similar(self, 
                    query_embedding: List[float], 
                    n_results: Optional[int] = None,
                    document_id: Optional[str] = None,
                    filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        
        n_results = n_results or min(10, self.config.max_results)
        
        where_clause = {}
        if document_id:
            where_clause["document_id"] = document_id
        if filters:
            where_clause.update(filters)
        
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where_clause if where_clause else None,
                include=["documents", "metadatas", "distances"]
            )
            
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
            
        except Exception as e:
            self.logger.error(f"Failed to search similar chunks: {str(e)}")
            return []
    
    def get_chunk_by_id(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        try:
            result = self.collection.get(
                ids=[chunk_id],
                include=["documents", "metadatas"]
            )
            
            if result["ids"]:
                return {
                    "id": result["ids"][0],
                    "content": result["documents"][0],
                    "metadata": result["metadatas"][0]
                }
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get chunk by ID: {str(e)}")
            return None
    
    def delete_document(self, document_id: str) -> bool:
        try:
            self.collection.delete(
                where={"document_id": document_id}
            )
            self.logger.info(f"Deleted all chunks for document {document_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete document chunks: {str(e)}")
            return False
    
    def delete_chunk(self, chunk_id: str) -> bool:
        try:
            self.collection.delete(ids=[chunk_id])
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete chunk: {str(e)}")
            return False
    
    def get_collection_stats(self) -> Dict[str, Any]:
        try:
            count = self.collection.count()
            return {
                "total_chunks": count,
                "collection_name": self.config.collection_name,
                "distance_metric": self.config.distance_metric
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get collection stats: {str(e)}")
            return {}
    
    def list_documents(self) -> List[str]:
        try:
            results = self.collection.get(
                include=["metadatas"]
            )
            
            document_ids = set()
            for metadata in results["metadatas"]:
                if "document_id" in metadata:
                    document_ids.add(metadata["document_id"])
            
            return list(document_ids)
            
        except Exception as e:
            self.logger.error(f"Failed to list documents: {str(e)}")
            return []
    
    def update_chunk_metadata(self, chunk_id: str, metadata: Dict[str, Any]) -> bool:
        try:
            self.collection.update(
                ids=[chunk_id],
                metadatas=[metadata]
            )
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update chunk metadata: {str(e)}")
            return False