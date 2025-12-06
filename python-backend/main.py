"""
FastAPI application entry point for Local AI Brain chat integration.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import configuration - this will validate on import
from config import config

# Import rate limiter
from middleware.rate_limiter import limiter, rate_limit_exceeded_handler

# Import logging middleware
from middleware.logging_middleware import LoggingMiddleware

# Import brain manager
from services.brain_manager import brain_manager

# Import service manager
from services.service_manager import service_manager

# Create FastAPI application
app = FastAPI(
    title="StudyMate AI Chat API",
    description="FastAPI backend for Local AI Brain-powered chat functionality",
    version="1.0.0"
)

# Register rate limiter state
app.state.limiter = limiter

# Register custom rate limit exceeded handler
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# Register logging middleware
app.add_middleware(LoggingMiddleware)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register auth router
from routers.auth import router as auth_router
app.include_router(auth_router)

# Register academic router
from routers.academic import router as academic_router
app.include_router(academic_router)

# Register preferences router
from routers.preferences import router as preferences_router
app.include_router(preferences_router)

# Register profile router (legacy - kept for backward compatibility)
from routers.profile import router as profile_router
app.include_router(profile_router)

# Register courses router
from routers.courses import router as courses_router
app.include_router(courses_router)

# Register materials router
from routers.materials import router as materials_router
app.include_router(materials_router)

# Register chat router
from routers.chat import router as chat_router
app.include_router(chat_router)

# Register transcription router
from routers.transcribe import router as transcribe_router
app.include_router(transcribe_router)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "studymate-ai-chat"}

@app.get("/api/test-rate-limit")
@limiter.limit(f"{config.RATE_LIMIT_REQUESTS}/{config.RATE_LIMIT_WINDOW}seconds")
async def test_rate_limit(request: Request):
    """
    Test endpoint to verify rate limiting is working.
    This endpoint is rate-limited and will return 429 after exceeding the limit.
    """
    return {
        "message": "Rate limiter is working!",
        "limit": f"{config.RATE_LIMIT_REQUESTS} requests per {config.RATE_LIMIT_WINDOW} seconds"
    }

@app.on_event("startup")
async def startup_event():
    """Log startup confirmation and configuration status."""
    logger.info("=" * 60)
    logger.info("FastAPI backend starting up...")
    logger.info("=" * 60)
    logger.info("Configuration loaded successfully")
    logger.info(f"  - Rate Limiting: {config.RATE_LIMIT_REQUESTS} requests per {config.RATE_LIMIT_WINDOW}s")
    logger.info(f"  - CORS Allowed Origins: {', '.join(config.ALLOWED_ORIGINS)}")
    logger.info(f"  - AI Brain Endpoint: {config.AI_BRAIN_ENDPOINT}")
    logger.info("=" * 60)
    
    # Initialize services (AI Brain client, Material Processing Service)
    logger.info("Initializing services...")
    try:
        await service_manager.initialize()
        logger.info("✓ Services initialized successfully")
    except Exception as e:
        logger.error(f"✗ Error initializing services: {str(e)}")
        logger.warning("  Material processing features may not work correctly")
    
    # Start AI Brain Service
    logger.info("Starting AI Brain Service...")
    try:
        success = await brain_manager.start_brain()
        if success:
            logger.info("✓ AI Brain Service started successfully")
        else:
            logger.warning("✗ AI Brain Service failed to start - AI features will be disabled")
            logger.warning("  The backend will continue running without AI capabilities")
    except Exception as e:
        logger.error(f"✗ Error starting AI Brain Service: {str(e)}")
        logger.warning("  The backend will continue running without AI capabilities")
        logger.warning("  Check that Ollama is installed and running")
    
    logger.info("=" * 60)
    logger.info("StudyMate AI Chat API is ready to accept requests")
    logger.info("=" * 60)

@app.on_event("shutdown")
async def shutdown_event():
    """Gracefully shutdown services."""
    logger.info("=" * 60)
    logger.info("FastAPI backend shutting down...")
    logger.info("=" * 60)
    
    # Stop AI Brain Service
    logger.info("Stopping AI Brain Service...")
    try:
        await brain_manager.stop_brain()
        logger.info("✓ AI Brain Service stopped successfully")
    except Exception as e:
        logger.error(f"✗ Error stopping AI Brain Service: {str(e)}")
    
    logger.info("=" * 60)
    logger.info("Shutdown complete")
    logger.info("=" * 60)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
