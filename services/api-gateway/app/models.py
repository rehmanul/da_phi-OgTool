"""Pydantic models for request/response validation"""
from pydantic import BaseModel, EmailStr, Field, UUID4
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# Enums
class TierEnum(str, Enum):
    starter = "starter"
    growth = "growth"
    enterprise = "enterprise"


class PlatformEnum(str, Enum):
    reddit = "reddit"
    linkedin = "linkedin"
    blog = "blog"
    chatgpt = "chatgpt"


class PriorityEnum(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    urgent = "urgent"


class StatusEnum(str, Enum):
    pending = "pending"
    reviewed = "reviewed"
    responded = "responded"
    ignored = "ignored"
    archived = "archived"


class RoleEnum(str, Enum):
    viewer = "viewer"
    member = "member"
    admin = "admin"
    owner = "owner"


# Auth models
class TokenData(BaseModel):
    user_id: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str
    organization_name: str


# User models
class User(BaseModel):
    id: UUID4
    organization_id: UUID4
    email: EmailStr
    full_name: Optional[str] = None
    role: RoleEnum
    tier: TierEnum
    api_key: str
    active: bool = True


class UserResponse(BaseModel):
    id: UUID4
    email: EmailStr
    full_name: Optional[str]
    role: RoleEnum
    active: bool
    created_at: datetime


# Organization models
class OrganizationResponse(BaseModel):
    id: UUID4
    name: str
    tier: TierEnum
    monthly_budget: Optional[float]
    current_spend: float
    active: bool
    created_at: datetime


# Keyword models
class KeywordCreate(BaseModel):
    keyword: str = Field(..., min_length=2, max_length=200)
    platform: PlatformEnum
    filters: Optional[Dict[str, Any]] = {}
    priority: int = Field(50, ge=0, le=100)


class KeywordUpdate(BaseModel):
    keyword: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None
    priority: Optional[int] = Field(None, ge=0, le=100)
    active: Optional[bool] = None


class KeywordResponse(BaseModel):
    id: UUID4
    organization_id: UUID4
    keyword: str
    platform: PlatformEnum
    filters: Dict[str, Any]
    priority: int
    alert_threshold: int
    active: bool
    created_at: datetime


# Monitor models
class SubredditMonitorCreate(BaseModel):
    subreddit: str = Field(..., min_length=2, max_length=100)
    keyword_ids: List[UUID4] = []
    engagement_threshold: int = 5
    auto_reply: bool = False
    persona_id: Optional[UUID4] = None


class SubredditMonitorResponse(BaseModel):
    id: UUID4
    organization_id: UUID4
    subreddit: str
    engagement_threshold: int
    auto_reply: bool
    persona_id: Optional[UUID4]
    check_frequency: int
    last_checked: Optional[datetime]
    active: bool
    created_at: datetime


class BlogMonitorCreate(BaseModel):
    blog_url: str
    blog_name: Optional[str] = None
    rss_feed: Optional[str] = None
    check_frequency: int = 3600


class BlogMonitorResponse(BaseModel):
    id: UUID4
    organization_id: UUID4
    blog_url: str
    blog_name: Optional[str]
    rss_feed: Optional[str]
    check_frequency: int
    last_checked: Optional[datetime]
    active: bool
    created_at: datetime


# Post models
class DetectedPostResponse(BaseModel):
    id: UUID4
    platform: PlatformEnum
    external_id: str
    url: str
    title: Optional[str]
    content: str
    author: Optional[str]
    subreddit: Optional[str]
    engagement_score: float
    comment_count: int
    relevance_score: Optional[float]
    keyword_matches: List[str]
    priority: PriorityEnum
    status: StatusEnum
    detected_at: datetime


class GenerateResponseRequest(BaseModel):
    persona_id: Optional[UUID4] = None


class GeneratedResponseResponse(BaseModel):
    id: UUID4
    post_id: UUID4
    persona_id: Optional[UUID4]
    response_text: str
    quality_score: float
    safety_score: Optional[float]
    approved: bool
    posted: bool
    created_at: datetime


class ApproveResponseRequest(BaseModel):
    approved: bool = True


# Persona models
class PersonaCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None
    voice_profile: Dict[str, Any] = {}
    system_prompt: str
    example_responses: List[Dict[str, str]] = []
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(500, ge=50, le=2000)
    knowledge_base_ids: List[UUID4] = []


class PersonaUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    voice_profile: Optional[Dict[str, Any]] = None
    system_prompt: Optional[str] = None
    example_responses: Optional[List[Dict[str, str]]] = None
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, ge=50, le=2000)
    knowledge_base_ids: Optional[List[UUID4]] = None
    active: Optional[bool] = None


class PersonaResponse(BaseModel):
    id: UUID4
    organization_id: UUID4
    name: str
    description: Optional[str]
    voice_profile: Dict[str, Any]
    system_prompt: str
    example_responses: List[Dict[str, str]]
    temperature: float
    max_tokens: int
    active: bool
    created_at: datetime


# Knowledge Base models
class KnowledgeBaseCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = None


class KnowledgeBaseResponse(BaseModel):
    id: UUID4
    organization_id: UUID4
    name: str
    description: Optional[str]
    created_at: datetime


class DocumentUploadRequest(BaseModel):
    title: Optional[str] = None
    content: str
    source_url: Optional[str] = None


class DocumentResponse(BaseModel):
    id: UUID4
    knowledge_base_id: UUID4
    title: Optional[str]
    content: str
    source_url: Optional[str]
    created_at: datetime


# Webhook models
class WebhookCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    url: str
    events: List[str]
    secret: Optional[str] = None


class WebhookResponse(BaseModel):
    id: UUID4
    organization_id: UUID4
    name: str
    url: str
    events: List[str]
    active: bool
    last_triggered: Optional[datetime]
    failure_count: int
    created_at: datetime


# Analytics models
class ShareOfVoiceResponse(BaseModel):
    keyword: str
    platform: PlatformEnum
    our_mentions: int
    competitor_mentions: int
    total_mentions: int
    share_percentage: float
    period: str


class KeywordRankingResponse(BaseModel):
    keyword: str
    platform: PlatformEnum
    position: Optional[int]
    mentions_count: int
    share_of_voice: float
    timestamp: datetime


class EngagementMetrics(BaseModel):
    total_posts_detected: int
    responses_generated: int
    responses_posted: int
    avg_engagement_score: float
    avg_quality_score: float
    conversion_count: int
    period: str


# Pagination
class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int
