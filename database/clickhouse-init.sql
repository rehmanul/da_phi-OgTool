-- ClickHouse Analytics Database Schema
-- Optimized for fast analytical queries

-- Share of Voice tracking
CREATE TABLE IF NOT EXISTS share_of_voice (
    timestamp DateTime,
    organization_id String,
    keyword String,
    platform String,
    our_mentions UInt32,
    competitor_mentions UInt32,
    total_mentions UInt32,
    share_percentage Float32,
    avg_engagement Float32,
    date Date MATERIALIZED toDate(timestamp)
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (organization_id, platform, keyword, timestamp)
TTL date + INTERVAL 2 YEAR;

-- Platform activity metrics
CREATE TABLE IF NOT EXISTS platform_activity (
    timestamp DateTime,
    organization_id String,
    platform String,
    activity_type String, -- post, comment, reply, like
    post_id String,
    response_id Nullable(String),
    engagement_count UInt32,
    sentiment_score Float32,
    date Date MATERIALIZED toDate(timestamp)
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (organization_id, platform, timestamp)
TTL date + INTERVAL 1 YEAR;

-- Conversion attribution
CREATE TABLE IF NOT EXISTS conversions (
    timestamp DateTime,
    organization_id String,
    conversion_id String,
    post_id String,
    response_id Nullable(String),
    platform String,
    conversion_value Float32,
    conversion_type String, -- lead, signup, purchase
    attribution_model String, -- first_touch, last_touch, linear
    touchpoint_count UInt8,
    date Date MATERIALIZED toDate(timestamp)
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (organization_id, timestamp)
TTL date + INTERVAL 2 YEAR;

-- Cost tracking
CREATE TABLE IF NOT EXISTS cost_tracking (
    timestamp DateTime,
    organization_id String,
    service String, -- openai, anthropic, reddit_api, proxy
    operation String,
    units_used UInt32, -- tokens, requests, etc.
    cost Float32,
    date Date MATERIALIZED toDate(timestamp)
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (organization_id, service, timestamp)
TTL date + INTERVAL 2 YEAR;

-- Response performance
CREATE TABLE IF NOT EXISTS response_performance (
    timestamp DateTime,
    organization_id String,
    response_id String,
    post_id String,
    persona_id String,
    platform String,
    generation_time_ms UInt32,
    quality_score Float32,
    upvotes UInt32,
    downvotes UInt32,
    replies UInt32,
    conversion_attributed Boolean,
    date Date MATERIALIZED toDate(timestamp)
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (organization_id, timestamp)
TTL date + INTERVAL 1 YEAR;

-- Keyword performance
CREATE TABLE IF NOT EXISTS keyword_performance (
    timestamp DateTime,
    organization_id String,
    keyword_id String,
    keyword String,
    platform String,
    search_volume UInt32,
    position UInt16,
    mentions UInt32,
    avg_sentiment Float32,
    competitor_mentions UInt32,
    date Date MATERIALIZED toDate(timestamp)
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (organization_id, keyword, platform, timestamp)
TTL date + INTERVAL 2 YEAR;

-- ChatGPT mentions tracking
CREATE TABLE IF NOT EXISTS chatgpt_mentions (
    timestamp DateTime,
    organization_id String,
    keyword String,
    mention_context String,
    source String, -- plugin, web, api
    sentiment_score Float32,
    competitor_mentioned Boolean,
    date Date MATERIALIZED toDate(timestamp)
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (organization_id, keyword, timestamp)
TTL date + INTERVAL 2 YEAR;

-- Materialized views for common queries

-- Daily aggregated share of voice
CREATE MATERIALIZED VIEW IF NOT EXISTS share_of_voice_daily
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (organization_id, keyword, platform, date)
AS SELECT
    toDate(timestamp) as date,
    organization_id,
    keyword,
    platform,
    sum(our_mentions) as our_mentions,
    sum(competitor_mentions) as competitor_mentions,
    sum(total_mentions) as total_mentions,
    avg(share_percentage) as avg_share_percentage
FROM share_of_voice
GROUP BY date, organization_id, keyword, platform;

-- Hourly cost rollup
CREATE MATERIALIZED VIEW IF NOT EXISTS cost_hourly
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (organization_id, service, date, hour)
AS SELECT
    toDate(timestamp) as date,
    toHour(timestamp) as hour,
    organization_id,
    service,
    sum(units_used) as total_units,
    sum(cost) as total_cost
FROM cost_tracking
GROUP BY date, hour, organization_id, service;

-- Daily response metrics
CREATE MATERIALIZED VIEW IF NOT EXISTS response_metrics_daily
ENGINE = AggregatingMergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (organization_id, platform, date)
AS SELECT
    toDate(timestamp) as date,
    organization_id,
    platform,
    count() as response_count,
    avg(quality_score) as avg_quality_score,
    avg(generation_time_ms) as avg_generation_time,
    sum(upvotes) as total_upvotes,
    sum(replies) as total_replies,
    countIf(conversion_attributed) as conversions
FROM response_performance
GROUP BY date, organization_id, platform;
