"""
SQL Agent FastAPI Service
Provides REST API endpoints for natural language database queries
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import os
import logging

# Import the SQL Agent
from sql_agent import create_plankton_agent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Plankton SQL Agent API",
    description="Natural language interface to plankton detection databases",
    version="1.0.0"
)

# Enable CORS for Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify Streamlit URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global agent instance (initialized on startup)
agent = None


# Request/Response models
class QueryRequest(BaseModel):
    question: str


class QueryResponse(BaseModel):
    success: bool
    answer: Optional[str] = None
    sql_query: Optional[str] = None
    database_used: Optional[str] = None
    error: Optional[str] = None


@app.on_event("startup")
async def startup_event():
    """Initialize SQL Agent on startup"""
    global agent
    
    # Get Groq API key from environment
    groq_api_key = os.getenv("GROQ_API_KEY")
    
    if not groq_api_key:
        logger.error("GROQ_API_KEY environment variable not set!")
        raise RuntimeError("GROQ_API_KEY is required")
    
    try:
        logger.info("Initializing SQL Agent...")
        agent = create_plankton_agent(groq_api_key=groq_api_key)
        logger.info("SQL Agent initialized successfully!")
    except Exception as e:
        logger.error(f"Failed to initialize SQL Agent: {e}")
        raise


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Plankton SQL Agent API",
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    if agent is None:
        raise HTTPException(status_code=503, detail="SQL Agent not initialized")
    
    return {
        "status": "healthy",
        "agent_initialized": agent is not None
    }


@app.post("/query", response_model=QueryResponse)
async def query_database(request: QueryRequest):
    """
    Execute a natural language query against the database
    
    Args:
        request: QueryRequest with the natural language question
        
    Returns:
        QueryResponse with answer, SQL query, and metadata
    """
    if agent is None:
        raise HTTPException(status_code=503, detail="SQL Agent not initialized")
    
    try:
        logger.info(f"Processing query: {request.question}")
        result = agent.query(request.question)
        logger.info(f"Query completed: success={result.get('success')}")
        
        return QueryResponse(**result)
    
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        return QueryResponse(
            success=False,
            error=str(e)
        )


@app.get("/schema")
async def get_schema():
    """Get database schema information"""
    if agent is None:
        raise HTTPException(status_code=503, detail="SQL Agent not initialized")
    
    try:
        schema_info = agent.get_schema_info()
        return {
            "success": True,
            "schemas": schema_info
        }
    except Exception as e:
        logger.error(f"Error getting schema: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/examples")
async def get_example_questions():
    """Get example questions for the database"""
    if agent is None:
        raise HTTPException(status_code=503, detail="SQL Agent not initialized")
    
    try:
        examples = agent.get_example_questions()
        return {
            "success": True,
            "examples": examples
        }
    except Exception as e:
        logger.error(f"Error getting examples: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sample-data")
async def get_sample_data(db_choice: str = "detection", limit: int = 5):
    """
    Get sample data from specified database
    
    Args:
        db_choice: 'detection' or 'data'
        limit: Number of rows to return
    """
    if agent is None:
        raise HTTPException(status_code=503, detail="SQL Agent not initialized")
    
    try:
        sample_data = agent.get_sample_data(db_choice=db_choice, limit=limit)
        return {
            "success": True,
            "data": sample_data,
            "database": db_choice
        }
    except Exception as e:
        logger.error(f"Error getting sample data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    
    # Run the server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8002,
        log_level="info"
    )
