#!/bin/bash
# Quick Build and Test Script for 2-Container Setup (Linux/Mac)

echo "========================================"
echo "Plankton 2-Container Setup - Build & Test"
echo "========================================"
echo ""

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  WARNING: .env file not found!"
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo ""
    echo "📝 IMPORTANT: Edit .env and add your GROQ_API_KEY!"
    echo "   Open .env file and replace 'your_groq_api_key_here' with your actual key"
    echo ""
    read -p "Press Enter when you've updated .env, or Ctrl+C to exit"
fi

echo "Step 1: Building SQL Agent container..."
docker build -t plankton-sql-agent ./services/sql-agent
if [ $? -ne 0 ]; then
    echo "❌ Failed to build SQL Agent container"
    exit 1
fi
echo "✅ SQL Agent container built successfully"
echo ""

echo "Step 2: Building Main App container..."
docker build -t plankton-app -f Dockerfile.minimal .
if [ $? -ne 0 ]; then
    echo "❌ Failed to build Main App container"
    exit 1
fi
echo "✅ Main App container built successfully"
echo ""

echo "Step 3: Starting both containers..."
docker-compose -f docker-compose-2container.yml up -d
if [ $? -ne 0 ]; then
    echo "❌ Failed to start containers"
    exit 1
fi
echo "✅ Containers started successfully"
echo ""

echo "Step 4: Waiting for services to be ready..."
sleep 10

echo "Step 5: Testing SQL Agent health..."
if curl -f http://localhost:8002/health > /dev/null 2>&1; then
    echo "✅ SQL Agent is healthy!"
else
    echo "⚠️  SQL Agent health check failed"
    echo "   Check logs: docker-compose -f docker-compose-2container.yml logs sql-agent"
fi
echo ""

echo "Step 6: Testing Main App health..."
if curl -f http://localhost:8501/_stcore/health > /dev/null 2>&1; then
    echo "✅ Main App is healthy!"
else
    echo "⚠️  Main App health check failed"
    echo "   Check logs: docker-compose -f docker-compose-2container.yml logs plankton-app"
fi
echo ""

echo "========================================"
echo "🎉 Setup Complete!"
echo "========================================"
echo ""
echo "Access your application:"
echo "  • Streamlit UI:    http://localhost:8501"
echo "  • SQL Agent API:   http://localhost:8002"
echo "  • SQL Agent Docs:  http://localhost:8002/docs"
echo ""
echo "Useful commands:"
echo "  • View logs:       docker-compose -f docker-compose-2container.yml logs -f"
echo "  • Stop services:   docker-compose -f docker-compose-2container.yml down"
echo "  • Restart:         docker-compose -f docker-compose-2container.yml restart"
echo "  • Check status:    docker-compose -f docker-compose-2container.yml ps"
echo ""
