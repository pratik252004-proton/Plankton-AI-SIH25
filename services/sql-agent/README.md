# SQL Agent Service

FastAPI-based microservice for natural language database queries.

## Features

- Natural language to SQL conversion using LangChain + Groq
- Multi-database routing (detection_db.db and data.db)
- REST API endpoints for easy integration
- Lightweight container (~500MB)

## API Endpoints

### `POST /query`
Execute a natural language query
```json
{
  "question": "How many detections were made today?"
}
```

### `GET /schema`
Get database schema information

### `GET /examples`
Get example questions

### `GET /sample-data?db_choice=detection&limit=5`
Get sample data from database

### `GET /health`
Health check endpoint

## Environment Variables

- `GROQ_API_KEY` - Required. Your Groq API key

## Running Standalone

```bash
# Build
docker build -t plankton-sql-agent .

# Run
docker run -p 8002:8002 \
  -e GROQ_API_KEY=your_key_here \
  -v ./database:/app/database \
  plankton-sql-agent
```

## Testing

```bash
# Health check
curl http://localhost:8002/health

# Query
curl -X POST http://localhost:8002/query \
  -H "Content-Type: application/json" \
  -d '{"question": "How many detections?"}'
```
