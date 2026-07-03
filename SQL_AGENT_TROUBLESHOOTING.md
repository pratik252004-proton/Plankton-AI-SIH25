# SQL Agent Troubleshooting Guide

## Issue: SQL Chat Agent Not Working

### Quick Diagnostic Checklist

Run these checks in order:

#### 1. Check if LangChain is Installed

```powershell
pip list | Select-String "langchain"
```

**Expected output:**

```
langchain                 0.1.x
langchain-community       0.0.x
langchain-groq            0.0.x
```

**If missing, install:**

```powershell
pip install langchain langchain-groq langchain-community
```

#### 2. Verify API Key is Set

Check line 843 in `app/streamlit_app.py`:

```python
GROQ_API_KEY = ""
```

✅ **Your API key IS set** (not the placeholder value)

#### 3. Check Database Files Exist

```powershell
ls database\
```

**Expected:**

- `detection_db.db` ✅ (exists - 12 KB)
- `data.db` ✅ (exists - 8 KB)

#### 4. Test SQL Agent Manually

Create a test file `test_sql_agent.py`:

```python
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent / 'app'))

from sql_agent import create_plankton_agent

# Your API key
GROQ_API_KEY = ""

try:
    print("Creating SQL agent...")
    agent = create_plankton_agent(groq_api_key=GROQ_API_KEY)
    print("✅ Agent created successfully!")
  
    print("\nTesting query...")
    result = agent.query("How many detections are in the database?")
  
    print(f"\n✅ Success: {result['success']}")
    print(f"Answer: {result['answer']}")
    print(f"Database: {result['database_used']}")
  
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("\nInstall missing packages:")
    print("pip install langchain langchain-groq langchain-community")
  
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
```

Run it:

```powershell
python test_sql_agent.py
```

---

## Common Issues & Solutions

### Issue 1: ImportError - LangChain Not Found

**Error:**

```
ImportError: No module named 'langchain'
```

**Solution:**

```powershell
pip install langchain langchain-groq langchain-community
```

### Issue 2: API Key Invalid

**Error:**

```
Error: Invalid API key
```

**Solution:**

1. Get a new API key from https://console.groq.com/keys
2. Replace in `app/streamlit_app.py` line 843

### Issue 3: Database Not Found

**Error:**

```
Error: no such table: detections
```

**Solution:**
The database is created automatically when you make your first detection. Try:

1. Go to "Image Analysis" tab
2. Upload an image
3. Click "Analyze Images"
4. Then try SQL chat again

### Issue 4: Agent Initialization Fails

**Error:**

```
Error initializing SQL agent
```

**Solution:**
Check if both database files exist:

```powershell
# Should show both files
ls database\*.db
```

If missing, the app will create them on first use.

### Issue 5: "Feature Not Available" Message

**Symptom:**
You see: "SQL Chat feature not available"

**Cause:**
Running the **minimal Docker image** which excludes LangChain

**Solution:**
Either:

- **Option A:** Use the full Docker image
  ```bash
  docker build -f Dockerfile -t plankton-app:full .
  ```
- **Option B:** Install locally (not in Docker)
  ```powershell
  pip install langchain langchain-groq langchain-community
  streamlit run app/streamlit_app.py
  ```

---

## Verification Steps

### Step 1: Check Streamlit Logs

Look at the terminal where Streamlit is running for error messages.

### Step 2: Test Database Connection

```python
import sqlite3
conn = sqlite3.connect('database/detection_db.db')
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM detections")
print(f"Total detections: {cursor.fetchone()[0]}")
conn.close()
```

### Step 3: Test Groq API

```python
from langchain_groq import ChatGroq

llm = ChatGroq(
    model="qwen/qwen3-32b",
    api_key=""
)

response = llm.invoke("Hello, are you working?")
print(response.content)
```

---

## Current Status

Based on your setup:

✅ **API Key:** Set correctly
✅ **Database Files:** Exist
❓ **LangChain:** Need to verify installation

**Next Step:** Check if LangChain is installed by running:

```powershell
pip list | Select-String "langchain"
```

If not installed, run:

```powershell
pip install langchain==0.1.0 langchain-groq==0.0.1 langchain-community==0.0.20
```

Then restart Streamlit:

```powershell
# Stop current Streamlit (Ctrl+C)
streamlit run app/streamlit_app.py
```

---

## Quick Fix Commands

```powershell
# 1. Install dependencies
pip install langchain langchain-groq langchain-community

# 2. Restart Streamlit
# Press Ctrl+C to stop current instance
streamlit run app/streamlit_app.py

# 3. Test in browser
# Go to http://localhost:8501
# Click "Chat with Database" tab
# Try: "How many detections are there?"
```

---

## If Still Not Working

1. **Check Streamlit terminal for errors**
2. **Run the test script above** to isolate the issue
3. **Verify internet connection** (Groq API needs internet)
4. **Check firewall** (might block API calls)

Let me know what error message you see and I can help further!
