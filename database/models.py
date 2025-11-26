"""
Production Database Models for OGTool
Complete schema for lead generation platform
"""
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, JSON, Enum, Index, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

Base = declarative_base()

# Enums
class PlatformType(enum.Enum):
    REDDIT = "reddit"
    LINKEDIN = "linkedin"
    BLOG = "blog"
    TWITTER = "twitter"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"

class LeadStatus(enum.Enum):
    NEW = "new"
    REVIEWING = "reviewing"
    RESPONDED = "responded"
    IGNORED = "ignored"
    ARCHIVED = "archived"

class PersonaType(enum.Enum):
    FOUNDER = "founder"
    MARKETER = "marketer"
    SALES = "sales"
    SUPPORT = "support"
    TECHNICAL = "technical"
    COACH = "coach"
    CONSULTANT = "consultant"
    CUSTOM = "custom"

class WebhookEvent(enum.Enum):
    LEAD_FOUND = "lead_found"
    LEAD_SCORED = "lead_scored"
    RESPONSE_GENERATED = "response_generated"
    RESPONSE_POSTED = "response_posted"
    MONITOR_ALERT = "monitor_alert"

class UserRole(enum.Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    MEMBER = "member"
    VIEWER = "viewer"

# User Management
class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255))
    avatar_url = Column(String(500))
    role = Column(Enum(UserRole), default=UserRole.MEMBER)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    verification_token = Column(String(255))
    reset_token = Column(String(255))
    last_login = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    organization_id = Column(Integer, ForeignKey('organizations.id'))
    organization = relationship("Organization", back_populates="users")
    keywords = relationship("Keyword", back_populates="user")
    monitors = relationship("Monitor", back_populates="user")
    personas = relationship("Persona", back_populates="user")
    responses = relationship("Response", back_populates="user")
    webhooks = relationship("Webhook", back_populates="user")
    activities = relationship("Activity", back_populates="user")

class Organization(Base):
    __tablename__ = 'organizations'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text)
    logo_url = Column(String(500))
    website = Column(String(500))
    subscription_tier = Column(String(50), default="free")
    subscription_expires = Column(DateTime)
    api_key = Column(String(255), unique=True, index=True)
    settings = Column(JSON, default={})
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    users = relationship("User", back_populates="organization")
    teams = relationship("Team", back_populates="organization")

class Team(Base):
    __tablename__ = 'teams'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    organization_id = Column(Integer, ForeignKey('organizations.id'))
    created_at = Column(DateTime, default=func.now())

    # Relationships
    organization = relationship("Organization", back_populates="teams")
    members = relationship("TeamMember", back_populates="team")

class TeamMember(Base):
    __tablename__ = 'team_members'

    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey('teams.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    role = Column(Enum(UserRole), default=UserRole.MEMBER)
    joined_at = Column(DateTime, default=func.now())

    # Relationships
    team = relationship("Team", back_populates="members")
    user = relationship("User")

    __table_args__ = (
        UniqueConstraint('team_id', 'user_id', name='unique_team_member'),
    )

# Lead Generation Core
class Keyword(Base):
    __tablename__ = 'keywords'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    keyword = Column(String(255), nullable=False, index=True)
    category = Column(String(100))
    priority = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="keywords")
    monitors = relationship("MonitorKeyword", back_populates="keyword")
    lead_matches = relationship("LeadKeyword", back_populates="keyword")

    __table_args__ = (
        Index('idx_keyword_user', 'user_id', 'keyword'),
    )

class Monitor(Base):
    __tablename__ = 'monitors'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    platforms = Column(JSON, default=[])  # List of PlatformType values
    subreddits = Column(JSON, default=[])  # For Reddit-specific monitoring
    check_interval = Column(Integer, default=300)  # seconds
    max_results = Column(Integer, default=100)
    is_active = Column(Boolean, default=True)
    last_check = Column(DateTime)
    next_check = Column(DateTime)
    webhook_url = Column(String(500))
    notification_email = Column(String(255))
    settings = Column(JSON, default={})
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="monitors")
    keywords = relationship("MonitorKeyword", back_populates="monitor")
    leads = relationship("Lead", back_populates="monitor")
    alerts = relationship("Alert", back_populates="monitor")

class MonitorKeyword(Base):
    __tablename__ = 'monitor_keywords'

    id = Column(Integer, primary_key=True)
    monitor_id = Column(Integer, ForeignKey('monitors.id'))
    keyword_id = Column(Integer, ForeignKey('keywords.id'))

    # Relationships
    monitor = relationship("Monitor", back_populates="keywords")
    keyword = relationship("Keyword", back_populates="monitors")

    __table_args__ = (
        UniqueConstraint('monitor_id', 'keyword_id', name='unique_monitor_keyword'),
    )

