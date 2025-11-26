"""Prometheus metrics"""
from prometheus_client import Counter, Histogram, start_http_server

# Counters
events_processed = Counter(
    "analytics_events_processed_total",
    "Total number of analytics events processed",
    ["event_type"],
)

aggregations_completed = Counter(
    "analytics_aggregations_completed_total",
    "Total number of aggregations completed",
    ["interval"],
)

# Histograms
processing_time = Histogram(
    "analytics_processing_seconds",
    "Time spent processing analytics",
    ["operation"],
)


def start_metrics_server(port: int = 9095):
    """Start Prometheus metrics HTTP server"""
    start_http_server(port)
