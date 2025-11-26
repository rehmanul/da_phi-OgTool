"""
API Gateway - Main FastAPI Application
Production-ready REST API with WebSocket support
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
import structlog

from app.config import settings
from app.database import init_db, close_db
from app.routers import (
    auth,
    keywords,
    monitors,
    posts,
    personas,
    knowledge_bases,
    analytics,
    webhooks,
    organizations,
)
from app.websocket import router as ws_router

logger = structlog.get_logger()

# Create FastAPI app
app = FastAPI(
    title="OGTool API",
    description="AI-powered lead generation platform API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(organizations.router, prefix="/api/v1/organizations", tags=["Organizations"])
app.include_router(keywords.router, prefix="/api/v1/keywords", tags=["Keywords"])
app.include_router(monitors.router, prefix="/api/v1/monitors", tags=["Monitors"])
app.include_router(posts.router, prefix="/api/v1/posts", tags=["Posts"])
app.include_router(personas.router, prefix="/api/v1/personas", tags=["Personas"])
app.include_router(knowledge_bases.router, prefix="/api/v1/knowledge-bases", tags=["Knowledge Bases"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])
app.include_router(webhooks.router, prefix="/api/v1/webhooks", tags=["Webhooks"])
app.include_router(ws_router, prefix="/api/v1/ws", tags=["WebSocket"])

# Prometheus metrics
Instrumentator().instrument(app).expose(app)


@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    logger.info("Starting API Gateway", version=settings.VERSION)
    await init_db()
    logger.info("API Gateway started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down API Gateway")
    await close_db()


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
        "service": "OGTool API Gateway",
        "version": settings.VERSION,
        "status": "operational",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "api-gateway"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