class Lead(Base):
    __tablename__ = 'leads'

    id = Column(Integer, primary_key=True)
    monitor_id = Column(Integer, ForeignKey('monitors.id'))
    platform = Column(Enum(PlatformType), nullable=False, index=True)
    platform_id = Column(String(255), index=True)  # Reddit post ID, LinkedIn post ID, etc.
    title = Column(String(500))
    content = Column(Text)
    author = Column(String(255))
    author_profile = Column(String(500))
    url = Column(String(500), nullable=False)
    permalink = Column(String(500))

    # Scoring
    relevance_score = Column(Float, default=0.0, index=True)
    engagement_score = Column(Float, default=0.0)
    opportunity_score = Column(Float, default=0.0)
    total_score = Column(Float, default=0.0, index=True)

    # Metadata
    subreddit = Column(String(100))  # For Reddit
    post_karma = Column(Integer)
    comment_count = Column(Integer)
    upvote_ratio = Column(Float)

    # Status
    status = Column(Enum(LeadStatus), default=LeadStatus.NEW, index=True)
    assigned_to = Column(Integer, ForeignKey('users.id'))
    responded_at = Column(DateTime)

    # AI Analysis
    ai_summary = Column(Text)
    ai_intent = Column(String(100))
    ai_sentiment = Column(String(50))
    ai_suggested_persona = Column(Enum(PersonaType))

    # Timestamps
    posted_at = Column(DateTime)
    found_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    monitor = relationship("Monitor", back_populates="leads")
    keywords = relationship("LeadKeyword", back_populates="lead")
    responses = relationship("Response", back_populates="lead")
    activities = relationship("Activity", back_populates="lead")

    __table_args__ = (
        Index('idx_lead_score', 'total_score', 'status'),
        Index('idx_lead_platform', 'platform', 'platform_id'),
        UniqueConstraint('platform', 'platform_id', name='unique_platform_lead'),
    )

class LeadKeyword(Base):
    __tablename__ = 'lead_keywords'

    id = Column(Integer, primary_key=True)
    lead_id = Column(Integer, ForeignKey('leads.id'))
    keyword_id = Column(Integer, ForeignKey('keywords.id'))
    match_count = Column(Integer, default=1)

    # Relationships
    lead = relationship("Lead", back_populates="keywords")
    keyword = relationship("Keyword", back_populates="lead_matches")

# AI Response Generation
class Persona(Base):
    __tablename__ = 'personas'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    name = Column(String(255), nullable=False)
    type = Column(Enum(PersonaType), default=PersonaType.CUSTOM)
    description = Column(Text)
    voice_tone = Column(String(100))  # professional, casual, friendly, expert

    # Persona characteristics
    background = Column(Text)
    expertise = Column(JSON, default=[])
    communication_style = Column(Text)
    values = Column(JSON, default=[])
    goals = Column(JSON, default=[])

    # Response templates
    greeting_template = Column(Text)
    closing_template = Column(Text)
    signature = Column(Text)

    # Settings
    max_response_length = Column(Integer, default=500)
    include_call_to_action = Column(Boolean, default=True)
    include_credentials = Column(Boolean, default=False)

    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="personas")
    responses = relationship("Response", back_populates="persona")
    templates = relationship("ResponseTemplate", back_populates="persona")

class ResponseTemplate(Base):
    __tablename__ = 'response_templates'

    id = Column(Integer, primary_key=True)
    persona_id = Column(Integer, ForeignKey('personas.id'))
    name = Column(String(255), nullable=False)
    category = Column(String(100))
    intent = Column(String(100))  # question, complaint, interest, general
    template = Column(Text, nullable=False)
    variables = Column(JSON, default=[])  # List of variable names to replace
    usage_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    persona = relationship("Persona", back_populates="templates")

