# OGTool Clone - Production Architecture

## System Overview

### Core Components
1. **Multi-Platform Monitoring Engine** - Real-time tracking of Reddit, LinkedIn, Blogs, ChatGPT mentions
2. **AI Response Generator** - LLM-powered response creation with persona management
3. **Analytics Pipeline** - Share of voice, keyword rankings, attribution tracking
4. **Knowledge Base Engine** - Vector storage for context-aware responses
5. **API Gateway** - RESTful API for external integrations
6. **Admin Dashboard** - Real-time monitoring and management interface

## Technology Stack

### Backend Services
- **Primary API**: FastAPI (Python 3.11+) - High performance async operations
- **Task Queue**: Celery + Redis - Background job processing
- **Message Broker**: RabbitMQ - Event-driven architecture
- **Real-time Updates**: WebSocket (FastAPI WebSocket)

### Data Layer
- **Primary Database**: PostgreSQL 15+ with TimescaleDB extension
- **Cache Layer**: Redis Cluster (separate from Celery)
- **Vector Store**: Qdrant or Weaviate for embeddings
- **Time-Series Data**: ClickHouse for analytics
- **Search Engine**: Elasticsearch for full-text search

### AI/ML Infrastructure
- **LLM Provider**: OpenAI GPT-4 (primary), Anthropic Claude (fallback)
- **Embeddings**: OpenAI text-embedding-3-large
- **Fine-tuning**: Custom LoRA adapters on Llama-3-70B (self-hosted)
- **Vector Operations**: LangChain + FAISS

### Frontend
- **Framework**: Next.js 14+ (App Router)
- **UI Library**: Shadcn/ui + Tailwind CSS
- **State Management**: Zustand + React Query
- **Real-time**: Socket.io client
- **Charts**: Recharts + D3.js

### Infrastructure
- **Container Orchestration**: Kubernetes (EKS/GKE/AKS)
- **CI/CD**: GitHub Actions + ArgoCD
- **Monitoring**: Prometheus + Grafana
- **Logging**: ELK Stack (Elasticsearch, Logstash, Kibana)
- **Tracing**: Jaeger
- **Secret Management**: HashiCorp Vault
- **CDN**: CloudFlare
- **Object Storage**: AWS S3/MinIO

## Service Architecture

### Microservices Breakdown

#### 1. Reddit Monitoring Service
```
reddit-monitor-service/
├── listener/          # Pushshift alternative + Reddit API
├── processor/         # Content analysis and scoring
├── keyword-matcher/   # Keyword detection engine
└── alert-generator/   # Trigger system
```

#### 2. LinkedIn Monitoring Service
```
linkedin-monitor-service/
├── scraper/          # Selenium Grid + Playwright
├── content-parser/   # Extract and normalize posts
├── engagement-tracker/ # Track interactions
└── webhook-handler/  # LinkedIn API events
```

#### 3. Blog Monitoring Service
```
blog-monitor-service/
├── rss-crawler/      # RSS feed aggregation
├── web-scraper/      # Full blog scraping (Scrapy)
├── change-detector/  # Detect new posts
└── content-extractor/ # Clean content extraction
```

#### 4. ChatGPT Mention Tracker
```
chatgpt-tracker-service/
├── plugin-monitor/   # Track ChatGPT plugin store
├── web-scraper/      # Monitor ChatGPT-related discussions
└── api-listener/     # OpenAI API usage tracking
```

#### 5. AI Response Engine
```
ai-response-service/
├── context-builder/  # Aggregate context from KB
├── persona-manager/  # Load and apply personas
├── response-generator/ # LLM orchestration
├── safety-checker/   # Content moderation
└── quality-scorer/   # Response quality assessment
```

#### 6. Analytics Engine
```
analytics-service/
├── share-of-voice/   # Calculate SOV metrics
├── keyword-ranker/   # Track keyword positions
├── attribution/      # Link engagement to conversions
└── reporter/         # Generate reports
```

## Database Schema

### Core Tables

