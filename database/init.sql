-- OGTool Production Database Schema
-- PostgreSQL 15+ with TimescaleDB

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search
CREATE EXTENSION IF NOT EXISTS "timescaledb";

-- Organizations and Users
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    tier VARCHAR(50) NOT NULL CHECK (tier IN ('starter', 'growth', 'enterprise')),
    api_key VARCHAR(255) UNIQUE NOT NULL,
    api_secret VARCHAR(255) NOT NULL,
    monthly_budget DECIMAL(10,2),
    current_spend DECIMAL(10,2) DEFAULT 0,
    settings JSONB DEFAULT '{}',
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) NOT NULL CHECK (role IN ('owner', 'admin', 'member', 'viewer')),
    last_login TIMESTAMPTZ,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_users_org ON users(organization_id);
CREATE INDEX idx_users_email ON users(email);

-- Personas (Voice Profiles)
CREATE TABLE personas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    voice_profile JSONB NOT NULL, -- {tone, style, formality, vocabulary, avoid_words}
    system_prompt TEXT NOT NULL,
    example_responses JSONB DEFAULT '[]', -- Array of {input, output} pairs
    temperature FLOAT DEFAULT 0.7,
    max_tokens INTEGER DEFAULT 500,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT unique_persona_name_per_org UNIQUE (organization_id, name)
);

CREATE INDEX idx_personas_org ON personas(organization_id);

-- Knowledge Bases
CREATE TABLE knowledge_bases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE knowledge_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    knowledge_base_id UUID REFERENCES knowledge_bases(id) ON DELETE CASCADE,
    title VARCHAR(500),
    content TEXT NOT NULL,
    source_url TEXT,
    document_type VARCHAR(50), -- webpage, pdf, doc, txt
    metadata JSONB DEFAULT '{}',
    embedding_id VARCHAR(255), -- Qdrant point ID
    chunk_index INTEGER DEFAULT 0,
    total_chunks INTEGER DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_knowledge_docs_kb ON knowledge_documents(knowledge_base_id);
CREATE INDEX idx_knowledge_docs_embedding ON knowledge_documents(embedding_id);

-- Link personas to knowledge bases
CREATE TABLE persona_knowledge_bases (
    persona_id UUID REFERENCES personas(id) ON DELETE CASCADE,
    knowledge_base_id UUID REFERENCES knowledge_bases(id) ON DELETE CASCADE,
    PRIMARY KEY (persona_id, knowledge_base_id)
);

-- Keywords and Monitoring Configuration
CREATE TABLE keywords (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    keyword TEXT NOT NULL,
    platform VARCHAR(50) NOT NULL CHECK (platform IN ('reddit', 'linkedin', 'blog', 'chatgpt')),
    filters JSONB DEFAULT '{}', -- Platform-specific filters
    priority INTEGER DEFAULT 50 CHECK (priority BETWEEN 0 AND 100),
    alert_threshold INTEGER DEFAULT 10, -- Minimum engagement to alert
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_keywords_org_platform ON keywords(organization_id, platform);
CREATE INDEX idx_keywords_active ON keywords(active) WHERE active = true;

-- Reddit Monitoring
CREATE TABLE subreddit_monitors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    subreddit VARCHAR(255) NOT NULL,
    engagement_threshold INTEGER DEFAULT 5,
    auto_reply BOOLEAN DEFAULT false,
    persona_id UUID REFERENCES personas(id),
    check_frequency INTEGER DEFAULT 300, -- seconds
    last_checked TIMESTAMPTZ,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT unique_subreddit_per_org UNIQUE (organization_id, subreddit)
);

CREATE INDEX idx_subreddit_monitors_org ON subreddit_monitors(organization_id);
CREATE INDEX idx_subreddit_monitors_active ON subreddit_monitors(active) WHERE active = true;

-- Link keywords to subreddits
CREATE TABLE subreddit_keywords (
    subreddit_monitor_id UUID REFERENCES subreddit_monitors(id) ON DELETE CASCADE,
    keyword_id UUID REFERENCES keywords(id) ON DELETE CASCADE,
    PRIMARY KEY (subreddit_monitor_id, keyword_id)
);

-- LinkedIn Monitoring
CREATE TABLE linkedin_monitors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    profile_url TEXT,
    company_url TEXT,
    hashtags TEXT[],
    auto_reply BOOLEAN DEFAULT false,
    persona_id UUID REFERENCES personas(id),
    check_frequency INTEGER DEFAULT 600,
    last_checked TIMESTAMPTZ,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_linkedin_monitors_org ON linkedin_monitors(organization_id);

-- Blog Monitoring
CREATE TABLE blog_monitors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    blog_url TEXT NOT NULL,
    blog_name VARCHAR(255),
    rss_feed TEXT,
    check_frequency INTEGER DEFAULT 3600,
    last_checked TIMESTAMPTZ,
    last_post_date TIMESTAMPTZ,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT unique_blog_per_org UNIQUE (organization_id, blog_url)
);

