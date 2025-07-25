import os
import logging
import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import chromadb
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

from ..chunking.base import DocumentChunk


@dataclass
class VectorStorageConfig:
    host: str = os.getenv("CHROMADB_HOST", "localhost")
    port: int = int(os.getenv("CHROMADB_PORT", "8080"))
    collection_name: str = "legal_documents"
    distance_metric: str = "cosine"
    max_results: int = 50


class VectorStorageService:
    def __init__(self, config: Optional[VectorStorageConfig] = None, embedding_function=None):
        self.config = config or VectorStorageConfig()
        self.logger = logging.getLogger(__name__)
        
        self.chroma_client = chromadb.HttpClient(
            host=self.config.host,
            port=self.config.port
        )
        
        if embedding_function is None:
            embedding_function = OpenAIEmbeddings()
        
        self.vectorstore = Chroma(
            client=self.chroma_client,
            collection_name=self.config.collection_name,
            embedding_function=embedding_function,
            collection_metadata={"hnsw:space": self.config.distance_metric}
        )
        
        self.logger.info(f"Connected to self-hosted ChromaDB at {self.config.host}:{self.config.port}")

    async def store_embeddings(self, embedded_chunks: List[Dict[str, Any]]) -> bool:
        """Store embeddings using LangChain Chroma"""
        try:
            documents = []
            ids = []
            
            for item in embedded_chunks:
                chunk = item["chunk"]
                
                doc_metadata = {
                    "document_id": chunk.document_id,
                    "chunk_index": chunk.chunk_index,
                    "start_position": chunk.start_position,
                    "end_position": chunk.end_position,
                    "content_length": len(chunk.content),
                    "parent_section": chunk.parent_section or "",
                    **chunk.metadata
                }
                
                if chunk.legal_context:
                    doc_metadata.update({
                        "has_legal_context": True,
                        "legal_context": str(chunk.legal_context)
                    })
                
                doc_metadata = self._ensure_json_serializable(doc_metadata)
                
                doc_metadata = self._filter_chromadb_metadata(doc_metadata)
                
                doc = Document(
                    page_content=chunk.content,
                    metadata=doc_metadata
                )
                
                documents.append(doc)
                ids.append(chunk.id)
            
            self.vectorstore.add_documents(documents, ids=ids)
            
            self.logger.info(f"Stored {len(embedded_chunks)} embeddings successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to store embeddings: {str(e)}")
            return False

    async def search_similar(self, 
                    query_embedding: List[float], 
                    n_results: Optional[int] = None,
                    document_id: Optional[str] = None,
                    filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search similar embeddings using LangChain Chroma"""
        try:
            n_results = n_results or min(10, self.config.max_results)
            
            where_filter = {}
            if document_id:
                where_filter["document_id"] = document_id
            if filters:
                if "document_id" in filters:
                    doc_filter = filters["document_id"]
                    if isinstance(doc_filter, dict) and "$in" in doc_filter:
                        where_filter["document_id"] = {"$in": doc_filter["$in"]}
                    else:
                        where_filter["document_id"] = doc_filter
                for key, value in filters.items():
                    if key != "document_id":
                        where_filter[key] = value
            
            docs_with_scores = self.vectorstore.similarity_search_by_vector_with_relevance_scores(
                embedding=query_embedding,
                k=n_results,
                filter=where_filter if where_filter else None
            )
            
            search_results = []
            for doc, score in docs_with_scores:
                search_results.append({
                    "id": doc.metadata.get("chunk_id", ""),
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "similarity": score,
                    "distance": 1 - score
                })
            
            return search_results
            
        except Exception as e:
            self.logger.error(f"Failed to search similar chunks: {str(e)}")
            return []

    async def delete_document(self, document_id: str) -> bool:
        """Delete document chunks using LangChain Chroma"""
        try:
            all_docs = self.vectorstore.get(where={"document_id": document_id})
            
            if all_docs["ids"]:
                self.vectorstore.delete(ids=all_docs["ids"])
                self.logger.info(f"Deleted {len(all_docs['ids'])} chunks for document {document_id}")
            
            return True
                
        except Exception as e:
            self.logger.error(f"Failed to delete document chunks: {str(e)}")
            return False

    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics using LangChain Chroma"""
        try:
            collection = self.vectorstore._collection
            count = collection.count()
            
            return {
                "total_chunks": count,
                "collection_name": self.config.collection_name,
                "distance_metric": self.config.distance_metric
            }
                
        except Exception as e:
            self.logger.error(f"Failed to get collection stats: {str(e)}")
            return {}

    async def list_documents(self) -> List[str]:
        """List all document IDs using LangChain Chroma"""
        try:
            all_docs = self.vectorstore.get(include=["metadatas"])
            
            document_ids = set()
            for metadata in all_docs["metadatas"]:
                if "document_id" in metadata:
                    document_ids.add(metadata["document_id"])
            
            return list(document_ids)
                
        except Exception as e:
            self.logger.error(f"Failed to list documents: {str(e)}")
            return []

    def store_embeddings_sync(self, embedded_chunks: List[Dict[str, Any]]) -> bool:
        return asyncio.run(self.store_embeddings(embedded_chunks))
    
    def search_similar_sync(self, query_embedding: List[float], **kwargs) -> List[Dict[str, Any]]:
        return asyncio.run(self.search_similar(query_embedding, **kwargs))
    
    async def close(self):
        """Close connection - not needed for LangChain but kept for compatibility"""
        pass

    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    def _ensure_json_serializable(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure all metadata values are JSON serializable"""
        serializable_metadata = {}
        for key, value in metadata.items():
            try:
                if hasattr(value, 'value'):  
                    serializable_metadata[key] = value.value
                elif isinstance(value, (str, int, float, bool, type(None))):
                    serializable_metadata[key] = value
                elif isinstance(value, (list, tuple)):
                    serializable_metadata[key] = [
                        item.value if hasattr(item, 'value') else str(item) 
                        for item in value
                    ]
                elif isinstance(value, dict):
                    serializable_metadata[key] = self._ensure_json_serializable(value)
                else:
                    serializable_metadata[key] = str(value)
            except Exception:
                serializable_metadata[key] = str(value)
        return serializable_metadata

    def _filter_chromadb_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Filter metadata to only include types supported by ChromaDB (str, int, float, bool, None)"""
        filtered_metadata = {}
        for key, value in metadata.items():
            if isinstance(value, (str, int, float, bool, type(None))):
                filtered_metadata[key] = value
            else:
                filtered_metadata[key] = str(value)
        return filtered_metadata