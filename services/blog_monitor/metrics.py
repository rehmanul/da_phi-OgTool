"""Prometheus metrics"""
from prometheus_client import Counter, Histogram, start_http_server

# Counters
posts_processed = Counter(
    "blog_posts_processed_total",
    "Total number of blog posts processed",
    ["platform", "type"],
)

posts_detected = Counter(
    "blog_posts_detected_total",
    "Total number of relevant blog posts detected",
    ["platform", "priority"],
)

fetch_errors = Counter(
    "blog_fetch_errors_total",
    "Total number of fetch errors",
    ["source", "error_type"],
)

# Histograms
processing_time = Histogram(
    "blog_processing_seconds",
    "Time spent processing blog content",
    ["operation"],
)


def start_metrics_server(port: int = 9094):
    """Start Prometheus metrics HTTP server"""
    start_http_server(port)
