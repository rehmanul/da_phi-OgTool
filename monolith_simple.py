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
openai_client = None
gemini_model = None

if settings.PERPLEXITY_API_KEY:
    try:
        openai_client = openai.OpenAI(
            api_key=settings.PERPLEXITY_API_KEY,
            base_url="https://api.perplexity.ai"
        )
        logger.info(f"Perplexity API client initialized with key starting: {settings.PERPLEXITY_API_KEY[:8]}...")
    except Exception as e:
        logger.error(f"Failed to initialize Perplexity client: {e}")
        openai_client = None

if settings.GEMINI_API_KEY:
    try:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel('gemini-1.5-flash')
        logger.info("Gemini API client initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Gemini client: {e}")

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

# Root endpoint moved to serve HTML frontend below

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
    errors = []

    logger.info(f"Lead search request: keywords={request.keywords}, platforms={request.platforms}")
    logger.info(f"Perplexity configured: {bool(settings.PERPLEXITY_API_KEY)}, Client initialized: {openai_client is not None}")

    # Use Perplexity AI for all searches since it's configured
    if settings.PERPLEXITY_API_KEY and openai_client:
        for platform in request.platforms:
            try:
                # Construct platform-specific search query for better results
                keyword_string = ', '.join(request.keywords)
                if platform == "reddit":
                    search_query = f"""Search Reddit for recent posts about {keyword_string}.
                    Return 5 specific posts with:
                    1. Post title
                    2. Subreddit name
                    3. Key discussion points
                    4. Author insights
                    Format each post clearly separated."""
                elif platform == "linkedin":
                    search_query = f"""Find LinkedIn posts and articles about {keyword_string}.
                    Return 5 specific posts with:
                    1. Post headline
                    2. Professional insights
                    3. Industry trends mentioned
                    4. Key takeaways
                    Format each post clearly separated."""
                else:  # blogs
                    search_query = f"""Find recent blog posts about {keyword_string}.
                    Return 5 specific articles with:
                    1. Article title
                    2. Blog/Publication name
                    3. Main points covered
                    4. Key insights
                    Format each article clearly separated."""

                logger.info(f"Searching {platform} with query length: {len(search_query)}")

                # Use Perplexity to search
                response = openai_client.chat.completions.create(
                    model="llama-3.1-sonar-small-128k-online",
                    messages=[{"role": "user", "content": search_query}],
                    max_tokens=1500,  # Increased for better results
                    temperature=0.7
                )

                content = response.choices[0].message.content
                logger.info(f"Received response from Perplexity for {platform}, length: {len(content) if content else 0}")

                if content:
                    # Better parsing logic - look for numbered items or bullet points
                    # Split by common separators
                    import re

                    # Try to split by numbers (1., 2., etc) or bullet points
                    split_pattern = r'(?:^|\n)(?:\d+\.|[\*\-•])\s+'
                    sections = re.split(split_pattern, content)

                    # If no good splits, try double newlines
                    if len(sections) < 2:
                        sections = content.split('\n\n')

                    # Process each section into a lead
                    lead_count = 0
                    for i, section in enumerate(sections):
                        if len(section.strip()) > 30 and lead_count < 5:  # Ensure meaningful content
                            # Clean up section
                            section = section.strip()

                            # Extract title (first line or first sentence)
                            lines = section.split('\n')
                            title_line = lines[0] if lines else ""

                            # Clean title
                            title = re.sub(r'^[\d\.\)\-\*\s]+', '', title_line)  # Remove leading numbers/bullets
                            title = title.replace('**', '').replace('*', '').replace('#', '').strip()

                            # If title is too short or empty, create a better one
                            if len(title) < 10:
                                title = f"{platform.title()} insight: {request.keywords[0]}"

                            # Truncate title to reasonable length
                            title = title[:200]

                            # Create lead
                            lead = Lead(
                                id=f"{platform}_{datetime.now().timestamp()}_{lead_count}",
                                platform=platform,
                                title=title,
                                content=section[:800],  # Increased content length
                                author=f"{platform.title()} Discovery",
                                url=f"https://perplexity.ai/search?q={'+'.join([kw.replace(' ', '+') for kw in request.keywords])}",
                                score=0.9 - (lead_count * 0.15),  # Better score distribution
                                timestamp=datetime.now(),
                                keywords_matched=[kw for kw in request.keywords if kw.lower() in section.lower()]
                            )

                            # Add persona analysis if provided
                            if request.persona:
                                try:
                                    analysis_prompt = f"As a {request.persona}, provide a brief analysis of this lead in 2 sentences: {section[:300]}"
                                    analysis_response = openai_client.chat.completions.create(
                                        model="llama-3.1-sonar-small-128k-online",
                                        messages=[{"role": "user", "content": analysis_prompt}],
                                        max_tokens=100
                                    )
                                    lead.ai_analysis = analysis_response.choices[0].message.content
                                except Exception as ae:
                                    logger.warning(f"Persona analysis failed: {ae}")

                            leads.append(lead)
                            lead_count += 1

                    logger.info(f"Created {lead_count} leads for {platform}")

            except Exception as e:
                logger.error(f"{platform} search error: {e}", exc_info=True)
                errors.append(f"{platform}: {str(e)}")

    # Reddit API search (fallback if configured)
    if "reddit" in request.platforms and settings.REDDIT_CLIENT_ID and settings.REDDIT_CLIENT_SECRET:
        try:
            import praw
            reddit = praw.Reddit(
                client_id=settings.REDDIT_CLIENT_ID,
                client_secret=settings.REDDIT_CLIENT_SECRET,
                user_agent=settings.REDDIT_USER_AGENT
            )

            for keyword in request.keywords[:2]:  # Limit to prevent rate limiting
                subreddit = reddit.subreddit("all")
                for submission in subreddit.search(keyword, limit=3):
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
                    leads.append(lead)
        except Exception as e:
            logger.warning(f"Reddit API error: {e}")

    # If no leads found, provide helpful information
    if not leads:
        if errors:
            # If there were errors, create informative lead about the issue
            error_summary = "; ".join(errors[:3])  # Show first 3 errors
            leads.append(Lead(
                id="error_info",
                platform="system",
                title="Search encountered errors",
                content=f"The search encountered the following errors: {error_summary}. Please check the application logs for more details. Ensure API keys are properly configured in environment variables.",
                author="System",
                url="/health",
                score=0.0,
                timestamp=datetime.now(),
                keywords_matched=request.keywords
            ))
        elif not settings.PERPLEXITY_API_KEY:
            # No API key configured
            leads.append(Lead(
                id="config_needed",
                platform="system",
                title="Perplexity API Key Required",
                content="The Perplexity API key is not configured. Please set the PERPLEXITY_API_KEY environment variable to enable AI-powered lead generation. Visit the /health endpoint to check configuration status.",
                author="System",
                url="/health",
                score=0.0,
                timestamp=datetime.now(),
                keywords_matched=request.keywords
            ))
        else:
            # API configured but no results - provide production sample
            leads.append(Lead(
                id="sample_1",
                platform="system",
                title="No results found - Try different keywords",
                content=f"No leads were found for keywords: {', '.join(request.keywords)}. Try using broader terms, checking different platforms, or adjusting your search criteria. The AI search is operational but didn't find matching content.",
                author="System",
                url="/docs",
                score=0.0,
                timestamp=datetime.now(),
                keywords_matched=request.keywords
            ))

    # Log final results
    logger.info(f"Returning {len(leads)} leads, {len(errors)} errors encountered")

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

