"""Prometheus metrics"""
from prometheus_client import Counter, Histogram, start_http_server

# Counters
posts_processed = Counter(
    "linkedin_posts_processed_total",
    "Total number of LinkedIn posts processed",
    ["platform", "type"],
)

posts_detected = Counter(
    "linkedin_posts_detected_total",
    "Total number of relevant LinkedIn posts detected",
    ["platform", "priority"],
)

scraping_errors = Counter(
    "linkedin_scraping_errors_total",
    "Total number of scraping errors",
    ["source", "error_type"],
)

# Histograms
processing_time = Histogram(
    "linkedin_processing_seconds",
    "Time spent processing LinkedIn content",
    ["operation"],
)


def start_metrics_server(port: int = 9093):
    """Start Prometheus metrics HTTP server"""
    start_http_server(port)
