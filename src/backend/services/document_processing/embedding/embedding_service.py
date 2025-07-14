import asyncio
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from langchain_openai import OpenAIEmbeddings

from ..chunking.base import DocumentChunk


@dataclass
class EmbeddingConfig:
    model: str = "text-embedding-3-small"
    dimensions: Optional[int] = None
    batch_size: int = 100
    max_retries: int = 3
    retry_delay: float = 1.0


class EmbeddingService:
    def __init__(self, api_key: str, config: Optional[EmbeddingConfig] = None):
        self.config = config or EmbeddingConfig()
        self.logger = logging.getLogger(__name__)
        
        # Initialize LangChain OpenAI embeddings
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=api_key,
            model=self.config.model,
            dimensions=self.config.dimensions,
            chunk_size=self.config.batch_size,
            max_retries=self.config.max_retries
        )
    
    async def embed_text(self, text: str) -> List[float]:
        """Embed a single text using LangChain OpenAI embeddings"""
        try:
            # LangChain embeddings are sync, but we can make them async-compatible
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(None, self.embeddings.embed_query, text)
            return embedding
        except Exception as e:
            self.logger.error(f"Failed to embed text: {str(e)}")
            raise
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple texts using LangChain OpenAI embeddings"""
        if not texts:
            return []
        
        try:
            # Use LangChain's built-in batching
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(None, self.embeddings.embed_documents, texts)
            return embeddings
        except Exception as e:
            self.logger.error(f"Failed to embed texts: {str(e)}")
            raise
    
    async def embed_chunks(self, chunks: List[DocumentChunk]) -> List[Dict[str, Any]]:
        """Embed document chunks and return structured data"""
        texts = [chunk.content for chunk in chunks]
        embeddings = await self.embed_texts(texts)
        
        embedded_chunks = []
        for chunk, embedding in zip(chunks, embeddings):
            embedded_chunks.append({
                "chunk": chunk,
                "embedding": embedding,
                "metadata": {
                    "document_id": chunk.document_id,
                    "chunk_id": chunk.id,
                    "chunk_index": chunk.chunk_index,
                    "content_length": len(chunk.content),
                    "embedding_model": self.config.model
                }
            })
        
        return embedded_chunks
    
    async def embed_query(self, query: str) -> List[float]:
        """Embed a query text"""
        return await self.embed_text(query)
    
    def get_embedding_dimension(self) -> int:
        """Get the embedding dimension for the model"""
        if self.config.dimensions:
            return self.config.dimensions
        
        # Default dimensions for OpenAI models
        model_dimensions = {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536
        }
        
        return model_dimensions.get(self.config.model, 1536)