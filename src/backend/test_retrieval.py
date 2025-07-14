"""
Test script for the document retrieval functionality.
Tests the complete retrieval pipeline (Steps 12-14).
"""

import asyncio
import logging
import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.document_processing.retrieval.query_processor import QueryProcessor
from services.document_processing.retrieval.hybrid_retriever import HybridRetriever, HybridSearchConfig
from services.document_processing.retrieval.answer_generator import AnswerGenerator
from services.document_processing.retrieval.retrieval_service import RetrievalService
from services.document_processing.embedding.vector_storage_service import VectorStorageService
from services.document_processing.search_engine.elasticsearch_service import ElasticsearchService

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_query_processor():
    """Test the query processor functionality."""
    logger.info("Testing Query Processor...")
    
    processor = QueryProcessor()
    
    # Test different types of queries
    test_queries = [
        "What are my termination rights?",
        "Define intellectual property in this contract",
        "Who is responsible for payment delays?",
        "What are the deadlines for deliverables?",
        "Can the company terminate early?"
    ]
    
    for query in test_queries:
        try:
            processed = await processor.process_query(query)
            logger.info(f"Query: {query}")
            logger.info(f"  Intent: {processed.intent.value}")
            logger.info(f"  Legal concepts: {processed.legal_concepts}")
            logger.info(f"  Entities: {processed.entities}")
            logger.info(f"  Confidence: {processed.confidence}")
            logger.info("---")
        except Exception as e:
            logger.error(f"Query processing failed for '{query}': {e}")

async def test_services_initialization():
    """Test that all services can be initialized properly."""
    logger.info("Testing Services Initialization...")
    
    try:
        # Test vector storage service
        vector_service = VectorStorageService()
        logger.info("✅ VectorStorageService initialized")
        
        # Test elasticsearch service
        elasticsearch_service = ElasticsearchService()
        logger.info("✅ ElasticsearchService initialized")
        
        # Test query processor
        query_processor = QueryProcessor()
        logger.info("✅ QueryProcessor initialized")
        
        # Test hybrid retriever
        hybrid_config = HybridSearchConfig()
        hybrid_retriever = HybridRetriever(
            vector_service=vector_service,
            elasticsearch_service=elasticsearch_service,
            query_processor=query_processor,
            config=hybrid_config
        )
        logger.info("✅ HybridRetriever initialized")
        
        # Test answer generator
        answer_generator = AnswerGenerator()
        logger.info("✅ AnswerGenerator initialized")
        
        # Test retrieval service
        retrieval_service = RetrievalService(
            vector_service=vector_service,
            elasticsearch_service=elasticsearch_service
        )
        logger.info("✅ RetrievalService initialized")
        
        return retrieval_service
        
    except Exception as e:
        logger.error(f"Service initialization failed: {e}")
        return None

async def test_health_checks():
    """Test health checks for all services."""
    logger.info("Testing Health Checks...")
    
    try:
        # Test Elasticsearch health
        elasticsearch_service = ElasticsearchService()
        es_health = await elasticsearch_service.health_check()
        logger.info(f"Elasticsearch health: {'✅ Healthy' if es_health else '❌ Unhealthy'}")
        
        # Test vector storage health
        vector_service = VectorStorageService()
        vector_stats = await vector_service.get_collection_stats()
        logger.info(f"Vector storage health: {'✅ Healthy' if vector_stats else '❌ Unhealthy'}")
        
        return es_health and bool(vector_stats)
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return False

async def test_mock_retrieval():
    """Test retrieval with mock data (if services are not available)."""
    logger.info("Testing Mock Retrieval...")
    
    try:
        # Initialize services
        retrieval_service = await test_services_initialization()
        if not retrieval_service:
            logger.warning("Services not available, skipping retrieval test")
            return
        
        # Test query
        test_query = "What are the termination conditions?"
        
        logger.info(f"Testing query: {test_query}")
        
        # Test search only (no answer generation)
        try:
            search_results = await retrieval_service.search_only(query=test_query)
            logger.info(f"Search returned {len(search_results)} results")
            
            if search_results:
                logger.info("Sample search result:")
                logger.info(f"  Content: {search_results[0]['content'][:100]}...")
                logger.info(f"  Score: {search_results[0]['score']}")
        except Exception as e:
            logger.warning(f"Search test failed: {e}")
        
        # Test full retrieval (with answer generation)
        try:
            retrieval_result = await retrieval_service.retrieve_answer(query=test_query)
            logger.info(f"Retrieval completed:")
            logger.info(f"  Answer: {retrieval_result.answer[:200]}...")
            logger.info(f"  Confidence: {retrieval_result.confidence}")
            logger.info(f"  Sources used: {retrieval_result.sources_used}")
            logger.info(f"  Processing time: {retrieval_result.processing_time:.2f}s")
        except Exception as e:
            logger.warning(f"Full retrieval test failed: {e}")
        
    except Exception as e:
        logger.error(f"Mock retrieval test failed: {e}")

async def main():
    """Run all tests."""
    logger.info("🚀 Starting Retrieval System Tests")
    logger.info("=" * 50)
    
    # Test 1: Query Processor
    await test_query_processor()
    
    # Test 2: Services Initialization
    await test_services_initialization()
    
    # Test 3: Health Checks
    services_healthy = await test_health_checks()
    
    # Test 4: Mock Retrieval (only if services are healthy)
    if services_healthy:
        await test_mock_retrieval()
    else:
        logger.warning("⚠️ Services not healthy, skipping retrieval tests")
        logger.info("To run full tests, ensure ChromaDB and Elasticsearch are running:")
        logger.info("  - ChromaDB: docker run -p 8080:8000 chromadb/chroma")
        logger.info("  - Elasticsearch: docker run -p 9200:9200 elasticsearch:8.8.0")
    
    logger.info("=" * 50)
    logger.info("✅ All tests completed!")

if __name__ == "__main__":
    asyncio.run(main())