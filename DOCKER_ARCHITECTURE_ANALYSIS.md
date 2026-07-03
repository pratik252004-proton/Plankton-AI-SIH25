# Docker Multi-Container Architecture Analysis

## Current Application Structure

### Overview
Your Plankton Detection System is a comprehensive Streamlit application with **4 main features**:

1. **📸 Image Classification** - Single/multiple image analysis with verification
2. **📊 Batch Processing** - Offline collection batch analysis with verification
3. **🎥 Video Analysis** - Frame-by-frame video processing with annotated output
4. **💬 SQL Agentic AI** - Natural language database queries using LangChain + Groq

### Current Monolithic Structure

```
d:\Plankton/
├── app/
│   ├── streamlit_app.py (72KB - main UI, all 4 features)
│   ├── sql_agent.py (13KB - LangChain SQL agent)
│   ├── detection_logger.py (4KB - database logging)
│   └── location_helper.py (2KB - location utilities)
├── src/
│   ├── model.py (ML model loading)
│   ├── video_processor.py (video frame extraction)
│   ├── video_annotator.py (video annotation with bounding boxes)
│   ├── plankton_utils.py (visualizations, exports)
│   └── data_loader.py (dataset utilities)
├── checkpoints/ (YOLO/MobileNet models)
├── database/ (SQLite databases)
└── Dockerfile (single monolithic image)
```

### Dependency Analysis

#### Heavy Dependencies (Large Docker Image Size)

| Component | Dependencies | Size Impact |
|-----------|-------------|-------------|
| **Image Classification** | PyTorch, TorchVision, PIL, NumPy | ~2GB |
| **Video Processing** | OpenCV, FFmpeg, video codecs | ~500MB |
| **Batch Processing** | Same as Image (PyTorch, etc.) | Shared |
| **SQL Agent** | LangChain, LangGraph, Groq SDK | ~200MB |

**Current Total Image Size**: ~3-4GB (estimated)

---

## Recommended Multi-Container Architecture

### Strategy: Microservices with API Gateway

Split into **4 separate Docker images**:

```
┌─────────────────────────────────────────────────────────┐
│                    STREAMLIT UI                         │
│              (Lightweight Frontend Only)                │
│                     ~200-300MB                          │
└─────────────────────────────────────────────────────────┘
                           │
                           │ HTTP/REST
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   IMAGE      │  │    VIDEO     │  │   AGENTIC    │
│ PROCESSING   │  │  PROCESSING  │  │   AI AGENT   │
│   SERVICE    │  │   SERVICE    │  │   SERVICE    │
│              │  │              │  │              │
│ PyTorch      │  │ OpenCV       │  │ LangChain    │
│ YOLO Model   │  │ FFmpeg       │  │ Groq LLM     │
│ ~2GB         │  │ ~1.5GB       │  │ ~500MB       │
└──────────────┘  └──────────────┘  └──────────────┘
```

### Service Breakdown

#### 1. **Streamlit UI Service** (Frontend)
- **Purpose**: User interface only, routes requests to backend services
- **Size**: ~200-300MB
- **Dependencies**: 
  - `streamlit`
  - `requests` (for API calls)
  - `pandas` (for display)
  - `plotly` (for visualizations)
- **Responsibilities**:
  - File uploads
  - Display results
  - User verification workflow
  - Route requests to appropriate services

#### 2. **Image Processing Service** (ML Backend)
- **Purpose**: Single image and batch image classification
- **Size**: ~2GB
- **Dependencies**:
  - `torch`, `torchvision`
  - `PIL`, `numpy`
  - YOLO/MobileNet models
- **API Endpoints**:
  - `POST /predict` - Single image prediction
  - `POST /batch_predict` - Batch image predictions
- **Responsibilities**:
  - Load ML models
  - Image preprocessing
  - Inference
  - Return predictions with confidence scores

#### 3. **Video Processing Service** (Video Backend)
- **Purpose**: Video frame extraction, analysis, and annotation
- **Size**: ~1.5GB
- **Dependencies**:
  - `opencv-python`
  - `ffmpeg` (system package)
  - Video codecs
  - PyTorch (for predictions)
  - YOLO models
- **API Endpoints**:
  - `POST /analyze_video` - Process video frames
  - `POST /annotate_video` - Create annotated video
