# Multi-stage build for optimized image
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements from all services
# We'll merge them or install them sequentially
# Since we are monolith, we can just install all dependencies
# But we don't have a single requirements.txt yet.
# We should probably create one or install from each service.

# For now, let's copy the whole project and install dependencies
COPY . .

# Create a merged requirements.txt or install directly
# We'll use a simple script to find all requirements.txt
RUN find . -name "requirements.txt" -exec cat {} + > all_requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r all_requirements.txt
RUN pip install --no-cache-dir uvicorn fastapi asyncpg clickhouse-driver qdrant-client openai anthropic google-generativeai tiktoken structlog prometheus_client aio_pika

# Runtime stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Run the monolith
CMD ["python", "monolith.py"]
