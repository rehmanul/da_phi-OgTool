@echo off
REM OGTool - Windows Setup Script

echo ===================================
echo   OGTool - Complete Setup
echo ===================================
echo.

REM Check if .env exists
if not exist .env (
    echo Creating .env file from .env.example...
    copy .env.example .env
    echo.
    echo WARNING: Edit .env file with your API keys:
    echo    - REDDIT_CLIENT_ID
    echo    - REDDIT_CLIENT_SECRET
    echo    - OPENAI_API_KEY
    echo    - ANTHROPIC_API_KEY
    echo    - LINKEDIN_EMAIL
    echo    - LINKEDIN_PASSWORD
    echo.
    pause
)

echo Pulling Docker images...
docker-compose pull

echo Building services...
docker-compose build

echo Starting infrastructure services...
docker-compose up -d postgres redis rabbitmq qdrant clickhouse elasticsearch

echo Waiting for databases to initialize (30 seconds)...
timeout /t 30 /nobreak

echo Initializing databases...
docker-compose exec -T postgres psql -U ogtool -d ogtool < database\init.sql

echo Starting all services...
docker-compose up -d

echo.
echo ===================================
echo   Setup Complete!
echo ===================================
echo.
echo Services are now running:
echo   - Frontend:      http://localhost:3000
echo   - API:           http://localhost:8000
echo   - API Docs:      http://localhost:8000/docs
echo   - Grafana:       http://localhost:3001
echo.
echo To view logs: docker-compose logs -f
echo To stop:      docker-compose down
echo.
pause