- **Responsibilities**:
  - Video frame extraction
  - Frame-by-frame prediction
  - Annotated video generation
  - Return detection timeline

#### 4. **Agentic AI Service** (SQL Agent Backend)
- **Purpose**: Natural language to SQL query processing
- **Size**: ~500MB
- **Dependencies**:
  - `langchain`, `langchain-community`, `langchain-groq`
  - `langgraph`
  - SQLite
- **API Endpoints**:
  - `POST /query` - Natural language query
  - `GET /schema` - Database schema info
  - `GET /examples` - Example questions
- **Responsibilities**:
  - Route queries to correct database
  - Generate SQL from natural language
  - Execute queries
  - Return formatted results

---

## Implementation Details

### Directory Structure

```
plankton/
├── docker-compose.yml
├── .env
├── services/
│   ├── streamlit-ui/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── app.py (simplified UI)
│   │   └── api_client.py (REST client)
│   │
│   ├── image-service/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── main.py (FastAPI server)
│   │   ├── model.py
│   │   └── inference.py
│   │
│   ├── video-service/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── main.py (FastAPI server)
│   │   ├── video_processor.py
│   │   └── video_annotator.py
│   │
│   └── agent-service/
│       ├── Dockerfile
│       ├── requirements.txt
│       ├── main.py (FastAPI server)
│       └── sql_agent.py
│
├── shared/
│   ├── models/ (volume mount - shared YOLO models)
│   └── database/ (volume mount - shared SQLite DBs)
│
└── nginx/ (optional - API gateway)
    └── nginx.conf
```

### Docker Compose Configuration

```yaml
version: '3.8'

services:
  # Streamlit UI (Frontend)
  streamlit-ui:
    build: ./services/streamlit-ui
    ports:
      - "8501:8501"
    environment:
      - IMAGE_SERVICE_URL=http://image-service:8000
      - VIDEO_SERVICE_URL=http://video-service:8001
      - AGENT_SERVICE_URL=http://agent-service:8002
    depends_on:
      - image-service
      - video-service
      - agent-service
    networks:
      - plankton-network

  # Image Processing Service
  image-service:
    build: ./services/image-service
    ports:
      - "8000:8000"
    volumes:
      - ./shared/models:/app/models:ro
    deploy:
      resources:
        limits:
          memory: 2G
    networks:
      - plankton-network

  # Video Processing Service
  video-service:
    build: ./services/video-service
    ports:
      - "8001:8001"
    volumes:
      - ./shared/models:/app/models:ro
    deploy:
      resources:
        limits:
          memory: 2G
    networks:
      - plankton-network

  # Agentic AI Service
  agent-service:
    build: ./services/agent-service
    ports:
      - "8002:8002"
    volumes:
      - ./shared/database:/app/database
    environment:
      - GROQ_API_KEY=${GROQ_API_KEY}
    deploy:
      resources:
        limits:
          memory: 1G
    networks:
      - plankton-network

networks:
  plankton-network:
    driver: bridge
```

---

## Benefits of Multi-Container Architecture

### ✅ Advantages

1. **Smaller Individual Images**
   - Streamlit UI: ~300MB (vs 3-4GB monolithic)
   - Only download/update what changed
   - Faster CI/CD pipelines

2. **Independent Scaling**
   - Scale video processing separately (more CPU/GPU)
   - Scale SQL agent independently
   - Resource optimization per service

3. **Faster Development**
   - Update UI without rebuilding ML models
   - Test video processing in isolation
   - Parallel development by team members

4. **Better Resource Management**
   - Assign GPU only to ML services
   - Limit memory per service
   - Prevent one service from crashing others

5. **Technology Flexibility**
   - Use different Python versions per service
   - Upgrade dependencies independently
   - Mix languages (e.g., Go for video processing)

6. **Easier Debugging**
   - Isolate issues to specific services
   - View logs per service
   - Test services independently

### ⚠️ Challenges

1. **Network Latency**
   - Inter-service communication overhead
   - Mitigated by Docker networking (same host)

2. **Complexity**
   - More containers to manage
   - Orchestration with docker-compose
   - Service discovery

3. **Development Setup**
   - Need to run multiple services locally
   - More complex debugging

