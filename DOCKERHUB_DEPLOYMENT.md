# 🚀 Docker Hub Deployment Guide (EASIEST METHOD)

## Why Docker Hub?

✅ **No file transfer** - Pull images directly from Docker Hub  
✅ **Faster deployment** - No need to transfer 3GB files  
✅ **Easy updates** - Just `docker pull` to get new versions  
✅ **Version control** - Tag and manage different versions  

---

## Prerequisites

### On Windows PC:
- Docker Desktop installed
- Docker Hub account (free): https://hub.docker.com/

### On Raspberry Pi:
- Docker installed
- Internet connection

---

## Step-by-Step Guide

### **PART 1: Build & Push (On Windows PC)**

#### Step 1: Get Docker Hub Account
1. Go to https://hub.docker.com/
2. Sign up for free (if you don't have an account)
3. Remember your username

#### Step 2: Run Build & Push Script
```powershell
cd d:\Plankton
.\build-and-push-dockerhub.ps1
```

#### Step 3: Answer Prompts
- **Docker Hub username**: Enter your username
- **Docker Hub password**: Enter when prompted for login
- **Build mode**: Choose `1` (Both containers)
- **Variant**: Choose `1` (Minimal)

#### Step 4: Wait for Build & Push
- **Time**: 30-50 minutes
- **What happens**: 
  - Builds ARM64 images
  - Pushes to Docker Hub automatically
  - No `.tar` files needed!

---

### **PART 2: Deploy (On Raspberry Pi)**

#### Step 1: Install Docker (if needed)
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
sudo apt install docker-compose -y
newgrp docker
```

#### Step 2: Setup Project Directory
```bash
mkdir -p ~/plankton/{checkpoints,database,uploads}
cd ~/plankton
```

#### Step 3: Copy Model File
```bash
# Transfer your model file
# From Windows: scp model.pt pi@<raspberry-pi-ip>:~/plankton/checkpoints/
```

#### Step 4: Create docker-compose.yml
```bash
nano docker-compose.yml
```

Paste this content (replace `YOUR_DOCKERHUB_USERNAME`):
```yaml
version: '3.8'

services:
  plankton-app:
    image: YOUR_DOCKERHUB_USERNAME/plankton-app:minimal-arm64
    container_name: plankton-detection
    restart: unless-stopped
    ports:
      - "8501:8501"
    volumes:
      - ./database:/app/database
      - ./uploads:/app/uploads
      - ./checkpoints:/app/checkpoints
    environment:
      - SQL_AGENT_URL=http://sql-agent:8002
    networks:
      - plankton-network

  sql-agent:
    image: YOUR_DOCKERHUB_USERNAME/plankton-sql-agent:arm64
    container_name: plankton-sql-agent
    restart: unless-stopped
    ports:
      - "8002:8002"
    volumes:
      - ./database:/app/database:ro
    environment:
      - GROQ_API_KEY=${GROQ_API_KEY}
    networks:
      - plankton-network

networks:
  plankton-network:
    driver: bridge
```

Save: `Ctrl+X`, `Y`, `Enter`

#### Step 5: Create .env File
```bash
nano .env
```

Add:
```
GROQ_API_KEY=your_groq_api_key_here
```

Save: `Ctrl+X`, `Y`, `Enter`

#### Step 6: Pull Images & Run
```bash
# Pull images from Docker Hub
docker-compose pull

# Start containers
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

#### Step 7: Access Application
Open browser: `http://<raspberry-pi-ip>:8501`

---

## 📊 Comparison: Docker Hub vs File Transfer

| Method | Transfer Time | Complexity | Updates |
|--------|---------------|------------|---------|
| **Docker Hub** | 5-10 min (pull) | Easy | `docker-compose pull` |
| **File Transfer** | 15-30 min (SCP) | Medium | Transfer new files |

---

## Common Commands

### Update to New Version
```bash
# On Raspberry Pi
cd ~/plankton
docker-compose pull
docker-compose up -d
```

### View Logs
```bash
docker-compose logs -f
```

### Restart
```bash
docker-compose restart
```

### Stop
```bash
docker-compose down
```

---

## Making Images Public vs Private

### Public (Free)
- Anyone can pull your images
- Good for open-source projects
- No authentication needed on Raspberry Pi

### Private (Free for 1 repository)
- Only you can pull
- Need to login on Raspberry Pi:
  ```bash
  docker login
  ```

---

## Troubleshooting

### Can't Pull Images
```bash
# Check internet connection
ping google.com

# Login to Docker Hub
docker login

# Try pulling manually
docker pull YOUR_USERNAME/plankton-app:minimal-arm64
```

### Images Too Large
- Use minimal variant
- Docker Hub free tier: unlimited public repos
- Each image is compressed during transfer

---

## Summary

**On Windows (Once):**
```powershell
.\build-and-push-dockerhub.ps1
```

**On Raspberry Pi (Anytime):**
```bash
docker-compose pull
docker-compose up -d
```

**That's it!** No file transfers, no USB drives, no SCP! 🎉

---

📖 **Full template**: See `docker-compose-dockerhub.yml`
