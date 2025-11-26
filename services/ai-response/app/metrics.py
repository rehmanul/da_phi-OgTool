"""Prometheus metrics for AI Response Service"""
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Counters
responses_generated = Counter(
    "ai_responses_generated_total",
    "Total number of AI responses generated",
    ["platform", "provider"],
)

generation_errors = Counter(
    "ai_generation_errors_total",
    "Total number of generation errors",
    ["provider", "error_type"],
)

responses_approved = Counter(
    "ai_responses_approved_total",
    "Total number of responses approved",
    ["auto", "platform"],
)

moderation_failures = Counter(
    "ai_moderation_failures_total",
    "Total number of moderation failures",
)

# Histograms
generation_time = Histogram(
    "ai_generation_seconds",
    "Time spent generating responses",
    ["provider", "model"],
)

token_usage = Counter(
    "ai_token_usage_total",
    "Total tokens used",
    ["provider", "model"],
)

quality_scores = Histogram(
    "ai_quality_score",
    "Distribution of quality scores",
    buckets=[0.0, 0.2, 0.4, 0.6, 0.7, 0.8, 0.9, 1.0],
)

# Gauges
active_generations = Gauge(
    "ai_active_generations",
    "Number of currently active response generations",
)

cost_per_response = Histogram(
    "ai_cost_per_response_dollars",
    "Cost per response in dollars",
    buckets=[0.001, 0.005, 0.01, 0.02, 0.05, 0.1, 0.5, 1.0],
)


def start_metrics_server(port: int = 9092):
    """Start Prometheus metrics HTTP server"""
    start_http_server(port)
