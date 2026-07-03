# Multi-stage Dockerfile for Plankton Detection Streamlit App
# Optimized for Raspberry Pi (ARM64 architecture)

FROM python:3.11-slim-bookworm

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Build essentials
    build-essential \
    # Linear algebra libraries (for NumPy/PyTorch)
    libatlas-base-dev \
    libopenblas-dev \
    # Image processing libraries
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    # Video processing libraries
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libv4l-dev \
    # Video codecs
    libxvidcore-dev \
    libx264-dev \
    # FFmpeg for video processing
    ffmpeg \
    # GTK for OpenCV (if needed)
    libgtk-3-dev \
    # curl for healthcheck
    curl \
    # Cleanup
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements-docker.txt .

# Install Python dependencies
# Use CPU-only PyTorch for ARM architecture
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements-docker.txt

# Copy application code (required)
COPY app/ ./app/
COPY src/ ./src/

# Create directories that will be populated via volume mounts or at runtime
# checkpoints: model files (can be added via volume mount)
# database: SQLite database (created by app at runtime)
# uploads: temporary upload storage
RUN mkdir -p /app/checkpoints /app/database /app/uploads

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Run Streamlit app
CMD ["streamlit", "run", "app/streamlit_app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--browser.gatherUsageStats=false"]
