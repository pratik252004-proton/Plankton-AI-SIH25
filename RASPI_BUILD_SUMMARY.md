# Raspberry Pi Docker Build Summary - 2-Container Architecture

## What Was Created

### 1. Build Script for Windows
**File**: `build-raspi-docker.ps1`
- Builds **2 separate ARM64 images** on Windows using Docker Buildx
- **Container 1**: Main App (Streamlit + ML/CV Processing)
- **Container 2**: SQL Agent Service (FastAPI + LangChain)
- Supports flexible build modes:
  - Both containers (recommended)
  - Main app only (without SQL chat)
  - SQL agent only (for updates)
- Supports both minimal and full variants for main app
- Automatically saves images to `.tar` files for transfer
- Interactive prompts for easy use

### 2. Deployment Guide
**File**: `RASPBERRY_PI_DEPLOYMENT.md`
- Complete step-by-step deployment instructions
- Prerequisites and system requirements
- Multiple transfer methods (SCP, USB, direct build)
- Docker installation on Raspberry Pi
- Configuration and management commands
- Troubleshooting section
- Performance optimization tips
- Security recommendations

### 3. Quick Start Guide
**File**: `RASPI_QUICK_START.md`
- Condensed command reference
- Essential commands only
- Quick troubleshooting
- Perfect for experienced users

## How It Works

### Multi-Platform Build Process

1. **Docker Buildx** creates ARM64 images on x86_64 Windows machines
2. Image is saved to a `.tar` file (~2.5-4GB depending on variant)
3. Transfer file to Raspberry Pi via SCP, USB, or network
4. Load and run on Raspberry Pi

### Image Variants

#### Minimal (Recommended for Raspberry Pi)
- **Size**: ~2.5GB
- **Features**: 
  - ✅ Image detection and analysis
  - ✅ Batch processing
  - ✅ Human verification workflow
  - ✅ Database logging
  - ✅ Location tracking
  - ❌ SQL chat (LangChain/Groq)
- **Best for**: Production deployment on Raspberry Pi

#### Full
- **Size**: ~3.5-4GB
- **Features**: Everything including SQL chat
- **Requires**: Groq API key
- **Best for**: Development or high-spec Raspberry Pi 5

## Usage

### Quick Start

```powershell
# On Windows
.\build-raspi-docker.ps1

# Transfer to Raspberry Pi
scp plankton-raspi.tar pi@<ip>:~/

# On Raspberry Pi
docker load -i plankton-raspi.tar
docker run -d --name plankton-detection -p 8501:8501 \
  -v ~/plankton-app/checkpoints:/app/checkpoints \
  plankton-app:minimal-arm64
```

### Access
Open browser: `http://<raspberry-pi-ip>:8501`

## System Requirements

### Raspberry Pi
- **Model**: Raspberry Pi 4 (4GB+ RAM) or Raspberry Pi 5
- **OS**: Raspberry Pi OS 64-bit or Ubuntu Server 22.04 ARM64
- **Storage**: 16GB+ SD card (32GB+ recommended)
- **Network**: WiFi or Ethernet

### Development Machine (Windows)
- Docker Desktop with Buildx
- ~5GB free disk space
- Good internet connection (for first build)

## Build Time Estimates

- **On Windows (cross-compile)**: 20-40 minutes
- **On Raspberry Pi 4 (direct build)**: 1-2 hours
- **Transfer via SCP**: 5-15 minutes (depends on network)

## Files Modified/Created

```
d:\Plankton\
├── build-raspi-docker.ps1          # NEW: ARM64 build script
├── RASPBERRY_PI_DEPLOYMENT.md      # NEW: Full deployment guide
├── RASPI_QUICK_START.md           # NEW: Quick reference
├── Dockerfile                      # Existing: Full variant
├── Dockerfile.minimal              # Existing: Minimal variant
├── requirements-docker.txt         # Existing: Full dependencies
└── requirements-minimal.txt        # Existing: Minimal dependencies
```

## Next Steps

1. **Build the image**:
   ```powershell
   .\build-raspi-docker.ps1
   ```

2. **Test locally** (optional):
   ```powershell
   docker run -p 8501:8501 plankton-app:minimal-arm64
   ```
   Note: May not work on Windows if built for ARM64

3. **Transfer to Raspberry Pi** and deploy

4. **Monitor performance**:
   ```bash
   docker stats plankton-detection
   vcgencmd measure_temp
   ```

## Troubleshooting

### Build Fails
- Ensure Docker Desktop is running
- Check Docker Buildx: `docker buildx version`
- Try: `docker system prune -a`
- Allocate more resources to Docker Desktop

### Transfer Fails
- Check network connectivity: `ping <raspberry-pi-ip>`
- Verify SSH access: `ssh pi@<raspberry-pi-ip>`
- Try USB transfer method instead

### Container Won't Start on Raspberry Pi
- Check logs: `docker logs plankton-detection`
- Verify model file exists in checkpoints directory
- Check memory: `free -h`
- Ensure ARM64 OS is installed: `uname -m` (should show `aarch64`)

## Performance Tips

1. Use **minimal variant** for better performance
2. Use **SSD instead of SD card** for storage
3. Ensure good **cooling** (heatsink + fan)
4. **Disable desktop environment** if running headless
5. **Monitor temperature**: Keep below 80°C

## Support

- **Documentation**: See `RASPBERRY_PI_DEPLOYMENT.md`
- **Quick Reference**: See `RASPI_QUICK_START.md`
- **GitHub**: https://github.com/samarth49/SIH2025
- **Issues**: Check Docker logs and system resources

---

**Created**: 2025-12-10
**Last Updated**: 2025-12-10
