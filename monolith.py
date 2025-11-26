"""
Monolithic application entry point for Render deployment.
Combines all microservices into a single process.
"""
import asyncio
import structlog
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from prometheus_fastapi_instrumentator import Instrumentator

# Import from api_gateway
from services.api_gateway.app.config import settings
from services.api_gateway.app.database import init_db, close_db
from services.api_gateway.app.routers import (
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
from services.api_gateway.app.websocket import router as ws_router

from services.shared.internal_queue import init_mq, close_mq
from services.reddit_monitor.main import RedditMonitorService
from services.ai_response.main import AIResponseService
from services.analytics.main import AnalyticsService
from services.linkedin_monitor.main import LinkedInMonitorService
from services.blog_monitor.main import BlogMonitorService

logger = structlog.get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for the monolith"""
    logger.info("Starting Monolith Application")

    # Initialize API Gateway database
    await init_db()

    # Initialize shared resources
    await init_mq()

    # Initialize services
    try:
        reddit_service = RedditMonitorService()
        ai_service = AIResponseService()
        analytics_service = AnalyticsService()
        linkedin_service = LinkedInMonitorService()
        blog_service = BlogMonitorService()
    except Exception as e:
        logger.warning(f"Some services failed to initialize: {e}. Continuing with API Gateway only.")
        reddit_service = ai_service = analytics_service = linkedin_service = blog_service = None

    # Start background tasks
    tasks = []
    try:
        if reddit_service:
            tasks.append(asyncio.create_task(reddit_service.start()))
        if ai_service:
            tasks.append(asyncio.create_task(ai_service.start()))
        if analytics_service:
            tasks.append(asyncio.create_task(analytics_service.start()))
        if linkedin_service:
            tasks.append(asyncio.create_task(linkedin_service.start()))
        if blog_service:
            tasks.append(asyncio.create_task(blog_service.start()))

        logger.info("Monolith started successfully")
        yield

    finally:
        logger.info("Shutting down Monolith Application")
        # Stop services
        if reddit_service:
            await reddit_service.stop()
        if ai_service:
            await ai_service.stop()
        if analytics_service:
            await analytics_service.stop()
        if linkedin_service:
            await linkedin_service.stop()
        if blog_service:
            await blog_service.stop()

        # Cancel background tasks
        for task in tasks:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        await close_mq()
        await close_db()

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

# Compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Include routers from API Gateway
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
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "ogtool-monolith"}

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
