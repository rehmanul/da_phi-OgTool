#!/bin/bash

# OGTool - Stop All Services

echo "Stopping OGTool services..."

docker-compose down

echo ""
echo "All services stopped."
