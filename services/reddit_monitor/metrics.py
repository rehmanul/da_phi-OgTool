"""Prometheus metrics"""
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Counters
posts_processed = Counter(
    "reddit_posts_processed_total",
    "Total number of posts processed",
    ["platform", "type"],
)

posts_detected = Counter(
    "reddit_posts_detected_total",
    "Total number of relevant posts detected",
    ["platform", "priority"],
)

api_errors = Counter(
    "reddit_api_errors_total",
    "Total number of API errors",
    ["service", "error_type"],
)

# Histograms
processing_time = Histogram(
    "reddit_processing_seconds",
    "Time spent processing",
    ["service", "operation"],
)

# Gauges
active_monitors = Gauge(
    "reddit_active_monitors",
    "Number of active subreddit monitors",
)

keyword_count = Gauge(
    "reddit_keyword_count",
    "Total number of keywords being monitored",
)


def start_metrics_server(port: int = 9091):
    """Start Prometheus metrics HTTP server"""
    start_http_server(port)
