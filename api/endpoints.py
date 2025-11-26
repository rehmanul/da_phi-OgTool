"""
Production API Endpoints for OGTool
Complete REST API for all platform features
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from database.connection import get_async_db
from database.models import (
    User, Organization, Team, Keyword, Monitor, Lead, Persona,
    Response, Analytics, Webhook, Alert, KnowledgeBase,
    UserRole, PlatformType, LeadStatus, PersonaType, WebhookEvent
)
from auth.authentication import (
    auth_service, get_current_user, get_current_active_user,
    require_admin, require_organization
)
from services.reddit_monitor import reddit_monitor
from services.lead_scorer import LeadScorer
from services.ai_response_generator import AIResponseGenerator
from services.webhook_dispatcher import WebhookDispatcher

# Request/Response Models
class UserRegister(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class KeywordCreate(BaseModel):
    keyword: str
    category: Optional[str] = None
    priority: int = 1

class MonitorCreate(BaseModel):
    name: str
    description: Optional[str] = None
    keywords: List[int]  # Keyword IDs
    platforms: List[str] = ["reddit"]
    subreddits: Optional[List[str]] = None
    check_interval: int = 300
    webhook_url: Optional[str] = None

class PersonaCreate(BaseModel):
    name: str
    type: str = "custom"
    description: Optional[str] = None
    voice_tone: str = "professional"
    background: Optional[str] = None
    expertise: Optional[List[str]] = None
    communication_style: Optional[str] = None
    values: Optional[List[str]] = None
    greeting_template: Optional[str] = None
    closing_template: Optional[str] = None
    signature: Optional[str] = None

class ResponseGenerate(BaseModel):
    lead_id: int
    persona_id: int
    model: str = "perplexity"
    custom_instructions: Optional[str] = None

class WebhookCreate(BaseModel):
    name: str
    url: str
    events: List[str]
    headers: Optional[Dict[str, str]] = None

# Initialize services
lead_scorer = LeadScorer()
ai_generator = AIResponseGenerator()
webhook_dispatcher = WebhookDispatcher()

# Create routers
auth_router = APIRouter(prefix="/api/v2/auth", tags=["Authentication"])
users_router = APIRouter(prefix="/api/v2/users", tags=["Users"])
keywords_router = APIRouter(prefix="/api/v2/keywords", tags=["Keywords"])
monitors_router = APIRouter(prefix="/api/v2/monitors", tags=["Monitors"])
leads_router = APIRouter(prefix="/api/v2/leads", tags=["Leads"])
personas_router = APIRouter(prefix="/api/v2/personas", tags=["Personas"])
responses_router = APIRouter(prefix="/api/v2/responses", tags=["Responses"])
webhooks_router = APIRouter(prefix="/api/v2/webhooks", tags=["Webhooks"])
analytics_router = APIRouter(prefix="/api/v2/analytics", tags=["Analytics"])

# Authentication Endpoints
@auth_router.post("/register", response_model=TokenResponse)
async def register(data: UserRegister, db: Session = Depends(get_async_db)):
    """Register a new user"""
    # Check if user exists
    existing = db.query(User).filter(
        (User.email == data.email) | (User.username == data.username)
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    # Create user
    user = User(
        email=data.email,
        username=data.username,
        password_hash=auth_service.hash_password(data.password),
        full_name=data.full_name,
        role=UserRole.MEMBER,
        is_active=True,
        is_verified=False
    )
    db.add(user)
    db.commit()

    # Generate tokens
    access_token = auth_service.create_access_token({"sub": str(user.id)})
    refresh_token = auth_service.create_refresh_token({"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=1800  # 30 minutes
    )

@auth_router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, db: Session = Depends(get_async_db)):
    """Login with email and password"""
    user = db.query(User).filter(User.email == data.email).first()

    if not user or not auth_service.verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")

    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()

    # Generate tokens
    access_token = auth_service.create_access_token({"sub": str(user.id)})
    refresh_token = auth_service.create_refresh_token({"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=1800
    )

@auth_router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_token: str):
    """Refresh access token using refresh token"""
    payload = auth_service.verify_token(refresh_token, "refresh")
    user_id = payload.get("sub")

    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    # Generate new access token
    access_token = auth_service.create_access_token({"sub": user_id})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=1800
    )

# User Endpoints
@users_router.get("/me")
async def get_current_user_profile(user: User = Depends(get_current_active_user)):
    """Get current user profile"""
    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "full_name": user.full_name,
        "role": user.role.value,
        "organization_id": user.organization_id,
        "is_verified": user.is_verified
    }

# Keyword Endpoints
@keywords_router.post("/", status_code=201)
async def create_keyword(
    data: KeywordCreate,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_async_db)
):
    """Create a new keyword"""
    keyword = Keyword(
        user_id=user.id,
        keyword=data.keyword,
        category=data.category,
        priority=data.priority,
        is_active=True
    )
    db.add(keyword)
    db.commit()

    return {"id": keyword.id, "keyword": keyword.keyword}

@keywords_router.get("/", response_model=List[Dict])
async def list_keywords(
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_async_db)
):
    """List user's keywords"""
    keywords = db.query(Keyword).filter(
        Keyword.user_id == user.id,
        Keyword.is_active == True
    ).all()

    return [
        {
            "id": k.id,
            "keyword": k.keyword,
            "category": k.category,
            "priority": k.priority,
            "created_at": k.created_at
        }
        for k in keywords
    ]