```sql
-- Users and Organizations
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    tier VARCHAR(50) NOT NULL, -- starter, growth, enterprise
    api_key VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL, -- admin, member, viewer
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Personas
CREATE TABLE personas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id),
    name VARCHAR(255) NOT NULL,
    voice_profile JSONB NOT NULL, -- tone, style, vocabulary
    knowledge_base_ids UUID[] NOT NULL,
    example_responses JSONB,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Monitoring Configuration
CREATE TABLE keywords (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id),
    keyword TEXT NOT NULL,
    platform VARCHAR(50) NOT NULL, -- reddit, linkedin, blog, chatgpt
    filters JSONB, -- subreddit, language, etc.
    priority INTEGER DEFAULT 50,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE subreddit_monitors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id),
    subreddit VARCHAR(255) NOT NULL,
    keyword_ids UUID[] NOT NULL,
    engagement_threshold INTEGER DEFAULT 5,
    auto_reply BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE blog_monitors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id),
    blog_url TEXT NOT NULL,
    rss_feed TEXT,
    check_frequency INTEGER DEFAULT 3600, -- seconds
    last_checked TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Content Tracking
CREATE TABLE detected_posts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id),
    platform VARCHAR(50) NOT NULL,
    external_id VARCHAR(255) NOT NULL, -- Reddit ID, LinkedIn ID, etc.
    url TEXT NOT NULL,
    title TEXT,
    content TEXT NOT NULL,
    author VARCHAR(255),
    engagement_score FLOAT,
    relevance_score FLOAT,
    keyword_matches TEXT[],
    metadata JSONB,
    detected_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(platform, external_id)
);

CREATE TABLE generated_responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    post_id UUID REFERENCES detected_posts(id),
    persona_id UUID REFERENCES personas(id),
    response_text TEXT NOT NULL,
    quality_score FLOAT,
    sentiment_score FLOAT,
    approved BOOLEAN DEFAULT false,
    posted BOOLEAN DEFAULT false,
    posted_at TIMESTAMPTZ,
    engagement_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Knowledge Base
CREATE TABLE knowledge_bases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE knowledge_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    knowledge_base_id UUID REFERENCES knowledge_bases(id),
    title VARCHAR(255),
    content TEXT NOT NULL,
    source_url TEXT,
    metadata JSONB,
    embedding_id VARCHAR(255), -- Reference to vector store
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Analytics (TimescaleDB hypertables)
CREATE TABLE keyword_rankings (
    time TIMESTAMPTZ NOT NULL,
    organization_id UUID NOT NULL,
    keyword_id UUID NOT NULL,
    platform VARCHAR(50) NOT NULL,
    position INTEGER,
    mentions_count INTEGER,
    share_of_voice FLOAT,
    PRIMARY KEY (time, organization_id, keyword_id, platform)
);

SELECT create_hypertable('keyword_rankings', 'time');

CREATE TABLE engagement_events (
    time TIMESTAMPTZ NOT NULL,
    organization_id UUID NOT NULL,
    post_id UUID NOT NULL,
    response_id UUID,
    event_type VARCHAR(50) NOT NULL, -- view, click, reply, conversion
    user_id VARCHAR(255),
    metadata JSONB,
    PRIMARY KEY (time, organization_id, post_id, event_type)
);

SELECT create_hypertable('engagement_events', 'time');

-- Indexes
CREATE INDEX idx_keywords_org_platform ON keywords(organization_id, platform);
CREATE INDEX idx_detected_posts_org_platform ON detected_posts(organization_id, platform);
CREATE INDEX idx_detected_posts_detected_at ON detected_posts(detected_at DESC);
CREATE INDEX idx_generated_responses_post ON generated_responses(post_id);
CREATE INDEX idx_engagement_events_org ON engagement_events(organization_id, time DESC);
```

## API Endpoints

### Authentication
```
POST   /api/v1/auth/register
POST   /api/v1/auth/login
POST   /api/v1/auth/refresh
POST   /api/v1/auth/logout
```

### Keyword Management
```
GET    /api/v1/keywords
POST   /api/v1/keywords
GET    /api/v1/keywords/{id}
PUT    /api/v1/keywords/{id}
DELETE /api/v1/keywords/{id}
```

### Monitoring Configuration
```
GET    /api/v1/monitors/reddit
POST   /api/v1/monitors/reddit
PUT    /api/v1/monitors/reddit/{id}
DELETE /api/v1/monitors/reddit/{id}

GET    /api/v1/monitors/linkedin
POST   /api/v1/monitors/linkedin
...

GET    /api/v1/monitors/blogs
POST   /api/v1/monitors/blogs
...
```

### Detected Content
```
GET    /api/v1/posts                    # List all detected posts
GET    /api/v1/posts/{id}               # Get specific post
POST   /api/v1/posts/{id}/generate      # Generate AI response
POST   /api/v1/posts/{id}/approve       # Approve response
POST   /api/v1/posts/{id}/post          # Actually post to platform
GET    /api/v1/posts/{id}/analytics     # Get engagement data
```

### Personas
```
GET    /api/v1/personas
POST   /api/v1/personas
PUT    /api/v1/personas/{id}
DELETE /api/v1/personas/{id}
POST   /api/v1/personas/{id}/train      # Fine-tune with examples
```

