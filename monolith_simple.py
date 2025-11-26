"""
Simplified monolithic application for Render deployment.
Focuses on API Gateway functionality with optional service initialization.
"""
import asyncio
import os
import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

logger = structlog.get_logger()

# Simple configuration
class Settings:
    VERSION = "1.0.0"
    CORS_ORIGINS = ["*"]
    DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://localhost/ogtool")
    PERPLEXITY_API_KEY = os.environ.get("PERPLEXITY_API_KEY", "")
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

settings = Settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for the monolith"""
    logger.info("Starting OGTool Monolith (Simplified)")

    # Initialize what we can
    try:
        # Try to import and initialize services
        from services.shared.internal_queue import init_mq, close_mq
        await init_mq()
        logger.info("Internal queue initialized")
    except Exception as e:
        logger.warning(f"Could not initialize internal queue: {e}")

    yield

    logger.info("Shutting down OGTool Monolith")
    try:
        await close_mq()
    except:
        pass

# Create the main FastAPI app
app = FastAPI(
    title="OGTool Monolith",
    description="AI-powered lead generation platform API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(
        "Unhandled exception",
        path=request.url.path,
        method=request.method,
        error=str(exc),
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "OGTool Monolith",
        "version": settings.VERSION,
        "status": "operational",
        "docs": "/docs",
        "message": "Simplified deployment - core API only"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "ogtool-monolith",
        "version": settings.VERSION,
        "perplexity_configured": bool(settings.PERPLEXITY_API_KEY),
        "gemini_configured": bool(settings.GEMINI_API_KEY)
    }

@app.get("/api/v1/status")
async def api_status():
    """API status endpoint"""
    return {
        "api_version": "v1",
        "status": "operational",
        "available_endpoints": [
            "/",
            "/health",
            "/docs",
            "/redoc",
            "/api/v1/status"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)