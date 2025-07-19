from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
import asyncio
from contextlib import asynccontextmanager

from api.routers import documents
from api.routers import clerk_webhooks  
from api.routers import threads
from api.routers import messages
from api.routers import query

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_services = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting Legal AI - Inquire API")
    
    try:
        from services.document_processing.embedding.vector_storage_service import VectorStorageService
        from services.document_processing.search_engine.elasticsearch_service import ElasticsearchService
        
        try:
            _services["vector_storage"] = VectorStorageService()
            logger.info("✅ VectorStorageService initialized")
        except Exception as e:
            logger.warning(f"⚠️ VectorStorageService not available: {e}")
            _services["vector_storage"] = None
            
        try:
            _services["elasticsearch"] = ElasticsearchService()
            logger.info("✅ ElasticsearchService initialized")
        except Exception as e:
            logger.warning(f"⚠️ ElasticsearchService not available: {e}")
            _services["elasticsearch"] = None
        
        logger.info("✅ Application startup completed")
        
        yield
        
    finally:
        logger.info("🔄 Shutting down services...")
        
        try:
            if "vector_storage" in _services and _services["vector_storage"]:
                await _services["vector_storage"].close()
                
            if "elasticsearch" in _services and _services["elasticsearch"]:
                await _services["elasticsearch"].client.close()
                
            logger.info("✅ Services shut down successfully")
        except Exception as e:
            logger.error(f"❌ Error during shutdown: {e}")

app = FastAPI(
    title="Legal AI - Inquire", 
    version="1.0.0",
    description="Legal document analysis and AI processing system",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    allow_credentials=True,
)

app.include_router(documents.router, prefix="/api")
app.include_router(clerk_webhooks.router, prefix="/api")
app.include_router(threads.router, prefix="/api")
app.include_router(messages.router, prefix="/api")
app.include_router(query.router, prefix="/api")

@app.get("/")
async def root():
    return {
        "message": "Legal AI - Inquire API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "documents": "/api/documents",
            "clerk_webhook": "/webhooks",
            "threads": "/api/threads",
            "messages": "/api/messages",
            "query": "/api/query"
        }
    }

@app.get("/health")
async def health_check():
    status = {"service": "inquire", "status": "healthy"}
    
    health_checks = {}
    
    try:
        if "vector_storage" in _services and _services["vector_storage"]:
            health_checks["chromadb"] = "connected"
        else:
            health_checks["chromadb"] = "not_available"
            
        if "elasticsearch" in _services and _services["elasticsearch"]:
            es_health = await _services["elasticsearch"].health_check()
            health_checks["elasticsearch"] = "healthy" if es_health else "unhealthy"
        else:
            health_checks["elasticsearch"] = "not_available"
            
    except Exception as e:
        logger.error(f"Health check error: {e}")
        health_checks["error"] = str(e)
        status["status"] = "degraded"
    
    status["services"] = health_checks
    return status

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception: {exc}")
    raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)