### Knowledge Base
```
GET    /api/v1/knowledge-bases
POST   /api/v1/knowledge-bases
POST   /api/v1/knowledge-bases/{id}/upload
DELETE /api/v1/knowledge-bases/{id}/documents/{doc_id}
```

### Analytics
```
GET    /api/v1/analytics/share-of-voice
GET    /api/v1/analytics/keyword-rankings
GET    /api/v1/analytics/engagement
GET    /api/v1/analytics/attribution
GET    /api/v1/analytics/chatgpt-mentions
```

### WebSocket Events
```
WS     /api/v1/ws/posts         # Real-time post notifications
WS     /api/v1/ws/analytics     # Live analytics updates
```

## Deployment Configuration

### Kubernetes Structure
```
k8s/
├── namespaces/
│   ├── production.yaml
│   ├── staging.yaml
│   └── monitoring.yaml
├── services/
│   ├── api-gateway/
│   ├── reddit-monitor/
│   ├── linkedin-monitor/
│   ├── blog-monitor/
│   ├── ai-response/
│   └── analytics/
├── databases/
│   ├── postgresql/
│   ├── redis/
│   ├── rabbitmq/
│   ├── clickhouse/
│   └── elasticsearch/
├── ingress/
│   └── nginx-ingress.yaml
└── monitoring/
    ├── prometheus.yaml
    ├── grafana.yaml
    └── alert-manager.yaml
```

### Resource Allocation

#### API Gateway
- Replicas: 3 (auto-scale 3-10)
- CPU: 1-2 cores
- Memory: 2-4GB
- Rate Limit: 1000 req/min per org

#### Reddit Monitor
- Replicas: 5 (auto-scale 5-20)
- CPU: 2-4 cores
- Memory: 4-8GB
- Batch Size: 100 posts/iteration

#### AI Response Service
- Replicas: 3 (auto-scale 3-15)
- CPU: 4-8 cores
- Memory: 16-32GB
- GPU: Optional NVIDIA T4 for self-hosted models

#### Analytics Engine
- Replicas: 2 (fixed)
- CPU: 8-16 cores
- Memory: 32-64GB
- Batch processing: Hourly aggregations

## Security Implementation

### Authentication & Authorization
- JWT tokens with RS256 signing
- Refresh token rotation
- Role-Based Access Control (RBAC)
- API key management per organization
- Rate limiting per tier

### Data Protection
- Encryption at rest (AES-256)
- TLS 1.3 for all connections
- Secrets in HashiCorp Vault
- Database encryption
- PII anonymization in logs

### API Security
- OWASP API Security Top 10 compliance
- Input validation on all endpoints
- SQL injection prevention (parameterized queries)
- XSS protection
- CSRF tokens for web interface
- CORS configuration

### Platform Compliance
- Reddit API rate limits: 60 requests/minute
- LinkedIn scraping: User-agent rotation, proxy pool
- ChatGPT: Terms of service compliance
- GDPR compliance for EU users

## Monitoring & Alerting

### Key Metrics
- API response time (p50, p95, p99)
- Service availability (uptime %)
- Error rates by service
- Queue depth (Celery/RabbitMQ)
- Database connection pool usage
- LLM API latency and cost
- Post detection rate
- Response generation success rate

### Alerts
- Service down > 2 minutes
- Error rate > 5% for 5 minutes
- Queue depth > 10,000 jobs
- Database CPU > 80%
- LLM API failures > 10/minute
- Reddit/LinkedIn account flagged
- Cost anomaly detection

## Cost Optimization

### Compute
- Spot instances for batch jobs
- Auto-scaling based on load
- Scheduled scaling (business hours)
- Reserved instances for base load

### Storage
- S3 lifecycle policies
- Database partitioning and archival
- CDN caching for static assets
- Redis eviction policies

### AI/ML
- Batch LLM requests when possible
- Cache common responses
- Use cheaper models for quality scoring
- Self-host embedding generation
- Monitor token usage per org

## Disaster Recovery

### Backup Strategy
- Database: Continuous replication + hourly snapshots
- Vector store: Daily backups
- Configuration: Git-backed with ArgoCD
- Retention: 30 days hot, 1 year cold

### Recovery Objectives
- RPO: 1 hour (Recovery Point Objective)
- RTO: 4 hours (Recovery Time Objective)
- Multi-region deployment for enterprise tier

## Performance Targets

- API response time: < 200ms (p95)
- Post detection latency: < 5 minutes
- AI response generation: < 10 seconds
- Dashboard load time: < 2 seconds
- WebSocket message delivery: < 500ms
- Analytics query response: < 3 seconds
- System uptime: 99.9% (SLA)
