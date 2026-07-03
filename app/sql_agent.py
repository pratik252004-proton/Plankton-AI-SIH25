"""
Multi-Database SQL Agent for Plankton Analysis
Intelligently routes queries between data.db and detection_db.db
"""

import os
import sqlite3
from typing import Dict, List, Any, Optional
from pathlib import Path

from langchain_groq import ChatGroq
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent


class MultiDatabaseSQLAgent:
    """Intelligent SQL agent that routes queries to appropriate database"""
    
    def __init__(self, groq_api_key: str):
        """
        Initialize the multi-database SQL agent
        
        Args:
            groq_api_key: Groq API key
        """
        # Set API key
        os.environ["GROQ_API_KEY"] = groq_api_key
        
        # Initialize Groq LLM
        # Using llama3-70b-8192 for better ReAct agent compatibility
        self.llm = ChatGroq(
            model="qwen/qwen3-32b",
            temperature=0,
            max_tokens=None,
            timeout=None,
            max_retries=2,
        )
        
        # Database paths
        base_path = Path(__file__).parent.parent / "database"
        self.data_db_path = str(base_path / "data.db")
        self.detection_db_path = str(base_path / "detection_db.db")
        
        # Initialize both databases
        self.data_db = SQLDatabase.from_uri(f"sqlite:///{self.data_db_path}")
        self.detection_db = SQLDatabase.from_uri(f"sqlite:///{self.detection_db_path}")
        
        # Create agents for both databases
        self.data_agent = create_sql_agent(
            llm=self.llm,
            db=self.data_db,
            agent_type="zero-shot-react-description",
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=15,  # Increased from 5
            max_execution_time=60,  # Increased from 30
        )
        
        self.detection_agent = create_sql_agent(
            llm=self.llm,
            db=self.detection_db,
            agent_type="zero-shot-react-description",
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=15,  # Increased from 5
            max_execution_time=60,  # Increased from 30
        )
    
    def route_query(self, question: str) -> str:
        """
        Determine which database to query based on the question
        
        Args:
            question: User's natural language question
            
        Returns:
            'data' or 'detection'
        """
        question_lower = question.lower()
        
        # Keywords for detection database (live detection logs)
        detection_keywords = [
            'detection', 'detected', 'recent', 'today', 'yesterday', 'last week',
            'last month', 'date', 'time', 'timestamp', 'location', 'when',
            'logged', 'recorded', 'observed', 'found', 'confidence', 'image'
        ]
        
        # Keywords for data database (static species counts)
        data_keywords = [
            'total count', 'overall', 'all species', 'type', 'classification',
            'how many species', 'list all', 'complete list'
        ]
        
        # Check for detection keywords
        detection_score = sum(1 for keyword in detection_keywords if keyword in question_lower)
        data_score = sum(1 for keyword in data_keywords if keyword in question_lower)
        
        # If question mentions specific dates or time ranges, use detection DB
        if any(word in question_lower for word in ['from', 'between', 'since', 'until', 'after', 'before']):
            return 'detection'
        
        # If detection score is higher, use detection DB
        if detection_score > data_score:
            return 'detection'
        else:
            return 'data'
    
    def _execute_direct_query(self, question: str) -> Optional[Dict[str, Any]]:
        """
        Try to execute simple queries directly without agent
        Returns None if query is too complex for direct execution
        """
        question_lower = question.lower()
        
        # Simple count queries
        if "how many detections" in question_lower or "count" in question_lower:
            try:
                # Determine database
                db_choice = self.route_query(question)
                conn = sqlite3.connect(
                    self.detection_db_path if db_choice == 'detection' else self.data_db_path
                )
                cursor = conn.cursor()
                
                # Time-based filters
                if "today" in question_lower:
                    from datetime import datetime
                    today = datetime.now().strftime("%Y-%m-%d")
                    sql = f"SELECT COUNT(*) FROM detections WHERE DATE(detection_datetime) = '{today}'"
                elif "between" in question_lower and ("pm" in question_lower or "am" in question_lower):
                    # Handle "between 4 PM and 8 PM"
                    from datetime import datetime
                    today = datetime.now().strftime("%Y-%m-%d")
                    
                    # Extract hours (simplified)
                    if "4 pm" in question_lower and "8 pm" in question_lower:
                        sql = f"""
                        SELECT COUNT(*) FROM detections 
                        WHERE DATE(detection_datetime) = '{today}'
                        AND CAST(strftime('%H', detection_datetime) AS INTEGER) BETWEEN 16 AND 20
                        """
                    else:
                        return None  # Too complex
                elif "last week" in question_lower:
                    sql = """
                    SELECT COUNT(*) FROM detections 
                    WHERE detection_datetime >= datetime('now', '-7 days')
                    """
                elif "yesterday" in question_lower:
                    sql = """
                    SELECT COUNT(*) FROM detections 
                    WHERE DATE(detection_datetime) = DATE('now', '-1 day')
                    """
                else:
                    # General count
                    sql = "SELECT COUNT(*) FROM detections"
                
                cursor.execute(sql)
                count = cursor.fetchone()[0]
                conn.close()
                
                return {
                    "success": True,
                    "answer": f"There are {count} detections matching your criteria.",
                    "sql_query": sql,
                    "database_used": "Detection Database (detection_db.db)" if db_choice == 'detection' else "Species Data (data.db)",
                    "error": None
                }
            except Exception as e:
                return None  # Fall back to agent
        
        # List/show queries
        if ("show" in question_lower or "list" in question_lower) and "detection" in question_lower:
            try:
                conn = sqlite3.connect(self.detection_db_path)
                cursor = conn.cursor()
                
                # Time-based filters
                if "today" in question_lower:
                    from datetime import datetime
                    today = datetime.now().strftime("%Y-%m-%d")
                    sql = f"SELECT * FROM detections WHERE DATE(detection_datetime) = '{today}' LIMIT 100"
                elif "last week" in question_lower:
                    sql = "SELECT * FROM detections WHERE detection_datetime >= datetime('now', '-7 days') LIMIT 100"
                else:
                    sql = "SELECT * FROM detections ORDER BY created_at DESC LIMIT 50"
                
                cursor.execute(sql)
                results = cursor.fetchall()
                conn.close()
                
                # Format results
                if results:
                    answer = f"Found {len(results)} detections:\n\n"
                    for row in results[:10]:  # Show first 10
                        answer += f"- ID: {row[0]}, Species: {row[2]}, Confidence: {row[3]:.2%}, Time: {row[4]}\n"
                    if len(results) > 10:
                        answer += f"\n... and {len(results) - 10} more"
                else:
                    answer = "No detections found matching your criteria."
                
                return {
                    "success": True,
                    "answer": answer,
                    "sql_query": sql,
                    "database_used": "Detection Database (detection_db.db)",
                    "error": None
                }
            except Exception as e:
                return None  # Fall back to agent
        
        return None  # Query too complex, use agent
    
    def query(self, question: str) -> Dict[str, Any]:
        """
        Query the appropriate database using natural language
        
        Args:
            question: Natural language question
            
        Returns:
            Dict with 'answer', 'sql_query', 'database_used', and 'success' keys
        """
        try:
            # Try direct query first (faster, more reliable for simple queries)
            direct_result = self._execute_direct_query(question)
            if direct_result:
                return direct_result
            
            # Fall back to agent for complex queries
            db_choice = self.route_query(question)
            
            # Select appropriate agent
            if db_choice == 'detection':
                agent = self.detection_agent
                db_name = "Detection Database (detection_db.db)"
            else:
                agent = self.data_agent
                db_name = "Species Data (data.db)"
            
            # Run the agent
            result = agent.invoke({"input": question})
            
            # Extract and clean the output
            raw_output = result.get("output", "No answer generated")
            cleaned_output = self._clean_output(raw_output)
            
            return {
                "success": True,
                "answer": cleaned_output,
                "sql_query": self._extract_sql_from_result(result),
                "database_used": db_name,
                "error": None
            }
        except Exception as e:
            return {
                "success": False,
                "answer": None,
                "sql_query": None,
                "database_used": None,
                "error": str(e)
            }
    
    def _clean_output(self, output: str) -> str:
        """Clean LLM output by removing think tags and extra formatting"""
        import re
        
        # Remove <think>...</think> tags and their content
        output = re.sub(r'<think>.*?</think>', '', output, flags=re.DOTALL)
        
        # Remove any remaining HTML-like tags
        output = re.sub(r'<[^>]+>', '', output)
        
        # Clean up extra whitespace
        output = re.sub(r'\n\s*\n', '\n\n', output)
        output = output.strip()
        
        return output
    
    def _extract_sql_from_result(self, result: Dict) -> str:
        """Extract SQL query from agent result"""
        if "intermediate_steps" in result:
            for step in result["intermediate_steps"]:
                if isinstance(step, tuple) and len(step) > 0:
                    action = step[0]
                    if hasattr(action, "tool_input"):
                        return action.tool_input
        return "SQL query not available"
    
    def get_schema_info(self) -> Dict[str, str]:
        """Get schema information for both databases"""
        return {
            "data_db": self.data_db.get_table_info(),
            "detection_db": self.detection_db.get_table_info()
        }
    
    def get_sample_data(self, db_choice: str = "detection", limit: int = 5) -> List[tuple]:
        """Get sample data from specified database"""
        if db_choice == "detection":
            conn = sqlite3.connect(self.detection_db_path)
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM detections ORDER BY created_at DESC LIMIT {limit}")
        else:
            conn = sqlite3.connect(self.data_db_path)
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM counts LIMIT {limit}")
        
        data = cursor.fetchall()
        conn.close()
        return data
    
    def get_example_questions(self) -> List[str]:
        """Get example questions for both databases"""
        return [
            # Detection DB questions
            "How many detections were made today?",
            "Show me all detections from last week",
            "What species were detected between 2025-12-01 and 2025-12-08?",
            "How many times was Copepod detected?",
            "Show detections from Varanasi location",
            "What's the average confidence of recent detections?",
            # Data DB questions
            "How many species are in the database?",
            "What are the top 10 most common plankton species?",
            "List all species with more than 10,000 observations",
        ]


def create_plankton_agent(groq_api_key: str = None) -> MultiDatabaseSQLAgent:
    """
    Create a MultiDatabaseSQLAgent instance
    
    Args:
        groq_api_key: Groq API key
        
    Returns:
        MultiDatabaseSQLAgent instance
    """
    return MultiDatabaseSQLAgent(groq_api_key)
