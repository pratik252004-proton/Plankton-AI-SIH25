# Raspberry Pi Deployment Guide

This guide will help you deploy the Plankton Detection System on a Raspberry Pi using Docker.

## Prerequisites

### Raspberry Pi Requirements
- **Model**: Raspberry Pi 4 (4GB+ RAM recommended) or Raspberry Pi 5
- **OS**: Raspberry Pi OS (64-bit) or Ubuntu Server 22.04 ARM64
- **Storage**: 16GB+ SD card (32GB+ recommended)
- **Network**: WiFi or Ethernet connection

### On Your Development Machine (Windows)
- Docker Desktop installed and running
- Docker Buildx enabled (included in recent Docker Desktop versions)

## Step 1: Build the ARM64 Docker Image

On your Windows machine, run the build script:

```powershell
.\build-raspi-docker.ps1
```

**What this does:**
1. Checks if Docker is running
2. Sets up Docker Buildx for multi-platform builds
3. Builds an ARM64 image compatible with Raspberry Pi
4. Optionally saves the image to a `.tar` file

**Choose the variant:**
- **Minimal** (recommended): ~2.5GB, includes all core features except SQL chat
- **Full**: ~3.5-4GB, includes all features including SQL chat (requires Groq API key)

## Step 2: Transfer Image to Raspberry Pi

### Option A: Using SCP (Recommended)

1. **Save the image** (if not done automatically):
   ```powershell
   docker save plankton-app:minimal-arm64 -o plankton-raspi.tar
   ```

2. **Transfer to Raspberry Pi**:
   ```powershell
   scp plankton-raspi.tar pi@<raspberry-pi-ip>:~/
   ```
   Replace `<raspberry-pi-ip>` with your Raspberry Pi's IP address (e.g., `192.168.1.100`)

### Option B: Using USB Drive

1. Copy `plankton-raspi.tar` to a USB drive
2. Insert USB drive into Raspberry Pi
3. Mount and copy the file:
   ```bash
   sudo mount /dev/sda1 /mnt
   cp /mnt/plankton-raspi.tar ~/
   sudo umount /mnt
   ```

### Option C: Direct Build on Raspberry Pi (Slower)

If you prefer to build directly on the Pi:
```bash
git clone https://github.com/samarth49/SIH2025.git
cd SIH2025
chmod +x build-docker.sh
./build-docker.sh
```
⚠️ **Warning**: This will take 1-2 hours on Raspberry Pi 4

## Step 3: Setup Raspberry Pi

### Install Docker (if not already installed)

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER

# Logout and login again, or run:
newgrp docker

# Verify installation
docker --version
```

### Install Docker Compose (Optional but recommended)

```bash
sudo apt install docker-compose -y
```

## Step 4: Load and Run the Docker Image

### Load the Image

```bash
cd ~
docker load -i plankton-raspi.tar
```

Verify the image is loaded:
```bash
docker images
```

You should see `plankton-app:minimal-arm64` or `plankton-app:full-arm64`

### Create Required Directories

```bash
mkdir -p ~/plankton-app/{checkpoints,database,uploads}
cd ~/plankton-app
```

### Add Your Model File

Copy your trained model (`.pt` file) to the checkpoints directory:

```bash
# If transferring from your PC:
scp path/to/your/model.pt pi@<raspberry-pi-ip>:~/plankton-app/checkpoints/

# Or if using USB:
cp /mnt/model.pt ~/plankton-app/checkpoints/
```

### Run the Container

**Using Docker Run:**

```bash
docker run -d \
  --name plankton-detection \
  -p 8501:8501 \
  -v ~/plankton-app/checkpoints:/app/checkpoints \
  -v ~/plankton-app/database:/app/database \
  -v ~/plankton-app/uploads:/app/uploads \
  --restart unless-stopped \
  plankton-app:minimal-arm64
