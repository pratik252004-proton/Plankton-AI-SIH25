# Quick Start: Building Optimized Docker Image for Raspberry Pi

## ✅ Your Setup is Perfect for Raspberry Pi!

**Model:** MobileNetV3-Small - specifically designed for edge devices like Raspberry Pi  
**Compatibility:** Fully compatible with ARM64 architecture  
**Performance:** Real-time plankton detection on Raspberry Pi 4

---

## 🚀 Quick Build (Windows → Raspberry Pi)

### Step 1: Build the Image

```powershell
cd d:\Plankton
.\build-docker.ps1
```

**When prompted, select:**
- **Option 1** (Minimal - Recommended) → ~2.5GB image
- **Option 2** (Full) → ~3.5GB image (includes SQL chat)

### Step 2: Transfer to Raspberry Pi

```powershell
# Save the image
docker save plankton-app:minimal -o plankton-app.tar

# Transfer to Pi (replace with your Pi's IP)
scp plankton-app.tar pi@192.168.1.XXX:~/
```

### Step 3: Deploy on Raspberry Pi

```bash
# Load the image
docker load -i plankton-app.tar

# Navigate to project directory
cd ~/Plankton

# Start the application
docker-compose up -d

# View logs
docker-compose logs -f
```

### Step 4: Access Application

Open browser: `http://<raspberry-pi-ip>:8501`

---

## 📊 Image Comparison

| Feature | Minimal | Full |
|---------|---------|------|
| **Size** | ~2.5GB | ~3.5GB |
| **Build time** | ~15-20 min | ~20-30 min |
| **Image analysis** | ✅ | ✅ |
| **Video analysis** | ✅ | ✅ |
| **Batch processing** | ✅ | ✅ |
| **Database logging** | ✅ | ✅ |
| **SQL chat** | ❌ | ✅ |
| **Raspberry Pi** | ✅ Recommended | ⚠️ Works but larger |

---

## 💡 Recommendation

**Use Minimal variant** for Raspberry Pi:
- 40% smaller (saves 1GB)
- Faster build and transfer
- All core detection features included
- SQL chat is optional and rarely used

---

## 🔧 Alternative: Build on Raspberry Pi

If you prefer to build directly on the Pi:

```bash
cd ~/Plankton
chmod +x build-docker.sh
./build-docker.sh
# Select option 1 (minimal)
```

**Note:** Building on Pi takes longer (~30-45 min) but avoids file transfer.

---

## ❓ Need Help?

See full documentation:
- [DOCKER_README.md](file:///d:/Plankton/DOCKER_README.md) - Quick reference
- [Troubleshooting Guide](file:///C:/Users/otari/.gemini/antigravity/brain/ed5f24ce-11e0-4680-9d39-92ad70a01353/docker_troubleshooting.md) - Common errors
- [Walkthrough](file:///C:/Users/otari/.gemini/antigravity/brain/ed5f24ce-11e0-4680-9d39-92ad70a01353/walkthrough.md) - Detailed explanation