# Monitor Endpoints
@monitors_router.post("/", status_code=201)
async def create_monitor(
    data: MonitorCreate,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_async_db)
):
    """Create a new monitor"""
    monitor = Monitor(
        user_id=user.id,
        name=data.name,
        description=data.description,
        platforms=data.platforms,
        subreddits=data.subreddits,
        check_interval=data.check_interval,
        webhook_url=data.webhook_url,
        is_active=True,
        next_check=datetime.utcnow()
    )
    db.add(monitor)
    db.commit()

    # Link keywords
    from database.models import MonitorKeyword
    for keyword_id in data.keywords:
        mk = MonitorKeyword(monitor_id=monitor.id, keyword_id=keyword_id)
        db.add(mk)
    db.commit()

    return {"id": monitor.id, "name": monitor.name}

@monitors_router.get("/", response_model=List[Dict])
async def list_monitors(
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_async_db)
):
    """List user's monitors"""
    monitors = db.query(Monitor).filter(
        Monitor.user_id == user.id
    ).all()

    return [
        {
            "id": m.id,
            "name": m.name,
            "platforms": m.platforms,
            "is_active": m.is_active,
            "last_check": m.last_check,
            "next_check": m.next_check
        }
        for m in monitors
    ]

# Lead Endpoints
@leads_router.get("/", response_model=List[Dict])
async def list_leads(
    status: Optional[str] = None,
    platform: Optional[str] = None,
    min_score: Optional[float] = None,
    limit: int = Query(50, le=100),
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_async_db)
):
    """List leads with filters"""
    query = db.query(Lead).join(Monitor).filter(
        Monitor.user_id == user.id
    )

    if status:
        query = query.filter(Lead.status == LeadStatus[status.upper()])
    if platform:
        query = query.filter(Lead.platform == PlatformType[platform.upper()])
    if min_score:
        query = query.filter(Lead.total_score >= min_score)

    leads = query.order_by(Lead.total_score.desc()).limit(limit).all()

    return [
        {
            "id": l.id,
            "platform": l.platform.value,
            "title": l.title,
            "content": l.content[:200],
            "author": l.author,
            "url": l.url,
            "status": l.status.value,
            "scores": {
                "relevance": l.relevance_score,
                "engagement": l.engagement_score,
                "opportunity": l.opportunity_score,
                "total": l.total_score
            },
            "found_at": l.found_at
        }
        for l in leads
    ]

@leads_router.get("/{lead_id}")
async def get_lead(
    lead_id: int,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_async_db)
):
    """Get lead details"""
    lead = db.query(Lead).join(Monitor).filter(
        Lead.id == lead_id,
        Monitor.user_id == user.id
    ).first()

    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    return {
        "id": lead.id,
        "platform": lead.platform.value,
        "title": lead.title,
        "content": lead.content,
        "author": lead.author,
        "url": lead.url,
        "status": lead.status.value,
        "scores": {
            "relevance": lead.relevance_score,
            "engagement": lead.engagement_score,
            "opportunity": lead.opportunity_score,
            "total": lead.total_score
        },
        "ai_analysis": {
            "summary": lead.ai_summary,
            "intent": lead.ai_intent,
            "sentiment": lead.ai_sentiment,
            "suggested_persona": lead.ai_suggested_persona.value if lead.ai_suggested_persona else None
        },
        "metadata": {
            "subreddit": lead.subreddit,
            "karma": lead.post_karma,
            "comments": lead.comment_count,
            "upvote_ratio": lead.upvote_ratio
        },
        "found_at": lead.found_at,
        "posted_at": lead.posted_at
    }

