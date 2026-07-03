# 2-Container Docker Setup Guide

## Overview

Your Plankton Detection System is now split into 2 Docker containers:

1. **Main Container** (`plankton-app`) - Streamlit UI + Image/Batch/Video Processing (~2.5GB)
2. **SQL Agent Container** (`sql-agent`) - Natural language database queries (~500MB)

## Quick Start

### 1. Set up environment variables

```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your Groq API key
# GROQ_API_KEY=your_actual_key_here
```

### 2. Build and run both containers

```bash
# Build and start both services
docker-compose -f docker-compose-2container.yml up -d --build

# View logs
docker-compose -f docker-compose-2container.yml logs -f
```

### 3. Access the application

- **Streamlit UI**: http://localhost:8501
- **SQL Agent API**: http://localhost:8002
- **SQL Agent Docs**: http://localhost:8002/docs

## Running Options

### Option A: Run both containers (Full functionality)

```bash
docker-compose -f docker-compose-2container.yml up -d
```

All 4 features work:
- ✅ Image Analysis
- ✅ Batch Processing
- ✅ Video Analysis
- ✅ Chat with Database

### Option B: Run only main app (Save RAM)

```bash
docker-compose -f docker-compose-2container.yml up -d plankton-app
```

3 features work, SQL Agent unavailable:
- ✅ Image Analysis
- ✅ Batch Processing
- ✅ Video Analysis
- ❌ Chat with Database (shows "Service unavailable")

### Option C: Run only SQL Agent

```bash
docker-compose -f docker-compose-2container.yml up -d sql-agent
```

Useful for testing SQL Agent independently.

## Resource Usage

| Container | RAM Usage | Disk Size |
|-----------|-----------|-----------|
| plankton-app | ~1.5-2GB | ~2.5GB |
| sql-agent | ~256-512MB | ~500MB |
| **Total** | **~2-2.5GB** | **~3GB** |

**Raspberry Pi Recommendation**: 
- Pi 4/5 with 4GB RAM: Run both containers
- Pi 4/5 with 8GB RAM: Run both containers comfortably
- Limited RAM: Run only `plankton-app`, disable SQL Agent

## Management Commands

```bash
# Stop all services
docker-compose -f docker-compose-2container.yml down

# Restart a specific service
docker-compose -f docker-compose-2container.yml restart plankton-app
docker-compose -f docker-compose-2container.yml restart sql-agent

# View logs for specific service
docker-compose -f docker-compose-2container.yml logs -f plankton-app
docker-compose -f docker-compose-2container.yml logs -f sql-agent

# Rebuild after code changes
docker-compose -f docker-compose-2container.yml up -d --build

# Check service status
docker-compose -f docker-compose-2container.yml ps

# View resource usage
docker stats
```

## Testing SQL Agent Independently

```bash
# Health check
curl http://localhost:8002/health

# Example query
curl -X POST http://localhost:8002/query \
  -H "Content-Type: application/json" \
  -d '{"question": "How many detections were made today?"}'

# Get example questions
curl http://localhost:8002/examples

# Get database schema
curl http://localhost:8002/schema
```

## Troubleshooting

### SQL Agent not connecting

1. Check if SQL Agent container is running:
   ```bash
   docker-compose -f docker-compose-2container.yml ps
   ```

2. Check SQL Agent logs:
   ```bash
   docker-compose -f docker-compose-2container.yml logs sql-agent
   ```

3. Verify GROQ_API_KEY is set in `.env` file

4. Test SQL Agent health:
   ```bash
   curl http://localhost:8002/health
   ```

### Main app can't connect to SQL Agent

1. Verify both containers are on the same network:
   ```bash
   docker network inspect plankton_plankton-network
   ```

2. Check `SQL_AGENT_URL` environment variable in main app

3. Restart both containers:
   ```bash
   docker-compose -f docker-compose-2container.yml restart
   ```

### Out of memory on Raspberry Pi

1. Stop SQL Agent to save RAM:
   ```bash
   docker-compose -f docker-compose-2container.yml stop sql-agent
   ```

2. Reduce memory limits in `docker-compose-2container.yml`

3. Monitor resource usage:
   ```bash
   docker stats
   ```

## Rollback to Monolithic Setup

If you encounter issues, you can easily rollback:

```bash
# Stop 2-container setup
docker-compose -f docker-compose-2container.yml down

# Use original monolithic setup
docker-compose up -d
```

## File Structure

```
d:\Plankton/
├── services/
│   └── sql-agent/              # NEW - SQL Agent service
│       ├── main.py             # FastAPI server
│       ├── sql_agent.py        # Copy of SQL Agent logic
│       ├── Dockerfile          # Lightweight container
│       ├── requirements.txt    # Only LangChain deps
│       └── README.md           # Service documentation
│
├── docker-compose-2container.yml  # NEW - 2-container orchestration
├── docker-compose.yml              # Original monolithic setup
├── .env.example                    # Updated with SQL Agent config
└── .env                            # Your actual config (create this)
```

## Next Steps

1. ✅ Set your GROQ_API_KEY in `.env`
2. ✅ Build and test both containers
3. ✅ Verify all features work
4. ✅ Deploy to Raspberry Pi
5. ✅ Monitor resource usage

## Benefits of 2-Container Setup

- ✅ **Smaller main image**: 2.5GB vs 3GB
- ✅ **Optional SQL Agent**: Disable to save 500MB RAM
- ✅ **Faster updates**: Rebuild only changed service
- ✅ **Independent scaling**: Scale services separately
- ✅ **Easy rollback**: Keep original setup intact
