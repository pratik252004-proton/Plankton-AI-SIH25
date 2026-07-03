"""
Test SQL Agent - Diagnostic Script
Run this to identify SQL agent issues
"""

import sys
from pathlib import Path

# Add app directory to path
sys.path.append(str(Path(__file__).parent / 'app'))

print("=" * 60)
print("SQL AGENT DIAGNOSTIC TEST")
print("=" * 60)

# Step 1: Check imports
print("\n[1/5] Checking imports...")
try:
    from sql_agent import create_plankton_agent
    print("✅ sql_agent module imported successfully")
except ImportError as e:
    print(f"❌ Failed to import sql_agent: {e}")
    sys.exit(1)

try:
    from langchain_groq import ChatGroq
    print("✅ langchain_groq imported successfully")
except ImportError as e:
    print(f"❌ Failed to import langchain_groq: {e}")
    print("\nInstall with: pip install langchain-groq")
    sys.exit(1)

try:
    from langchain_community.utilities import SQLDatabase
    print("✅ langchain_community imported successfully")
except ImportError as e:
    print(f"❌ Failed to import langchain_community: {e}")
    print("\nInstall with: pip install langchain-community")
    sys.exit(1)

# Step 2: Check database files
print("\n[2/5] Checking database files...")
import os

db_dir = Path(__file__).parent / "database"
detection_db = db_dir / "detection_db.db"
data_db = db_dir / "data.db"

if detection_db.exists():
    print(f"✅ detection_db.db exists ({detection_db.stat().st_size} bytes)")
else:
    print(f"❌ detection_db.db NOT found at {detection_db}")

if data_db.exists():
    print(f"✅ data.db exists ({data_db.stat().st_size} bytes)")
else:
    print(f"❌ data.db NOT found at {data_db}")

# Step 3: Test database connection
print("\n[3/5] Testing database connection...")
try:
    import sqlite3
    conn = sqlite3.connect(str(detection_db))
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM detections")
    count = cursor.fetchone()[0]
    print(f"✅ Connected to detection_db.db ({count} detections)")
    conn.close()
except Exception as e:
    print(f"❌ Database connection failed: {e}")

# Step 4: Create SQL agent
print("\n[4/5] Creating SQL agent...")
GROQ_API_KEY = "YOUR_GROQ_API_KEY_HERE"

try:
    agent = create_plankton_agent(groq_api_key=GROQ_API_KEY)
    print("✅ SQL agent created successfully!")
except Exception as e:
    print(f"❌ Failed to create agent: {e}")
    import traceback
    print("\nFull error:")
    traceback.print_exc()
    sys.exit(1)

# Step 5: Test query
print("\n[5/5] Testing query...")
try:
    result = agent.query("How many detections are in the database?")
    
    print(f"\n{'='*60}")
    print("QUERY RESULT:")
    print(f"{'='*60}")
    print(f"Success: {result['success']}")
    print(f"Answer: {result['answer']}")
    print(f"Database: {result['database_used']}")
    if result.get('sql_query'):
        print(f"SQL: {result['sql_query']}")
    if result.get('error'):
        print(f"Error: {result['error']}")
    print(f"{'='*60}")
    
    if result['success']:
        print("\n✅ ALL TESTS PASSED! SQL agent is working correctly.")
    else:
        print(f"\n❌ Query failed: {result.get('error')}")
        
except Exception as e:
    print(f"❌ Query failed: {e}")
    import traceback
    print("\nFull error:")
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*60)
print("DIAGNOSTIC COMPLETE")
print("="*60)