# Serve the main frontend HTML
@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serve the frontend HTML"""
    # Read and return the index.html file content directly
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OGTool - AI-Powered Lead Generation Platform</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/axios/dist/axios.min.js"></script>
    <script src="https://unpkg.com/lucide@latest"></script>
    <style>
        .gradient-bg {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        .loading-spinner {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body class="bg-gray-50">
    <div id="app" class="min-h-screen">
        <!-- Navigation -->
        <nav class="bg-white shadow-lg sticky top-0 z-50">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="flex justify-between h-16">
                    <div class="flex items-center">
                        <span class="text-2xl font-bold text-indigo-600">OGTool</span>
                        <span class="ml-2 text-sm text-gray-500">Lead Generation AI</span>
                    </div>
                    <div class="flex items-center space-x-4">
                        <span id="connection-status" class="text-sm text-green-600">● Connected</span>
                    </div>
                </div>
            </div>
        </nav>

        <!-- Main Dashboard -->
        <div class="max-w-7xl mx-auto px-4 py-8">
            <!-- Lead Search Section -->
            <div class="bg-white rounded-lg shadow-lg p-6 mb-8">
                <h2 class="text-2xl font-bold mb-6">Lead Generation Search</h2>

                <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                    <!-- Keywords Input -->
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Keywords (comma separated)</label>
                        <input type="text" id="keywords-input"
                               value="AI startup, machine learning, SaaS"
                               class="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500">
                    </div>

                    <!-- Platforms Selection -->
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Platforms</label>
                        <div class="flex space-x-4">
                            <label class="flex items-center">
                                <input type="checkbox" id="reddit-check" checked class="mr-2">
                                <span>Reddit</span>
                            </label>
                            <label class="flex items-center">
                                <input type="checkbox" id="linkedin-check" class="mr-2">
                                <span>LinkedIn</span>
                            </label>
                            <label class="flex items-center">
                                <input type="checkbox" id="blogs-check" checked class="mr-2">
                                <span>Blogs</span>
                            </label>
                        </div>
                    </div>
                </div>

                <!-- Search Button -->
                <button onclick="searchLeads()"
                        class="w-full md:w-auto px-8 py-3 bg-indigo-600 text-white rounded-md hover:bg-indigo-700">
                    Search for Leads
                </button>
            </div>

            <!-- Results Section -->
            <div id="results-section" class="hidden">
                <h3 class="text-xl font-bold mb-4">Lead Results</h3>
                <div id="leads-container" class="space-y-4"></div>
            </div>

            <!-- Quick Links -->
            <div class="bg-white rounded-lg shadow-lg p-6">
                <h2 class="text-2xl font-bold mb-6">Quick Actions</h2>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <a href="/docs" target="_blank" class="p-4 bg-indigo-50 rounded-lg hover:bg-indigo-100 transition">
                        <h3 class="font-semibold text-indigo-700">API Documentation</h3>
                        <p class="text-sm text-gray-600 mt-2">Explore the full API</p>
                    </a>
                    <a href="/health" target="_blank" class="p-4 bg-green-50 rounded-lg hover:bg-green-100 transition">
                        <h3 class="font-semibold text-green-700">Health Status</h3>
                        <p class="text-sm text-gray-600 mt-2">Check system status</p>
                    </a>
                    <a href="/api/v1/status" target="_blank" class="p-4 bg-purple-50 rounded-lg hover:bg-purple-100 transition">
                        <h3 class="font-semibold text-purple-700">API Status</h3>
                        <p class="text-sm text-gray-600 mt-2">View available endpoints</p>
                    </a>
                </div>
            </div>
        </div>
    </div>

    <script>
        const API_BASE_URL = window.location.origin;

        // Search for leads
        async function searchLeads() {
            const keywords = document.getElementById('keywords-input').value.split(',').map(k => k.trim());
            const platforms = [];
            if (document.getElementById('reddit-check').checked) platforms.push('reddit');
            if (document.getElementById('linkedin-check').checked) platforms.push('linkedin');
            if (document.getElementById('blogs-check').checked) platforms.push('blogs');

            if (keywords.length === 0 || keywords[0] === '') {
                alert('Please enter at least one keyword');
                return;
            }

            try {
                const response = await axios.post(`${API_BASE_URL}/api/v1/leads/search`, {
                    keywords: keywords,
                    platforms: platforms,
                    limit: 20
                });

                displayLeads(response.data);
            } catch (error) {
                console.error('Search error:', error);
                alert('Search is being implemented. For now, explore the API documentation.');
            }
        }

        // Display leads
        function displayLeads(leads) {
            const container = document.getElementById('leads-container');
            const section = document.getElementById('results-section');

            container.innerHTML = '';

            if (leads.length === 0) {
                container.innerHTML = '<p class="text-gray-500">No leads found. Try different keywords.</p>';
            } else {
                leads.forEach(lead => {
                    const leadCard = document.createElement('div');
                    leadCard.className = 'bg-white border border-gray-200 rounded-lg p-4';
                    leadCard.innerHTML = `
                        <h4 class="font-semibold">${lead.title}</h4>
                        <p class="text-gray-600 mt-2">${lead.content}</p>
                        <div class="mt-3 text-sm text-gray-500">
                            <span>${lead.platform}</span> | <span>${lead.author}</span>
                        </div>
                    `;
                    container.appendChild(leadCard);
                });
            }

            section.classList.remove('hidden');
        }

        // Check connection on load
        async function checkConnection() {
            try {
                await axios.get(`${API_BASE_URL}/health`);
                document.getElementById('connection-status').innerHTML = '● Connected';
                document.getElementById('connection-status').className = 'text-sm text-green-600';
            } catch (error) {
                document.getElementById('connection-status').innerHTML = '● Disconnected';
                document.getElementById('connection-status').className = 'text-sm text-red-600';
            }
        }

        // Initialize
        checkConnection();
    </script>
</body>
</html>"""

    return HTMLResponse(content=html_content)

# Mount static files directory if it exists
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"Starting production server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)