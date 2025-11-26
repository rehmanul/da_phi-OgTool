"""
Production monolithic application for Render deployment.
Full API implementation with LLM integration.
"""
import asyncio
import os
import structlog
import json
from typing import Optional, List, Dict, Any
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from contextlib import asynccontextmanager
import httpx
import openai
import google.generativeai as genai

logger = structlog.get_logger()

# Production configuration
class Settings:
    VERSION = "2.0.0"
    CORS_ORIGINS = ["*"]
    DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://localhost/ogtool")
    PERPLEXITY_API_KEY = os.environ.get("PERPLEXITY_API_KEY", "")
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
    REDDIT_CLIENT_ID = os.environ.get("REDDIT_CLIENT_ID", "")
    REDDIT_CLIENT_SECRET = os.environ.get("REDDIT_CLIENT_SECRET", "")
    REDDIT_USER_AGENT = os.environ.get("REDDIT_USER_AGENT", "OGTool/2.0")

settings = Settings()

# Configure APIs
if settings.PERPLEXITY_API_KEY:
    openai_client = openai.OpenAI(
        api_key=settings.PERPLEXITY_API_KEY,
        base_url="https://api.perplexity.ai"
    )

if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-1.5-flash')

# Request/Response Models
class LeadRequest(BaseModel):
    keywords: List[str]
    platforms: List[str] = ["reddit", "linkedin", "blogs"]
    limit: int = 10
    persona: Optional[str] = None

class AIRequest(BaseModel):
    prompt: str
    model: str = "perplexity"  # "perplexity" or "gemini"
    max_tokens: Optional[int] = 1000
    temperature: Optional[float] = 0.7

class AIResponse(BaseModel):
    response: str
    model: str
    tokens_used: Optional[int] = None
    timestamp: datetime

class Lead(BaseModel):
    id: str
    platform: str
    title: str
    content: str
    author: str
    url: str
    score: float
    timestamp: datetime
    keywords_matched: List[str]
    ai_analysis: Optional[str] = None

class MonitorConfig(BaseModel):
    keywords: List[str]
    platforms: List[str]
    check_interval: int = 300  # seconds
    ai_enabled: bool = True
    webhook_url: Optional[str] = None

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
            "/api/v1/status",
            "/api/v1/ai/generate",
            "/api/v1/leads/search",
            "/api/v1/monitors"
        ]
    }

# AI Generation Endpoint
@app.post("/api/v1/ai/generate", response_model=AIResponse)
async def generate_ai_response(request: AIRequest):
    """Generate AI response using Perplexity or Gemini"""
    try:
        if request.model == "perplexity" and settings.PERPLEXITY_API_KEY:
            response = openai_client.chat.completions.create(
                model="llama-3.1-sonar-small-128k-online",
                messages=[{"role": "user", "content": request.prompt}],
                max_tokens=request.max_tokens,
                temperature=request.temperature
            )
            return AIResponse(
                response=response.choices[0].message.content,
                model="perplexity",
                tokens_used=response.usage.total_tokens if hasattr(response, 'usage') else None,
                timestamp=datetime.now()
            )
        elif request.model == "gemini" and settings.GEMINI_API_KEY:
            response = gemini_model.generate_content(request.prompt)
            return AIResponse(
                response=response.text,
                model="gemini",
                timestamp=datetime.now()
            )
        else:
            raise HTTPException(status_code=400, detail=f"Model {request.model} not configured")
    except Exception as e:
        logger.error(f"AI generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Lead Search Endpoint
@app.post("/api/v1/leads/search", response_model=List[Lead])
async def search_leads(request: LeadRequest):
    """Search for leads based on keywords and platforms"""
    leads = []

    # Reddit Search
    if "reddit" in request.platforms:
        try:
            import praw
            if settings.REDDIT_CLIENT_ID and settings.REDDIT_CLIENT_SECRET:
                reddit = praw.Reddit(
                    client_id=settings.REDDIT_CLIENT_ID,
                    client_secret=settings.REDDIT_CLIENT_SECRET,
                    user_agent=settings.REDDIT_USER_AGENT
                )

                for keyword in request.keywords[:3]:  # Limit to prevent rate limiting
                    subreddit = reddit.subreddit("all")
                    for submission in subreddit.search(keyword, limit=min(request.limit, 5)):
                        lead = Lead(
                            id=submission.id,
                            platform="reddit",
                            title=submission.title,
                            content=submission.selftext[:500] if submission.selftext else "",
                            author=str(submission.author) if submission.author else "deleted",
                            url=f"https://reddit.com{submission.permalink}",
                            score=float(submission.score),
                            timestamp=datetime.fromtimestamp(submission.created_utc),
                            keywords_matched=[keyword]
                        )

                        # AI Analysis if persona is provided
                        if request.persona and settings.PERPLEXITY_API_KEY:
                            try:
                                analysis_prompt = f"Analyze this Reddit post as a {request.persona}: Title: {lead.title}, Content: {lead.content[:200]}"
                                analysis = openai_client.chat.completions.create(
                                    model="llama-3.1-sonar-small-128k-online",
                                    messages=[{"role": "user", "content": analysis_prompt}],
                                    max_tokens=150
                                )
                                lead.ai_analysis = analysis.choices[0].message.content
                            except:
                                pass

                        leads.append(lead)
        except Exception as e:
            logger.warning(f"Reddit search error: {e}")

    # Blog/Web Search using Perplexity
    if "blogs" in request.platforms and settings.PERPLEXITY_API_KEY:
        try:
            search_query = f"Find recent blog posts about: {', '.join(request.keywords)}"
            response = openai_client.chat.completions.create(
                model="llama-3.1-sonar-small-128k-online",
                messages=[{"role": "user", "content": search_query}],
                max_tokens=500
            )

            # Parse and create synthetic leads from the response
            content = response.choices[0].message.content
            if content:
                lead = Lead(
                    id=f"blog_{datetime.now().timestamp()}",
                    platform="blogs",
                    title=f"Blog results for: {', '.join(request.keywords[:2])}",
                    content=content[:500],
                    author="AI Aggregated",
                    url="https://perplexity.ai",
                    score=1.0,
                    timestamp=datetime.now(),
                    keywords_matched=request.keywords
                )
                leads.append(lead)
        except Exception as e:
            logger.warning(f"Blog search error: {e}")

    return leads[:request.limit]

# Monitor Management
monitors_db = {}  # In-memory storage for production simplicity

@app.post("/api/v1/monitors")
async def create_monitor(config: MonitorConfig):
    """Create a new keyword monitor"""
    monitor_id = f"monitor_{datetime.now().timestamp()}"
    monitors_db[monitor_id] = {
        "id": monitor_id,
        "config": config.dict(),
        "created_at": datetime.now().isoformat(),
        "status": "active"
    }
    return {"monitor_id": monitor_id, "status": "created"}

@app.get("/api/v1/monitors")
async def list_monitors():
    """List all active monitors"""
    return list(monitors_db.values())

@app.delete("/api/v1/monitors/{monitor_id}")
async def delete_monitor(monitor_id: str):
    """Delete a monitor"""
    if monitor_id in monitors_db:
        del monitors_db[monitor_id]
        return {"status": "deleted"}
    raise HTTPException(status_code=404, detail="Monitor not found")

# Serve static files (frontend)
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

    @app.get("/", response_class=HTMLResponse)
    async def serve_frontend():
        """Serve the frontend HTML"""
        try:
            with open("static/index.html", "r") as f:
                return HTMLResponse(content=f.read())
        except:
            return HTMLResponse(content="<h1>OGTool API</h1><p>Frontend not found. API is operational.</p>")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"Starting production server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)