CREATE INDEX idx_blog_monitors_org ON blog_monitors(organization_id);

-- Detected Posts/Content
CREATE TABLE detected_posts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    platform VARCHAR(50) NOT NULL,
    external_id VARCHAR(500) NOT NULL, -- Reddit ID, LinkedIn post ID, etc.
    url TEXT NOT NULL,
    parent_url TEXT, -- For comments
    title TEXT,
    content TEXT NOT NULL,
    author VARCHAR(255),
    author_profile_url TEXT,
    subreddit VARCHAR(255), -- For Reddit
    engagement_score FLOAT DEFAULT 0, -- Upvotes, likes, etc.
    comment_count INTEGER DEFAULT 0,
    relevance_score FLOAT, -- AI-calculated relevance
    sentiment_score FLOAT, -- -1 to 1
    keyword_matches TEXT[],
    metadata JSONB DEFAULT '{}',
    priority VARCHAR(20) DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'urgent')),
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'reviewed', 'responded', 'ignored', 'archived')),
    detected_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT unique_post_per_platform UNIQUE (platform, external_id)
);

CREATE INDEX idx_detected_posts_org_platform ON detected_posts(organization_id, platform);
CREATE INDEX idx_detected_posts_status ON detected_posts(status) WHERE status IN ('pending', 'reviewed');
CREATE INDEX idx_detected_posts_detected_at ON detected_posts(detected_at DESC);
CREATE INDEX idx_detected_posts_priority ON detected_posts(priority, detected_at DESC);
CREATE INDEX idx_detected_posts_content_search ON detected_posts USING gin(to_tsvector('english', content));

-- Generated AI Responses
CREATE TABLE generated_responses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    post_id UUID REFERENCES detected_posts(id) ON DELETE CASCADE,
    persona_id UUID REFERENCES personas(id),
    response_text TEXT NOT NULL,
    response_metadata JSONB DEFAULT '{}', -- tokens used, model, etc.
    quality_score FLOAT, -- AI self-assessment
    sentiment_score FLOAT,
    safety_score FLOAT, -- Content moderation score
    approved BOOLEAN DEFAULT false,
    approved_by UUID REFERENCES users(id),
    approved_at TIMESTAMPTZ,
    posted BOOLEAN DEFAULT false,
    posted_at TIMESTAMPTZ,
    posted_by UUID REFERENCES users(id),
    external_response_id VARCHAR(500), -- ID on platform after posting
    engagement_data JSONB DEFAULT '{}', -- Likes, replies after posting
    cost DECIMAL(10,4), -- API cost for generation
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_generated_responses_post ON generated_responses(post_id);
CREATE INDEX idx_generated_responses_approved ON generated_responses(approved) WHERE approved = false;
CREATE INDEX idx_generated_responses_posted ON generated_responses(posted, posted_at DESC);

-- Platform Accounts (for posting)
CREATE TABLE platform_accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    platform VARCHAR(50) NOT NULL,
    account_name VARCHAR(255) NOT NULL,
    credentials JSONB NOT NULL, -- Encrypted
    proxy_config JSONB,
    rate_limit_remaining INTEGER,
    rate_limit_reset TIMESTAMPTZ,
    last_used TIMESTAMPTZ,
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'banned', 'rate_limited')),
    health_check_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT unique_platform_account UNIQUE (organization_id, platform, account_name)
);

CREATE INDEX idx_platform_accounts_org ON platform_accounts(organization_id);

-- Analytics Tables (TimescaleDB Hypertables)

-- Keyword Rankings Over Time
CREATE TABLE keyword_rankings (
    time TIMESTAMPTZ NOT NULL,
    organization_id UUID NOT NULL,
    keyword_id UUID NOT NULL,
    platform VARCHAR(50) NOT NULL,
    position INTEGER,
    mentions_count INTEGER DEFAULT 0,
    share_of_voice FLOAT DEFAULT 0,
    total_engagement INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}'
);

SELECT create_hypertable('keyword_rankings', 'time', chunk_time_interval => INTERVAL '1 day');
CREATE INDEX idx_keyword_rankings_org_time ON keyword_rankings(organization_id, time DESC);
CREATE INDEX idx_keyword_rankings_keyword ON keyword_rankings(keyword_id, time DESC);

-- Engagement Events
CREATE TABLE engagement_events (
    time TIMESTAMPTZ NOT NULL,
    organization_id UUID NOT NULL,
    post_id UUID NOT NULL,
    response_id UUID,
    event_type VARCHAR(50) NOT NULL, -- view, click, reply, upvote, conversion
    user_identifier VARCHAR(255),
    platform VARCHAR(50) NOT NULL,
    metadata JSONB DEFAULT '{}'
);

