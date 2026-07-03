# 🚀 Google Colab Training Guide

Complete guide to train your plankton detector on Google Colab with free GPU/TPU.

## 📋 Prerequisites

### 1. Upload to Google Drive

Create a folder structure in Google Drive:

```
Google Drive/
└── Plankton/
    ├── 101138.tsv              # Your TSV file
    └── individual_images/       # Your plankton images
```

### 2. Open Colab Notebook

1. Upload `Plankton_TSV_to_YOLO_Colab.ipynb` to Google Drive
2. Right-click → Open with → Google Colaboratory
3. Or visit: https://colab.research.google.com/

## ⚡ Quick Start (5 Steps)

### Step 1: Enable GPU

```
Runtime → Change runtime type → Hardware accelerator → GPU (T4)
```

**Free tier includes:**
- ✅ NVIDIA T4 GPU (16GB VRAM)
- ✅ 12GB RAM
- ✅ ~12 hours continuous runtime

### Step 2: Update Paths

In the **Configuration** cell, update these paths:

```python
# Path to TSV file in Google Drive
TSV_PATH = '/content/drive/MyDrive/Plankton/101138.tsv'

# Path to images directory in Google Drive
IMAGES_DIR = '/content/drive/MyDrive/Plankton/individual_images'
```

### Step 3: Run All Cells

```
Runtime → Run all
```

Or press `Ctrl+F9` (Windows) / `Cmd+F9` (Mac)

### Step 4: Authorize Google Drive

When prompted:
1. Click the link
2. Choose your Google account
3. Click "Allow"
4. Copy the authorization code
5. Paste it back in Colab

### Step 5: Wait for Training

**Timeline:**
- Conversion: 10-30 minutes (depends on dataset size)
- Training: 1-3 hours (50 epochs on GPU)
- Export: 2-5 minutes

**Total: ~2-4 hours**

## 📊 What Happens

### 1. TSV to YOLO Conversion

```
Loading TSV... ✓
Found 1,150,000 records
Found 100+ unique species
Processing species... [████████████] 100%

Conversion Complete!
Train samples: 40,000
Val samples: 10,000
```

### 2. YOLOv8 Training

```
Training YOLOv8 Plankton Detector
Model: yolov8n.pt
Epochs: 50
Batch size: 16

Epoch 1/50: 100%|██████| loss: 2.345
Epoch 10/50: 100%|██████| loss: 1.234
Epoch 50/50: 100%|██████| loss: 0.456

Training complete!
```

### 3. Validation

```
Validation Results
mAP50: 0.8934
mAP50-95: 0.7123
Precision: 0.8756
Recall: 0.8234
```

### 4. Export & Save

```
Exporting model...
✓ Exported to ONNX
✓ Exported to TFLite

Model saved to: Google Drive/Plankton/trained_model/
```

## 🎛️ Configuration Options

### Limit Samples (Faster Training)

```python
MAX_SAMPLES_PER_CLASS = 100  # Only 100 samples per species
```

**Use this if:**
- You want quick testing
- Limited time
- Prototyping

### Model Size

```python
MODEL_SIZE = 'n'  # Options: 'n', 's', 'm', 'l', 'x'
```

| Size | Speed | Accuracy | Training Time | Best For |
|------|-------|----------|---------------|----------|
| `n` (nano) | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | 1-2 hours | Real-time, Raspberry Pi |
| `s` (small) | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 2-3 hours | Balanced |
| `m` (medium) | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 3-4 hours | High accuracy |
| `l` (large) | ⭐⭐ | ⭐⭐⭐⭐⭐ | 4-6 hours | Maximum accuracy |

### Training Epochs

```python
EPOCHS = 50  # More epochs = better accuracy (but longer training)
```

**Recommendations:**
- Quick test: 10-20 epochs
- Normal: 50 epochs
- High accuracy: 100+ epochs

### Batch Size

```python
BATCH_SIZE = 16  # Adjust based on GPU memory
```