# Persona Endpoints
@personas_router.post("/", status_code=201)
async def create_persona(
    data: PersonaCreate,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_async_db)
):
    """Create a new persona"""
    persona = Persona(
        user_id=user.id,
        name=data.name,
        type=PersonaType[data.type.upper()] if data.type != "custom" else PersonaType.CUSTOM,
        description=data.description,
        voice_tone=data.voice_tone,
        background=data.background,
        expertise=data.expertise,
        communication_style=data.communication_style,
        values=data.values,
        greeting_template=data.greeting_template,
        closing_template=data.closing_template,
        signature=data.signature,
        is_active=True
    )
    db.add(persona)
    db.commit()

    return {"id": persona.id, "name": persona.name}

@personas_router.get("/", response_model=List[Dict])
async def list_personas(
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_async_db)
):
    """List user's personas"""
    personas = db.query(Persona).filter(
        Persona.user_id == user.id,
        Persona.is_active == True
    ).all()

    return [
        {
            "id": p.id,
            "name": p.name,
            "type": p.type.value,
            "description": p.description,
            "voice_tone": p.voice_tone,
            "is_default": p.is_default
        }
        for p in personas
    ]

# Response Generation Endpoints
@responses_router.post("/generate")
async def generate_response(
    data: ResponseGenerate,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_async_db)
):
    """Generate AI response for a lead"""
    # Get lead
    lead = db.query(Lead).join(Monitor).filter(
        Lead.id == data.lead_id,
        Monitor.user_id == user.id
    ).first()

    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    # Get persona
    persona = db.query(Persona).filter(
        Persona.id == data.persona_id,
        Persona.user_id == user.id
    ).first()

    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")

    # Generate response
    result = await ai_generator.generate_response(
        lead,
        persona,
        data.model,
        data.custom_instructions
    )

    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error"))

    # Save response
    response = Response(
        lead_id=lead.id,
        user_id=user.id,
        persona_id=persona.id,
        generated_content=result["content"],
        ai_model=data.model
    )
    db.add(response)
    db.commit()

    return {
        "id": response.id,
        "content": result["content"],
        "persona": persona.name,
        "model": data.model
    }

# Webhook Endpoints
@webhooks_router.post("/", status_code=201)
async def create_webhook(
    data: WebhookCreate,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_async_db)
):
    """Create a webhook"""
    webhook = Webhook(
        user_id=user.id,
        name=data.name,
        url=data.url,
        events=data.events,
        headers=data.headers,
        is_active=True
    )
    db.add(webhook)
    db.commit()

    # Test webhook
    test_result = await webhook_dispatcher.test_webhook(data.url)

    return {
        "id": webhook.id,
        "name": webhook.name,
        "test_result": test_result
    }

# Analytics Endpoints
@analytics_router.get("/dashboard")
async def get_dashboard_analytics(
    days: int = Query(7, le=90),
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_async_db)
):
    """Get dashboard analytics"""
    cutoff = datetime.utcnow() - timedelta(days=days)

    # Get lead stats
    leads = db.query(Lead).join(Monitor).filter(
        Monitor.user_id == user.id,
        Lead.found_at >= cutoff
    ).all()

    # Calculate metrics
    total_leads = len(leads)
    avg_score = sum(l.total_score for l in leads) / total_leads if total_leads > 0 else 0
    responded = len([l for l in leads if l.status == LeadStatus.RESPONDED])

    # Platform breakdown
    platform_stats = {}
    for lead in leads:
        platform = lead.platform.value
        if platform not in platform_stats:
            platform_stats[platform] = {"count": 0, "avg_score": 0}
        platform_stats[platform]["count"] += 1
        platform_stats[platform]["avg_score"] += lead.total_score

    for platform in platform_stats:
        count = platform_stats[platform]["count"]
        platform_stats[platform]["avg_score"] /= count

    return {
        "period_days": days,
        "total_leads": total_leads,
        "average_score": round(avg_score, 2),
        "responded_count": responded,
        "response_rate": round(responded / total_leads * 100, 1) if total_leads > 0 else 0,
        "platform_breakdown": platform_stats,
        "daily_trend": []  # Would calculate daily data here
    }

# Export all routers
all_routers = [
    auth_router,
    users_router,
    keywords_router,
    monitors_router,
    leads_router,
    personas_router,
    responses_router,
    webhooks_router,
    analytics_router
]