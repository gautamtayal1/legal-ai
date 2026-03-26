import os
import logging
import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from sqlalchemy import create_engine, text
from langchain_postgres import PGVector
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

from ..chunking.base import DocumentChunk


def _build_connection_string() -> str:
    """Build PostgreSQL connection string with psycopg2 driver."""
    database_url = os.getenv("DATABASE_URL", "")
    if database_url:
        if database_url.startswith("postgresql://"):
            return database_url.replace("postgresql://", "postgresql+psycopg2://", 1)
        return database_url
    user = os.getenv("POSTGRES_USER", "inquire_user")
    password = os.getenv("POSTGRES_PASSWORD", "inquire_pass")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "inquire_db")
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"


@dataclass
class VectorStorageConfig:
    collection_name: str = "legal_documents"
    distance_metric: str = "cosine"
    max_results: int = 50


class VectorStorageService:
    def __init__(self, config: Optional[VectorStorageConfig] = None, embedding_function=None):
        self.config = config or VectorStorageConfig()
        self.logger = logging.getLogger(__name__)
        self._connection_string = _build_connection_string()

        if embedding_function is None:
            embedding_function = OpenAIEmbeddings()

        self.vectorstore = PGVector(
            embeddings=embedding_function,
            collection_name=self.config.collection_name,
            connection=self._connection_string,
            use_jsonb=True,
        )

        self.logger.info("Connected to pgvector via PostgreSQL")

    async def store_embeddings(self, embedded_chunks: List[Dict[str, Any]]) -> bool:
        """Store embeddings using LangChain PGVector"""
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
        """Search similar embeddings using LangChain PGVector"""
        try:
            n_results = n_results or min(10, self.config.max_results)

            filter_dict = {}
            if document_id:
                filter_dict["document_id"] = document_id
            if filters:
                filter_dict.update(filters)

            docs_with_scores = self.vectorstore.similarity_search_by_vector_with_relevance_scores(
                embedding=query_embedding,
                k=n_results,
                filter=filter_dict if filter_dict else None
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
        """Delete document chunks for a given document ID"""
        try:
            engine = create_engine(self._connection_string)
            with engine.connect() as conn:
                conn.execute(
                    text("""
                        DELETE FROM langchain_pg_embedding
                        WHERE collection_id = (
                            SELECT uuid FROM langchain_pg_collection WHERE name = :name
                        )
                        AND cmetadata->>'document_id' = :document_id
                    """),
                    {"name": self.config.collection_name, "document_id": document_id}
                )
                conn.commit()
            self.logger.info(f"Deleted chunks for document {document_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to delete document chunks: {str(e)}")
            return False

    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        try:
            engine = create_engine(self._connection_string)
            with engine.connect() as conn:
                count = conn.execute(
                    text("""
                        SELECT COUNT(*)
                        FROM langchain_pg_embedding e
                        JOIN langchain_pg_collection c ON e.collection_id = c.uuid
                        WHERE c.name = :name
                    """),
                    {"name": self.config.collection_name}
                ).scalar()

            return {
                "total_chunks": count or 0,
                "collection_name": self.config.collection_name,
                "distance_metric": self.config.distance_metric
            }

        except Exception as e:
            self.logger.error(f"Failed to get collection stats: {str(e)}")
            return {}

    async def list_documents(self) -> List[str]:
        """List all document IDs stored in the collection"""
        try:
            engine = create_engine(self._connection_string)
            with engine.connect() as conn:
                rows = conn.execute(
                    text("""
                        SELECT DISTINCT e.cmetadata->>'document_id'
                        FROM langchain_pg_embedding e
                        JOIN langchain_pg_collection c ON e.collection_id = c.uuid
                        WHERE c.name = :name
                          AND e.cmetadata->>'document_id' IS NOT NULL
                    """),
                    {"name": self.config.collection_name}
                ).fetchall()
            return [row[0] for row in rows]

        except Exception as e:
            self.logger.error(f"Failed to list documents: {str(e)}")
            return []

    def store_embeddings_sync(self, embedded_chunks: List[Dict[str, Any]]) -> bool:
        return asyncio.run(self.store_embeddings(embedded_chunks))

    def search_similar_sync(self, query_embedding: List[float], **kwargs) -> List[Dict[str, Any]]:
        return asyncio.run(self.search_similar(query_embedding, **kwargs))

    async def close(self):
        """Close connection - kept for compatibility"""
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
