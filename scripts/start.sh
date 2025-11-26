#!/bin/bash

# OGTool - Start All Services

echo "Starting OGTool services..."

docker-compose up -d

echo ""
echo "All services started!"
echo ""
echo "Access points:"
echo "  - Dashboard: http://localhost:3000"
echo "  - API Docs:  http://localhost:8000/docs"
echo ""
echo "To view logs: docker-compose logs -f [service-name]"
