# Docker Quick Reference for Plankton Detection App

## Image Variants

Two Docker image variants are available:

| Variant | Size | Features | Use Case |
|---------|------|----------|----------|
| **Minimal** (recommended) | ~2.5GB | All core detection features | Raspberry Pi deployment |
| **Full** | ~3.5-4GB | All features + SQL chat | Development/powerful servers |

**Model:** MobileNetV3-Small - optimized for ARM64 (Raspberry Pi compatible) ✅

## Quick Commands

### Build and Run

**On Raspberry Pi:**
```bash
# Use the build script (recommended) - will prompt for variant
chmod +x build-docker.sh
./build-docker.sh

# Or build manually (minimal variant)
docker build -f Dockerfile.minimal -t plankton-app:minimal .

# Or build manually (full variant)
docker build -f Dockerfile -t plankton-app:full .

# Run with Docker Compose (uses minimal by default)
docker-compose up -d

# Or specify full variant
DOCKERFILE=Dockerfile docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

**On Windows (cross-compile for Raspberry Pi):**
```powershell
# Use the build script (recommended) - will prompt for variant
.\build-docker.ps1

# Or build manually with buildx (minimal)
docker buildx build --platform linux/arm64 -f Dockerfile.minimal -t plankton-app:minimal --load .

# Or build manually with buildx (full)
docker buildx build --platform linux/arm64 -f Dockerfile -t plankton-app:full --load .
```

### Management
```bash
# Restart after code changes
docker-compose restart

# Check status
docker-compose ps

# View resource usage
docker stats plankton-detection

# Execute command in container
docker exec -it plankton-detection bash
```

### Troubleshooting
```bash
# View logs
docker-compose logs --tail=50

# Check health
docker inspect plankton-detection | grep Health

# Clean up space
docker system prune -a
```

## File Structure

```
d:\Plankton\
├── Dockerfile              # Container definition
├── docker-compose.yml      # Orchestration config
├── .dockerignore          # Files to exclude
├── requirements.txt       # Python dependencies
├── app/
│   └── streamlit_app.py
├── src/
├── checkpoints/           # Mounted as volume
├── database/              # Mounted as volume
└── uploads/               # Mounted as volume
```

## Access Application

After running `docker-compose up -d`:
- **Local**: http://localhost:8501
- **Network**: http://192.168.1.XXX:8501

## Update Application

```bash
# 1. Update code files
# 2. Rebuild
docker-compose build
# 3. Restart
docker-compose up -d
```

## Troubleshooting

If you encounter build errors, see the comprehensive troubleshooting guide:
- Common errors and solutions
- Memory optimization for Raspberry Pi
- Cross-compilation instructions
- Performance tuning tips

## Raspberry Pi Compatibility

✅ **Fully compatible** with Raspberry Pi 4 (2GB+ RAM recommended)
- **Model:** MobileNetV3-Small (optimized for ARM64)
- **Image size:** 2.5GB (minimal) or 3.5GB (full)
- **Memory usage:** ~1-2GB during inference
- **Performance:** Real-time detection on Pi 4

**Recommended:** Use minimal variant for best performance on Raspberry Pi.