SELECT create_hypertable('engagement_events', 'time', chunk_time_interval => INTERVAL '1 day');
CREATE INDEX idx_engagement_events_org_time ON engagement_events(organization_id, time DESC);
CREATE INDEX idx_engagement_events_post ON engagement_events(post_id, time DESC);

-- API Usage Tracking
CREATE TABLE api_usage (
    time TIMESTAMPTZ NOT NULL,
    organization_id UUID NOT NULL,
    service VARCHAR(100) NOT NULL, -- openai, anthropic, reddit, etc.
    operation VARCHAR(100) NOT NULL,
    tokens_used INTEGER DEFAULT 0,
    cost DECIMAL(10,4) DEFAULT 0,
    latency_ms INTEGER,
    success BOOLEAN DEFAULT true,
    error_message TEXT
);

SELECT create_hypertable('api_usage', 'time', chunk_time_interval => INTERVAL '1 day');
CREATE INDEX idx_api_usage_org_time ON api_usage(organization_id, time DESC);

-- Audit Log
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID REFERENCES organizations(id),
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id UUID,
    changes JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_audit_logs_org_time ON audit_logs(organization_id, created_at DESC);
CREATE INDEX idx_audit_logs_user ON audit_logs(user_id, created_at DESC);

-- Notifications/Alerts
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL, -- new_post, response_generated, alert, system
    title VARCHAR(255) NOT NULL,
    message TEXT,
    link TEXT,
    read BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_notifications_user_unread ON notifications(user_id, read) WHERE read = false;

-- Webhooks
CREATE TABLE webhooks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    url TEXT NOT NULL,
    events TEXT[] NOT NULL, -- ['post.detected', 'response.generated', etc.]
    secret VARCHAR(255),
    active BOOLEAN DEFAULT true,
    last_triggered TIMESTAMPTZ,
    failure_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_webhooks_org ON webhooks(organization_id);

-- Functions and Triggers

-- Update timestamp function
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply update_updated_at trigger to relevant tables
CREATE TRIGGER update_organizations_updated_at BEFORE UPDATE ON organizations FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER update_personas_updated_at BEFORE UPDATE ON personas FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER update_keywords_updated_at BEFORE UPDATE ON keywords FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER update_detected_posts_updated_at BEFORE UPDATE ON detected_posts FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER update_generated_responses_updated_at BEFORE UPDATE ON generated_responses FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Initial Data

-- Create a default admin organization for testing
INSERT INTO organizations (name, tier, api_key, api_secret, monthly_budget)
VALUES ('Demo Organization', 'growth', 'demo-api-key-' || gen_random_uuid(), 'demo-secret-' || gen_random_uuid(), 500.00);

-- Create admin user (password: admin123 - change in production!)
INSERT INTO users (organization_id, email, password_hash, full_name, role)
VALUES (
    (SELECT id FROM organizations WHERE name = 'Demo Organization'),
    'admin@demo.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5lZjKqW4kEfxi', -- bcrypt hash of 'admin123'
    'Demo Admin',
    'owner'
);

-- Create continuous aggregates for analytics

-- Hourly keyword rankings aggregate
CREATE MATERIALIZED VIEW keyword_rankings_hourly
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', time) AS hour,
    organization_id,
    keyword_id,
    platform,
    AVG(position) AS avg_position,
    SUM(mentions_count) AS total_mentions,
    AVG(share_of_voice) AS avg_share_of_voice,
    SUM(total_engagement) AS total_engagement
FROM keyword_rankings
GROUP BY hour, organization_id, keyword_id, platform
WITH NO DATA;

SELECT add_continuous_aggregate_policy('keyword_rankings_hourly',
    start_offset => INTERVAL '3 hours',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour');

-- Daily engagement summary
CREATE MATERIALIZED VIEW engagement_daily
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', time) AS day,
    organization_id,
    platform,
    event_type,
    COUNT(*) AS event_count
FROM engagement_events
GROUP BY day, organization_id, platform, event_type
WITH NO DATA;

SELECT add_continuous_aggregate_policy('engagement_daily',
    start_offset => INTERVAL '3 days',
    end_offset => INTERVAL '1 day',
    schedule_interval => INTERVAL '1 day');

-- Retention policies (keep detailed data for 90 days, aggregates for 2 years)
SELECT add_retention_policy('engagement_events', INTERVAL '90 days');
SELECT add_retention_policy('api_usage', INTERVAL '90 days');
SELECT add_retention_policy('keyword_rankings', INTERVAL '90 days');

COMMENT ON TABLE organizations IS 'Organizations (companies) using the platform';
COMMENT ON TABLE personas IS 'AI voice profiles for response generation';
COMMENT ON TABLE detected_posts IS 'Posts detected from Reddit, LinkedIn, blogs';
COMMENT ON TABLE generated_responses IS 'AI-generated responses to detected posts';
COMMENT ON TABLE keyword_rankings IS 'Time-series data for keyword performance tracking';
COMMENT ON TABLE engagement_events IS 'Time-series data for engagement tracking';