```

**Using Docker Compose (Recommended):**

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  plankton-app:
    image: plankton-app:minimal-arm64
    container_name: plankton-detection
    ports:
      - "8501:8501"
    volumes:
      - ./checkpoints:/app/checkpoints
      - ./database:/app/database
      - ./uploads:/app/uploads
    restart: unless-stopped
    environment:
      - TZ=Asia/Kolkata
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

Then run:
```bash
docker-compose up -d
```

## Step 5: Access the Application

1. **Find your Raspberry Pi's IP address**:
   ```bash
   hostname -I
   ```

2. **Open in browser**:
   - From same network: `http://<raspberry-pi-ip>:8501`
   - From Raspberry Pi itself: `http://localhost:8501`

## Step 6: Configure for Production (Optional)

### Enable Auto-Start on Boot

The `--restart unless-stopped` flag ensures the container starts automatically on boot.

### Setup Reverse Proxy with Nginx (Optional)

For HTTPS and custom domain:

```bash
sudo apt install nginx -y
```

Create nginx config `/etc/nginx/sites-available/plankton`:

```nginx
server {
    listen 80;
    server_name plankton.local;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable and restart:
```bash
sudo ln -s /etc/nginx/sites-available/plankton /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Management Commands

### View Logs
```bash
docker logs -f plankton-detection
```

### Stop Container
```bash
docker stop plankton-detection
```

### Start Container
```bash
docker start plankton-detection
```

### Restart Container
```bash
docker restart plankton-detection
```

### Update to New Version
```bash
# Stop and remove old container
docker stop plankton-detection
docker rm plankton-detection

# Load new image
docker load -i plankton-raspi-new.tar

# Run new container
docker run -d \
  --name plankton-detection \
  -p 8501:8501 \
  -v ~/plankton-app/checkpoints:/app/checkpoints \
  -v ~/plankton-app/database:/app/database \
  -v ~/plankton-app/uploads:/app/uploads \
  --restart unless-stopped \
  plankton-app:minimal-arm64
```

### Check Container Status
```bash
docker ps
docker stats plankton-detection
```

### Backup Database
```bash
cp ~/plankton-app/database/detection_db.db ~/backups/detection_db_$(date +%Y%m%d).db
```

## Troubleshooting

### Container Won't Start
```bash
# Check logs
docker logs plankton-detection

# Check if port is already in use
sudo netstat -tulpn | grep 8501

# Check available memory
free -h
```

### Out of Memory Errors
```bash
# Check memory usage
docker stats

# Reduce memory usage by using minimal image
# Or add swap space:
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile  # Set CONF_SWAPSIZE=2048
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

### Slow Performance
- Use the minimal image variant
- Ensure you're using Raspberry Pi 4 with 4GB+ RAM
- Close other applications
- Use a fast SD card (Class 10 or better)
- Consider using an SSD via USB 3.0

### Cannot Access from Other Devices
```bash
# Check firewall
sudo ufw status

# Allow port 8501
sudo ufw allow 8501/tcp

# Check if container is running
docker ps
```

## Performance Tips

1. **Use SSD instead of SD card** for better I/O performance
2. **Overclock Raspberry Pi** (if comfortable):
   ```bash
   sudo nano /boot/config.txt
   # Add: over_voltage=6, arm_freq=2000
   ```
3. **Use minimal image** to reduce memory footprint
4. **Disable GUI** if running headless:
   ```bash
   sudo systemctl set-default multi-user.target
   ```
5. **Monitor temperature**:
   ```bash
   vcgencmd measure_temp
   ```

## Security Recommendations

1. **Change default password**:
   ```bash
   passwd
   ```

2. **Setup SSH key authentication**
3. **Enable firewall**:
   ```bash
   sudo ufw enable
   sudo ufw allow ssh
   sudo ufw allow 8501/tcp
   ```

4. **Keep system updated**:
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

5. **Use HTTPS** with nginx and Let's Encrypt for production

## Support

For issues or questions:
- GitHub: https://github.com/samarth49/SIH2025
- Check logs: `docker logs plankton-detection`
- System info: `docker info`, `uname -a`, `free -h`