---

## Alternative: Simplified 3-Container Setup

If 4 containers is too complex, consider combining image + batch processing:

```
1. Streamlit UI (Frontend)
2. ML Processing Service (Image + Batch + Video)
3. Agentic AI Service (SQL Agent)
```

**Rationale**: Image and batch processing share the same YOLO model, so combining them reduces duplication.

---

## Communication Strategy

### REST API (Recommended)

Use **FastAPI** for backend services:

```python
# services/image-service/main.py
from fastapi import FastAPI, File, UploadFile
from PIL import Image
import io

app = FastAPI()

@app.post("/predict")
async def predict_image(file: UploadFile = File(...)):
    image = Image.open(io.BytesIO(await file.read()))
    prediction, confidence = model.predict(image)
    return {
        "species": prediction,
        "confidence": float(confidence)
    }

@app.post("/batch_predict")
async def batch_predict(files: list[UploadFile] = File(...)):
    results = []
    for file in files:
        image = Image.open(io.BytesIO(await file.read()))
        prediction, confidence = model.predict(image)
        results.append({
            "filename": file.filename,
            "species": prediction,
            "confidence": float(confidence)
        })
    return {"results": results}
```

### Async Job Queue (Optional)

For long-running tasks (video processing), use **Redis + Celery**:

```python
# Submit video processing job
job_id = requests.post("/video/analyze", files={"video": video_file})

# Poll for results
status = requests.get(f"/video/status/{job_id}")
```

---

## Deployment Considerations

### Raspberry Pi Deployment

**Challenge**: Limited resources on Raspberry Pi

**Solutions**:
1. **Deploy only UI on Pi** - Backend services on cloud/server
2. **Use ARM64 images** - Ensure all base images support ARM
3. **Resource limits** - Set memory limits per service
4. **Model optimization** - Use quantized models (INT8)

### GPU Support

If you have GPU available:

```yaml
video-service:
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
```

---

## Migration Path

### Phase 1: Preparation (Week 1)
1. ✅ Analyze current structure (DONE)
2. Create API contracts (OpenAPI specs)
3. Set up project structure

### Phase 2: Backend Services (Week 2-3)
1. Build Image Processing Service (FastAPI)
2. Build Video Processing Service (FastAPI)
3. Build Agentic AI Service (FastAPI)
4. Test services independently

### Phase 3: Frontend Migration (Week 4)
1. Refactor Streamlit UI to call APIs
2. Update verification workflow
3. Test end-to-end

### Phase 4: Deployment (Week 5)
1. Create docker-compose.yml
2. Build and test all containers
3. Deploy to target environment
4. Monitor and optimize

---

## Next Steps

### Option A: Full Microservices (4 Containers)
**Best for**: Production deployment, team development, scalability

### Option B: Simplified (3 Containers)
**Best for**: Smaller teams, faster implementation, moderate scale

### Option C: Hybrid (2 Containers)
**Best for**: Raspberry Pi deployment, resource constraints
- Container 1: Streamlit UI + Image/Batch processing
- Container 2: Video processing (optional, on-demand)
- Container 3: SQL Agent (optional, on-demand)

---

## Recommendation

Based on your requirements:

1. **Start with 3-container setup**:
   - Streamlit UI
   - ML Processing (Image + Video)
   - Agentic AI

2. **Later split to 4 containers** if needed:
   - Separate video processing when scaling

3. **Use FastAPI** for backend services (fast, modern, async)

4. **Share models via volumes** to avoid duplication

5. **Deploy UI on Raspberry Pi**, backends on cloud/server if resources limited

---

## Questions to Decide Architecture

1. **Where will you deploy?**
   - All on Raspberry Pi? → 2-3 containers
   - Pi + Cloud? → 4 containers (UI on Pi, backends on cloud)
   - All on server? → 4 containers (full microservices)

2. **Do you need GPU?**
   - Yes → Separate ML services for GPU allocation
   - No → Can combine services

3. **Team size?**
   - Solo → 2-3 containers (simpler)
   - Team → 4 containers (parallel development)

4. **Expected load?**
   - Low (research) → 2-3 containers
   - High (production) → 4 containers with scaling

Let me know your answers and I can create the specific implementation!
