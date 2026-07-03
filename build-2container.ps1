# Quick Build and Test Script for 2-Container Setup
# Run this script to build and test the new architecture

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Plankton 2-Container Setup - Build & Test" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if .env file exists
if (-Not (Test-Path ".env")) {
    Write-Host "WARNING: .env file not found!" -ForegroundColor Yellow
    Write-Host "Creating .env from .env.example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host ""
    Write-Host "IMPORTANT: Edit .env and add your GROQ_API_KEY!" -ForegroundColor Red
    Write-Host "   Open .env file and replace your_groq_api_key_here with your actual key" -ForegroundColor Yellow
    Write-Host ""
    $continue = Read-Host "Press Enter when you have updated .env, or Ctrl+C to exit"
}

Write-Host "Step 1: Building SQL Agent container..." -ForegroundColor Green
docker build -t plankton-sql-agent ./services/sql-agent
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to build SQL Agent container" -ForegroundColor Red
    exit 1
}
Write-Host "SQL Agent container built successfully" -ForegroundColor Green
Write-Host ""

Write-Host "Step 2: Building Main App container..." -ForegroundColor Green
docker build -t plankton-app -f Dockerfile.minimal .
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to build Main App container" -ForegroundColor Red
    exit 1
}
Write-Host "Main App container built successfully" -ForegroundColor Green
Write-Host ""

Write-Host "Step 3: Starting both containers..." -ForegroundColor Green
docker-compose -f docker-compose-2container.yml up -d
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to start containers" -ForegroundColor Red
    exit 1
}
Write-Host "Containers started successfully" -ForegroundColor Green
Write-Host ""

Write-Host "Step 4: Waiting for services to be ready..." -ForegroundColor Green
Start-Sleep -Seconds 10

Write-Host "Step 5: Testing SQL Agent health..." -ForegroundColor Green
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8002/health" -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "SQL Agent is healthy!" -ForegroundColor Green
    }
} catch {
    Write-Host "SQL Agent health check failed: $_" -ForegroundColor Yellow
    Write-Host "   Check logs: docker-compose -f docker-compose-2container.yml logs sql-agent" -ForegroundColor Yellow
}
Write-Host ""

Write-Host "Step 6: Testing Main App health..." -ForegroundColor Green
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8501/_stcore/health" -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "Main App is healthy!" -ForegroundColor Green
    }
} catch {
    Write-Host "Main App health check failed: $_" -ForegroundColor Yellow
    Write-Host "   Check logs: docker-compose -f docker-compose-2container.yml logs plankton-app" -ForegroundColor Yellow
}
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Access your application:" -ForegroundColor White
Write-Host "  - Streamlit UI:    http://localhost:8501" -ForegroundColor Cyan
Write-Host "  - SQL Agent API:   http://localhost:8002" -ForegroundColor Cyan
Write-Host "  - SQL Agent Docs:  http://localhost:8002/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "Useful commands:" -ForegroundColor White
Write-Host "  - View logs:       docker-compose -f docker-compose-2container.yml logs -f" -ForegroundColor Yellow
Write-Host "  - Stop services:   docker-compose -f docker-compose-2container.yml down" -ForegroundColor Yellow
Write-Host "  - Restart:         docker-compose -f docker-compose-2container.yml restart" -ForegroundColor Yellow
Write-Host "  - Check status:    docker-compose -f docker-compose-2container.yml ps" -ForegroundColor Yellow
Write-Host ""