**If you get "Out of Memory" error:**
- Reduce to 8 or 4
- Or use smaller model size

## 📥 Download Trained Model

### Option 1: From Google Drive

After training completes:
1. Open Google Drive
2. Navigate to `Plankton/trained_model/plankton_detector/`
3. Download `weights/best.pt`

### Option 2: Direct Download

Run the last cell in the notebook:
```python
from google.colab import files
files.download('runs/detect/plankton_detector/weights/best.pt')
```

## 🔧 Troubleshooting

### "No GPU available"

**Solution:**
```
Runtime → Change runtime type → GPU → Save
```

Then restart runtime:
```
Runtime → Restart runtime
```

### "Out of Memory"

**Solutions:**
1. Reduce batch size: `BATCH_SIZE = 8`
2. Use smaller model: `MODEL_SIZE = 'n'`
3. Limit samples: `MAX_SAMPLES_PER_CLASS = 200`

### "Images not found"

**Check:**
1. Images are uploaded to Google Drive
2. Path is correct in configuration
3. Images have standard extensions (.jpg, .png)

**Verify path:**
```python
!ls "/content/drive/MyDrive/Plankton/individual_images" | head
```

### "Runtime disconnected"

**Colab free tier limits:**
- 12 hours max continuous runtime
- May disconnect if idle

**Solution:**
- Keep browser tab active
- Or upgrade to Colab Pro ($10/month)

### "Quota exceeded"

**Colab free tier:**
- Limited GPU hours per day
- Resets every 24 hours

**Solution:**
- Wait 24 hours
- Or use Colab Pro (unlimited GPU)

## 💡 Tips & Tricks

### 1. Save Checkpoints

The notebook auto-saves every 10 epochs to:
```
runs/detect/plankton_detector/weights/
├── best.pt    # Best model so far
└── last.pt    # Latest checkpoint
```

If training crashes, you can resume from `last.pt`.

### 2. Monitor Training

Watch the loss curve in real-time:
- Lower loss = better model
- Should decrease over time
- Plateaus around epoch 30-40

### 3. Prevent Disconnection

Run this in a cell to keep Colab active:
```python
import time
while True:
    time.sleep(60)
    print(".", end="")
```

### 4. Use Colab Pro

**Benefits:**
- Faster GPUs (A100, V100)
- Longer runtime (24 hours)
- More RAM (32GB)
- Priority access

**Cost:** $10/month

## 📊 Expected Results

### Dataset Statistics

```
Total samples: 50,000
Train: 40,000 (80%)
Val: 10,000 (20%)
Species: 100+
```

### Training Performance

```
Epoch 50/50
Loss: 0.45
mAP50: 0.89
mAP50-95: 0.71
Precision: 0.88
Recall: 0.82
```

### Inference Speed

```
GPU (T4): 60+ FPS
CPU: 10-15 FPS
Raspberry Pi 4: 5-8 FPS
```

## 🎯 Next Steps

After training:

1. **Download model** from Google Drive
2. **Test locally** on sample videos
3. **Integrate into Streamlit app**
4. **Deploy to production**

### Integration Code

```python
from ultralytics import YOLO

# Load trained model
model = YOLO('best.pt')

# Detect in video frame
results = model(frame, conf=0.5)

# Get detections
for box in results[0].boxes:
    x1, y1, x2, y2 = box.xyxy[0]
    confidence = box.conf[0]
    class_id = int(box.cls[0])
    species = model.names[class_id]
    
    # Draw box, count organisms, etc.
```

## 📚 Resources

- [YOLOv8 Documentation](https://docs.ultralytics.com/)
- [Google Colab Guide](https://colab.research.google.com/notebooks/intro.ipynb)
- [Colab Pro](https://colab.research.google.com/signup)

---

**🎉 You're ready to train your plankton detector on Google Colab!**

Upload the notebook, configure paths, and hit "Run all"!
