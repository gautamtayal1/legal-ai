import logging
import os
import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from elasticsearch import AsyncElasticsearch
from elasticsearch.exceptions import NotFoundError, RequestError

from ..chunking.base import DocumentChunk


@dataclass
class ElasticsearchConfig:
    host: str = os.getenv("ELASTICSEARCH_HOST", "localhost")
    port: int = int(os.getenv("ELASTICSEARCH_PORT", "9200"))
    index_name: str = "legal_documents"
    timeout: int = 30


class ElasticsearchService:
    def __init__(self, config: Optional[ElasticsearchConfig] = None):
        self.config = config or ElasticsearchConfig()
        self.logger = logging.getLogger(__name__)
        
        self.client = AsyncElasticsearch(
            hosts=[f"http://{self.config.host}:{self.config.port}"],
            timeout=self.config.timeout
        )
        
        self._index_initialized = False
        self._init_lock = asyncio.Lock()
    
    async def _create_index(self):
        """Create index if it doesn't exist (thread-safe)"""
        async with self._init_lock:
            if self._index_initialized:
                return
                
            try:
                exists = await self.client.indices.exists(index=self.config.index_name)
                if exists:
                    self.logger.info(f"Index {self.config.index_name} exists")
                    self._index_initialized = True
                    return
                    
                mapping = {
                    "mappings": {
                        "properties": {
                            "content": {"type": "text", "analyzer": "standard"},
                            "document_id": {"type": "keyword"},
                            "chunk_id": {"type": "keyword"},
                            "chunk_index": {"type": "integer"},
                            "start_position": {"type": "integer"},
                            "end_position": {"type": "integer"},
                            "parent_section": {"type": "keyword"},
                            "document_type": {"type": "keyword"},
                            "practice_area": {"type": "keyword"},
                            "date_created": {"type": "date"},
                            "has_legal_context": {"type": "boolean"},
                            "legal_definitions": {"type": "text"},
                            "legal_obligations": {"type": "text"},
                            "legal_parties": {"type": "text"},
                            "content_length": {"type": "integer"}
                        }
                    }
                }
                
                await self.client.indices.create(
                    index=self.config.index_name,
                    body=mapping
                )
                self.logger.info(f"Created index: {self.config.index_name}")
                self._index_initialized = True
            except Exception as e:
                self.logger.error(f"Failed to create index: {str(e)}")
    
    async def index_chunks(self, chunks: List[DocumentChunk]) -> bool:
        """Index chunks asynchronously"""
        await self._create_index()
            
        try:
            docs = []
            for chunk in chunks:
                doc = {
                    "_index": self.config.index_name,
                    "_id": chunk.id,
                    "_source": {
                        "content": chunk.content,
                        "document_id": chunk.document_id,
                        "chunk_id": chunk.id,
                        "chunk_index": chunk.chunk_index,
                        "start_position": chunk.start_position,
                        "end_position": chunk.end_position,
                        "parent_section": chunk.parent_section or "",
                        "content_length": len(chunk.content),
                        **chunk.metadata
                    }
                }
                
                if chunk.legal_context:
                    doc["_source"]["has_legal_context"] = True
                    legal_ctx = chunk.legal_context
                    if isinstance(legal_ctx, dict):
                        doc["_source"]["legal_definitions"] = str(legal_ctx.get("definitions", ""))
                        doc["_source"]["legal_obligations"] = str(legal_ctx.get("obligations", ""))
                        doc["_source"]["legal_parties"] = str(legal_ctx.get("parties", ""))
                
                docs.append(doc)
            
            from elasticsearch.helpers import async_bulk
            success, failed = await async_bulk(self.client, docs, refresh=True)
            
            self.logger.info(f"Indexed {success} chunks successfully")
            if failed:
                self.logger.warning(f"Failed to index {len(failed)} chunks")
            
            return len(failed) == 0
            
        except Exception as e:
            self.logger.error(f"Failed to index chunks: {str(e)}")
            return False

    async def search_text(self, 
                   query: str, 
                   size: int = 10,
                   document_id: Optional[str] = None,
                   document_ids: Optional[List[str]] = None,
                   filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search text asynchronously"""
        # Ensure index exists before searching
        await self._create_index()
            
        search_body = {
            "query": {
                "bool": {
                    "must": [
                        {"match": {"content": query}}
                    ]
                }
            },
            "size": size,
            "highlight": {
                "fields": {"content": {}}
            }
        }
        
        # Handle document filtering
        filter_clauses = []
        
        if document_id:
            filter_clauses.append({"term": {"document_id": document_id}})
        elif document_ids:
            filter_clauses.append({"terms": {"document_id": document_ids}})
        
        if filters:
            for key, value in filters.items():
                if key == "document_id":
                    # Handle multiple document IDs from filters
                    if isinstance(value, dict) and "$in" in value:
                        filter_clauses.append({"terms": {key: value["$in"]}})
                    else:
                        filter_clauses.append({"term": {key: value}})
                else:
                    filter_clauses.append({"term": {key: value}})
        
        if filter_clauses:
            search_body["query"]["bool"]["filter"] = filter_clauses
        
        try:
            response = await self.client.search(
                index=self.config.index_name,
                body=search_body
            )
            
            results = []
            for hit in response["hits"]["hits"]:
                result = {
                    "id": hit["_id"],
                    "score": hit["_score"],
                    "content": hit["_source"]["content"],
                    "metadata": hit["_source"],
                    "highlights": hit.get("highlight", {})
                }
                results.append(result)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Search failed: {str(e)}")
            return []

    async def search_legal_content(self, 
                           query: str,
                           content_type: str = "all",
                           size: int = 10) -> List[Dict[str, Any]]:
        """Search legal content asynchronously"""
        
        search_fields = []
        if content_type == "definitions" or content_type == "all":
            search_fields.append("legal_definitions")
        if content_type == "obligations" or content_type == "all":
            search_fields.append("legal_obligations")
        if content_type == "parties" or content_type == "all":
            search_fields.append("legal_parties")
        if content_type == "all":
            search_fields.append("content")
        
        search_body = {
            "query": {
                "bool": {
                    "must": [
                        {"multi_match": {
                            "query": query,
                            "fields": search_fields
                        }}
                    ],
                    "filter": [
                        {"term": {"has_legal_context": True}}
                    ]
                }
            },
            "size": size
        }
        
        try:
            response = await self.client.search(
                index=self.config.index_name,
                body=search_body
            )
            
            results = []
            for hit in response["hits"]["hits"]:
                results.append({
                    "id": hit["_id"],
                    "score": hit["_score"],
                    "content": hit["_source"]["content"],
                    "metadata": hit["_source"]
                })
            
            return results
            
        except Exception as e:
            self.logger.error(f"Legal content search failed: {str(e)}")
            return []

    async def get_document_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        try:
            response = await self.client.get(
                index=self.config.index_name,
                id=doc_id
            )
            return response["_source"]
            
        except NotFoundError:
            return None
        except Exception as e:
            self.logger.error(f"Failed to get document: {str(e)}")
            return None

    async def delete_document(self, document_id: str) -> bool:
        """Delete document asynchronously"""
        try:
            await self.client.delete_by_query(
                index=self.config.index_name,
                body={"query": {"term": {"document_id": document_id}}},
                refresh=True
            )
            self.logger.info(f"Deleted document {document_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete document: {str(e)}")
            return False

    async def get_index_stats(self) -> Dict[str, Any]:
        """Get index statistics asynchronously"""
        try:
            stats = await self.client.indices.stats(index=self.config.index_name)
            count = await self.client.count(index=self.config.index_name)
            
            return {
                "total_documents": count["count"],
                "index_size": stats["_all"]["total"]["store"]["size_in_bytes"],
                "index_name": self.config.index_name
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get index stats: {str(e)}")
            return {}

    async def health_check(self) -> bool:
        """Check Elasticsearch health asynchronously"""
        try:
            health = await self.client.cluster.health()
            return health["status"] in ["green", "yellow"]
        except Exception:
            return False

    # Sync wrappers for backward compatibility
    def index_chunks_sync(self, chunks: List[DocumentChunk]) -> bool:
        """Sync wrapper for backward compatibility"""
        return asyncio.run(self.index_chunks(chunks))
    
    def search_text_sync(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """Sync wrapper for backward compatibility"""
        return asyncio.run(self.search_text(query, **kwargs))
    
    def delete_document_sync(self, document_id: str) -> bool:
        """Sync wrapper for backward compatibility"""
        return asyncio.run(self.delete_document(document_id))

    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.close()