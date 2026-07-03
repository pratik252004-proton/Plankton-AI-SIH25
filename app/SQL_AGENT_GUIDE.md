# SQL Agent - Quick Start Guide

## 🚀 Getting Started

### 1. Get Groq API Key (Free!)

1. Visit https://console.groq.com/keys
2. Sign up for a free account
3. Click "Create API Key"
4. Copy your key (starts with `gsk_...`)

### 2. Run Streamlit App

```bash
cd d:\Plankton
venv\Scripts\activate
cd app
streamlit run streamlit_app.py
```

### 3. Use the Chat Tab

1. Click on **"💬 Chat with Database"** tab
2. Paste your Groq API key
3. Wait for "✅ SQL Agent ready!"
4. Start asking questions!

## 💡 Example Questions

- "How many species are in the database?"
- "What are the top 10 most common plankton species?"
- "Show me all species with more than 10,000 observations"
- "List species starting with 'A'"
- "Which species has the highest count?"

## 📊 Features

✅ Natural language to SQL conversion  
✅ Chat history  
✅ Example questions (clickable)  
✅ SQL query viewer  
✅ Database schema display  
✅ Error handling  

## 🎯 Database Info

**Table**: `counts`
- `Taxon` - Species name
- `Count` - Number of observations  
- `Type` - Classification type

Ready to chat with your plankton data! 🦐🔬
