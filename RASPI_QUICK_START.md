# 🚀 Quick Start: Raspberry Pi Docker Deployment (2-Container)

## Architecture
- **Container 1**: Main App (Streamlit + ML/CV Processing)
- **Container 2**: SQL Agent Service (FastAPI + LangChain)

## On Windows PC (Build Images)

```powershell
# 1. Build both ARM64 images
.\build-raspi-docker.ps1
# Select: 1) Both containers
# Select: 1) Minimal variant

# 2. Images are saved automatically:
#    - plankton-app-minimal-raspi.tar (~2.5GB)
#    - plankton-sql-agent-raspi.tar (~300MB)

# 3. Transfer to Raspberry Pi
scp plankton-app-minimal-raspi.tar plankton-sql-agent-raspi.tar pi@<raspberry-pi-ip>:~/
scp docker-compose-2container.yml pi@<raspberry-pi-ip>:~/plankton/
```

## On Raspberry Pi (Deploy)

```bash
# 1. Install Docker (if needed)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
sudo apt install docker-compose -y
newgrp docker

# 2. Load both images
docker load -i plankton-app-minimal-raspi.tar
docker load -i plankton-sql-agent-raspi.tar

# 3. Setup project directory
mkdir -p ~/plankton/{checkpoints,database,uploads}
cd ~/plankton

# 4. Copy your model file
# scp your-model.pt pi@<raspberry-pi-ip>:~/plankton/checkpoints/

# 5. Create .env file for SQL Agent
echo "GROQ_API_KEY=your_groq_api_key_here" > .env

# 6. Run both containers
docker-compose -f docker-compose-2container.yml up -d

# 7. Check status
docker-compose -f docker-compose-2container.yml ps
docker-compose -f docker-compose-2container.yml logs -f

# 8. Access app
# Open browser: http://<raspberry-pi-ip>:8501
```

## Single Container Deployment (Without SQL Chat)

If you only want the main app without SQL chat:

```bash
# Build only main app
.\build-raspi-docker.ps1  # Select: 2) Main App only

# On Raspberry Pi
docker load -i plankton-app-minimal-raspi.tar
docker run -d \
  --name plankton-detection \
  -p 8501:8501 \
  -v ~/plankton/checkpoints:/app/checkpoints \
  -v ~/plankton/database:/app/database \
  -v ~/plankton/uploads:/app/uploads \
  --restart unless-stopped \
  plankton-app:minimal-arm64
```

## Common Commands

```bash
# View logs (both containers)
docker-compose -f docker-compose-2container.yml logs -f

# View logs (specific container)
docker logs -f plankton-detection
docker logs -f plankton-sql-agent

# Stop/Start/Restart all
docker-compose -f docker-compose-2container.yml stop
docker-compose -f docker-compose-2container.yml start
docker-compose -f docker-compose-2container.yml restart

# Stop/Start individual container
docker stop plankton-detection
docker start plankton-sql-agent

# Check resource usage
docker stats

# Backup database
cp ~/plankton/database/detection_db.db ~/backup_$(date +%Y%m%d).db

# Update to new version
docker-compose -f docker-compose-2container.yml down
docker load -i new-image.tar
docker-compose -f docker-compose-2container.yml up -d
```

## Troubleshooting

```bash
# Container won't start
docker-compose -f docker-compose-2container.yml logs

# Check memory
free -h
docker stats

# Check temperature
vcgencmd measure_temp

# Restart Docker
sudo systemctl restart docker

# Check network connectivity between containers
docker network inspect plankton_plankton-network

# Test SQL Agent health
curl http://localhost:8002/health
```

## File Transfer Methods

**SCP (Recommended):**
```powershell
# Transfer both images
scp plankton-app-minimal-raspi.tar plankton-sql-agent-raspi.tar pi@192.168.1.100:~/

# Transfer docker-compose file
scp docker-compose-2container.yml pi@192.168.1.100:~/plankton/
```

**USB Drive:**
```bash
sudo mount /dev/sda1 /mnt
cp /mnt/*.tar ~/
sudo umount /mnt
```

## Resource Usage (Raspberry Pi 4)

| Container | Memory | CPU | Notes |
|-----------|--------|-----|-------|
| Main App | ~1.5-2GB | 20-40% | During inference |
| SQL Agent | ~200-300MB | 5-10% | Idle/query |
| **Total** | **~2-2.5GB** | **25-50%** | Both running |

**Recommendation**: Raspberry Pi 4 with 4GB+ RAM

---

📖 **Full Guide**: See `RASPBERRY_PI_DEPLOYMENT.md` for detailed instructions
