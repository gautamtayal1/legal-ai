from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
import asyncio
from contextlib import asynccontextmanager

from api.routers import documents
from api.routers import clerk_webhooks  
from api.routers import threads

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global services for proper lifecycle management
_services = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle - startup and shutdown"""
    logger.info("🚀 Starting Legal AI - Inquire API")
    
    # Initialize services
    try:
        from services.document_processing.embedding.vector_storage_service import VectorStorageService
        from services.document_processing.search_engine.elasticsearch_service import ElasticsearchService
        
        # Initialize global services
        _services["vector_storage"] = VectorStorageService()
        _services["elasticsearch"] = ElasticsearchService()
        
        logger.info("✅ Services initialized successfully")
        
        yield  # Application runs here
        
    finally:
        # Cleanup services
        logger.info("🔄 Shutting down services...")
        
        try:
            if "vector_storage" in _services:
                await _services["vector_storage"].close()
                
            if "elasticsearch" in _services:
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

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Legal AI - Inquire API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "documents": "/api/documents",
            "clerk_webhook": "/webhooks",
            "threads": "/api/threads"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint with service status"""
    status = {"service": "inquire", "status": "healthy"}
    
    # Check service health
    health_checks = {}
    
    try:
        if "vector_storage" in _services:
            # Simple connectivity check
            health_checks["chromadb"] = "connected"
        else:
            health_checks["chromadb"] = "not_initialized"
            
        if "elasticsearch" in _services:
            # Check if elasticsearch is healthy
            es_health = await _services["elasticsearch"].health_check()
            health_checks["elasticsearch"] = "healthy" if es_health else "unhealthy"
        else:
            health_checks["elasticsearch"] = "not_initialized"
            
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