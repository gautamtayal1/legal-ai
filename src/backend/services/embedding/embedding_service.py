import asyncio
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import openai
from openai import AsyncOpenAI

from ..document_processing.chunking.base import DocumentChunk


@dataclass
class EmbeddingConfig:
    model: str = "text-embedding-3-small"
    dimensions: Optional[int] = None
    batch_size: int = 100
    max_retries: int = 3
    retry_delay: float = 1.0


class EmbeddingService:
    def __init__(self, api_key: str, config: Optional[EmbeddingConfig] = None):
        self.client = AsyncOpenAI(api_key=api_key)
        self.config = config or EmbeddingConfig()
        self.logger = logging.getLogger(__name__)
    
    async def embed_text(self, text: str) -> List[float]:
        try:
            response = await self.client.embeddings.create(
                model=self.config.model,
                input=text,
                dimensions=self.config.dimensions
            )
            return response.data[0].embedding
        except Exception as e:
            self.logger.error(f"Failed to embed text: {str(e)}")
            raise
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        
        embeddings = []
        for i in range(0, len(texts), self.config.batch_size):
            batch = texts[i:i + self.config.batch_size]
            batch_embeddings = await self._embed_batch(batch)
            embeddings.extend(batch_embeddings)
        
        return embeddings
    
    async def _embed_batch(self, texts: List[str]) -> List[List[float]]:
        for attempt in range(self.config.max_retries):
            try:
                response = await self.client.embeddings.create(
                    model=self.config.model,
                    input=texts,
                    dimensions=self.config.dimensions
                )
                return [item.embedding for item in response.data]
            except Exception as e:
                if attempt == self.config.max_retries - 1:
                    self.logger.error(f"Failed to embed batch after {self.config.max_retries} attempts: {str(e)}")
                    raise
                await asyncio.sleep(self.config.retry_delay * (2 ** attempt))
    
    async def embed_chunks(self, chunks: List[DocumentChunk]) -> List[Dict[str, Any]]:
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
        return await self.embed_text(query)
    
    def get_embedding_dimension(self) -> int:
        if self.config.dimensions:
            return self.config.dimensions
        
        model_dimensions = {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536
        }
        
        return model_dimensions.get(self.config.model, 1536)