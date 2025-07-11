import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import NotFoundError, RequestError

from ..document_processing.chunking.base import DocumentChunk


@dataclass
class ElasticsearchConfig:
    host: str = "localhost"
    port: int = 9200
    index_name: str = "legal_documents"
    timeout: int = 30


class ElasticsearchService:
    def __init__(self, config: Optional[ElasticsearchConfig] = None):
        self.config = config or ElasticsearchConfig()
        self.logger = logging.getLogger(__name__)
        
        self.client = Elasticsearch(
            hosts=[{"host": self.config.host, "port": self.config.port}],
            timeout=self.config.timeout
        )
        
        self._create_index()
    
    def _create_index(self):
        if not self.client.indices.exists(index=self.config.index_name):
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
            
            self.client.indices.create(
                index=self.config.index_name,
                body=mapping
            )
            self.logger.info(f"Created index: {self.config.index_name}")
    
    def index_chunks(self, chunks: List[DocumentChunk]) -> bool:
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
            
            from elasticsearch.helpers import bulk
            success, failed = bulk(self.client, docs, refresh=True)
            
            self.logger.info(f"Indexed {success} chunks successfully")
            if failed:
                self.logger.warning(f"Failed to index {len(failed)} chunks")
            
            return len(failed) == 0
            
        except Exception as e:
            self.logger.error(f"Failed to index chunks: {str(e)}")
            return False
    
    def search_text(self, 
                   query: str, 
                   size: int = 10,
                   document_id: Optional[str] = None,
                   filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        
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
        
        if document_id:
            search_body["query"]["bool"]["filter"] = [
                {"term": {"document_id": document_id}}
            ]
        
        if filters:
            filter_clauses = search_body["query"]["bool"].get("filter", [])
            for key, value in filters.items():
                filter_clauses.append({"term": {key: value}})
            search_body["query"]["bool"]["filter"] = filter_clauses
        
        try:
            response = self.client.search(
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
    
    def search_legal_content(self, 
                           query: str,
                           content_type: str = "all",
                           size: int = 10) -> List[Dict[str, Any]]:
        
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
            response = self.client.search(
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
    
    def get_document_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        try:
            response = self.client.get(
                index=self.config.index_name,
                id=doc_id
            )
            return response["_source"]
            
        except NotFoundError:
            return None
        except Exception as e:
            self.logger.error(f"Failed to get document: {str(e)}")
            return None
    
    def delete_document(self, document_id: str) -> bool:
        try:
            self.client.delete_by_query(
                index=self.config.index_name,
                body={"query": {"term": {"document_id": document_id}}},
                refresh=True
            )
            self.logger.info(f"Deleted document {document_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete document: {str(e)}")
            return False
    
    def get_index_stats(self) -> Dict[str, Any]:
        try:
            stats = self.client.indices.stats(index=self.config.index_name)
            count = self.client.count(index=self.config.index_name)
            
            return {
                "total_documents": count["count"],
                "index_size": stats["_all"]["total"]["store"]["size_in_bytes"],
                "index_name": self.config.index_name
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get index stats: {str(e)}")
            return {}
    
    def health_check(self) -> bool:
        try:
            health = self.client.cluster.health()
            return health["status"] in ["green", "yellow"]
        except Exception:
            return False