class Response(Base):
    __tablename__ = 'responses'

    id = Column(Integer, primary_key=True)
    lead_id = Column(Integer, ForeignKey('leads.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    persona_id = Column(Integer, ForeignKey('personas.id'))

    # Response content
    generated_content = Column(Text, nullable=False)
    edited_content = Column(Text)
    final_content = Column(Text)

    # AI metadata
    ai_model = Column(String(50))  # perplexity, gemini, gpt-4
    ai_tokens_used = Column(Integer)
    ai_cost = Column(Float)
    generation_time = Column(Float)  # seconds

    # Status
    is_posted = Column(Boolean, default=False)
    posted_at = Column(DateTime)
    posted_by = Column(Integer, ForeignKey('users.id'))
    platform_response_id = Column(String(255))  # ID from Reddit/LinkedIn after posting

    # Engagement metrics
    views = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    replies = Column(Integer, default=0)

    # Review
    quality_score = Column(Float)
    reviewed_by = Column(Integer, ForeignKey('users.id'))
    review_notes = Column(Text)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    lead = relationship("Lead", back_populates="responses")
    user = relationship("User", back_populates="responses", foreign_keys=[user_id])
    persona = relationship("Persona", back_populates="responses")

# Analytics & Reporting
class Analytics(Base):
    __tablename__ = 'analytics'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    date = Column(DateTime, nullable=False, index=True)

    # Lead metrics
    leads_found = Column(Integer, default=0)
    leads_reviewed = Column(Integer, default=0)
    leads_responded = Column(Integer, default=0)

    # Response metrics
    responses_generated = Column(Integer, default=0)
    responses_posted = Column(Integer, default=0)
    avg_response_time = Column(Float)  # minutes

    # Engagement metrics
    total_views = Column(Integer, default=0)
    total_likes = Column(Integer, default=0)
    total_replies = Column(Integer, default=0)
    engagement_rate = Column(Float)

    # Platform breakdown
    reddit_leads = Column(Integer, default=0)
    linkedin_leads = Column(Integer, default=0)
    blog_leads = Column(Integer, default=0)

    # Score metrics
    avg_relevance_score = Column(Float)
    avg_opportunity_score = Column(Float)

    created_at = Column(DateTime, default=func.now())

    __table_args__ = (
        Index('idx_analytics_date', 'user_id', 'date'),
    )

class Activity(Base):
    __tablename__ = 'activities'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    lead_id = Column(Integer, ForeignKey('leads.id'))
    action = Column(String(100), nullable=False)  # viewed, responded, ignored, etc.
    details = Column(JSON, default={})
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    created_at = Column(DateTime, default=func.now())

    # Relationships
    user = relationship("User", back_populates="activities")
    lead = relationship("Lead", back_populates="activities")

    __table_args__ = (
        Index('idx_activity_user', 'user_id', 'created_at'),
    )

# Integrations
class Webhook(Base):
    __tablename__ = 'webhooks'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    name = Column(String(255), nullable=False)
    url = Column(String(500), nullable=False)
    events = Column(JSON, default=[])  # List of WebhookEvent values
    headers = Column(JSON, default={})
    is_active = Column(Boolean, default=True)
    last_triggered = Column(DateTime)
    failure_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    user = relationship("User", back_populates="webhooks")
    logs = relationship("WebhookLog", back_populates="webhook")

class WebhookLog(Base):
    __tablename__ = 'webhook_logs'

    id = Column(Integer, primary_key=True)
    webhook_id = Column(Integer, ForeignKey('webhooks.id'))
    event = Column(Enum(WebhookEvent))
    payload = Column(JSON)
    response_status = Column(Integer)
    response_body = Column(Text)
    error_message = Column(Text)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    webhook = relationship("Webhook", back_populates="logs")

class Alert(Base):
    __tablename__ = 'alerts'

    id = Column(Integer, primary_key=True)
    monitor_id = Column(Integer, ForeignKey('monitors.id'))
    type = Column(String(50))  # high_score, keyword_match, volume_spike
    severity = Column(String(20))  # low, medium, high, critical
    title = Column(String(255))
    message = Column(Text)
    data = Column(JSON, default={})
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    monitor = relationship("Monitor", back_populates="alerts")

# Knowledge Base for AI
class KnowledgeBase(Base):
    __tablename__ = 'knowledge_bases'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    name = Column(String(255), nullable=False)
    category = Column(String(100))
    content = Column(Text, nullable=False)
    embeddings = Column(JSON)  # Vector embeddings for semantic search
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

# Session Management
class Session(Base):
    __tablename__ = 'sessions'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    token = Column(String(500), unique=True, nullable=False, index=True)
    refresh_token = Column(String(500), unique=True, index=True)
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=func.now())
    last_activity = Column(DateTime, default=func.now())
    is_active = Column(Boolean, default=True)

# API Keys
class ApiKey(Base):
    __tablename__ = 'api_keys'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    name = Column(String(255), nullable=False)
    key = Column(String(255), unique=True, nullable=False, index=True)
    permissions = Column(JSON, default=[])
    rate_limit = Column(Integer, default=1000)  # requests per hour
    last_used = Column(DateTime)
    expires_at = Column(DateTime)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())

# Scheduled Tasks
class ScheduledTask(Base):
    __tablename__ = 'scheduled_tasks'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    task_type = Column(String(50))  # monitor_check, report_generation, cleanup
    schedule = Column(String(100))  # cron expression
    payload = Column(JSON, default={})
    last_run = Column(DateTime)
    next_run = Column(DateTime)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())