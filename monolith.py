"""
Monolithic application entry point for Render deployment.
Combines all microservices into a single process.
"""
import asyncio
import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from services.ai_response.config import settings
from services.shared.internal_queue import init_mq, close_mq

# Import service apps/routers
# We assume the services are packages under 'services'
from services.api_gateway.main import app as api_gateway_app
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
    
    # Initialize shared resources
    await init_mq()
    
    # Initialize services
    reddit_service = RedditMonitorService()
    ai_service = AIResponseService()
    analytics_service = AnalyticsService()
    linkedin_service = LinkedInMonitorService()
    blog_service = BlogMonitorService()
    
    # Start background tasks
    # We use create_task to run them in the background
    tasks = []
    try:
        # Start services (assuming they have non-blocking start or we wrap them)
        # Note: The original service.start() methods might be blocking if they run a loop.
        # We need to ensure they are designed to run concurrently or wrap them.
        # Looking at previous code, they seem to have start() methods that might block or run forever.
        # We should check if they need to be run as tasks.
        
        # For this implementation, we assume start() initializes and maybe spawns its own tasks,
        # or we wrap the main loop in a task.
        
        tasks.append(asyncio.create_task(reddit_service.start()))
        tasks.append(asyncio.create_task(ai_service.start()))
        tasks.append(asyncio.create_task(analytics_service.start()))
        tasks.append(asyncio.create_task(linkedin_service.start()))
        tasks.append(asyncio.create_task(blog_service.start()))
        
        yield
        
    finally:
        logger.info("Shutting down Monolith Application")
        # Stop services
        await reddit_service.stop()
        await ai_service.stop()
        await analytics_service.stop()
        await linkedin_service.stop()
        await blog_service.stop()
        
        # Cancel background tasks if they are still running
        for task in tasks:
            task.cancel()
            
        await close_mq()

# Create the main FastAPI app
# We mount the API Gateway as the root app, but we need to inject the lifespan
app = FastAPI(title="OGTool Monolith", lifespan=lifespan)

# Mount the API Gateway routes
# Since API Gateway is likely the main entry point for HTTP, we can just mount its routers
# or mount the whole app. Mounting the whole app is easier.
app.mount("/", api_gateway_app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
