#!/bin/bash

# OGTool - Complete Setup Script
# Run this script to set up the entire project

set -e

echo "==================================="
echo "  OGTool - Complete Setup"
echo "==================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Edit .env file with your API keys:"
    echo "   - REDDIT_CLIENT_ID"
    echo "   - REDDIT_CLIENT_SECRET"
    echo "   - OPENAI_API_KEY"
    echo "   - ANTHROPIC_API_KEY"
    echo "   - LINKEDIN_EMAIL"
    echo "   - LINKEDIN_PASSWORD"
    echo ""
    read -p "Press Enter after you've updated .env file..."
fi

# Pull Docker images
echo "Pulling Docker images..."
docker-compose pull

# Build services
echo "Building services..."
docker-compose build

# Start infrastructure
echo "Starting infrastructure services..."
docker-compose up -d postgres redis rabbitmq qdrant clickhouse elasticsearch

# Wait for databases
echo "Waiting for databases to initialize (30 seconds)..."
sleep 30

# Initialize databases
echo "Initializing PostgreSQL database..."
docker-compose exec -T postgres psql -U ogtool -d ogtool < database/init.sql

echo "Initializing ClickHouse database..."
docker-compose exec -T clickhouse clickhouse-client --multiquery < database/clickhouse-init.sql

# Start all services
echo "Starting all services..."
docker-compose up -d

echo ""
echo "==================================="
echo "  Setup Complete!"
echo "==================================="
echo ""
echo "Services are now running:"
echo "  - Frontend:      http://localhost:3000"
echo "  - API:           http://localhost:8000"
echo "  - API Docs:      http://localhost:8000/docs"
echo "  - Grafana:       http://localhost:3001 (admin/admin)"
echo "  - Prometheus:    http://localhost:9090"
echo "  - RabbitMQ:      http://localhost:15672 (ogtool/ogtool_pass)"
echo ""
echo "To view logs: docker-compose logs -f"
echo "To stop:      docker-compose down"
echo ""
