# TSV-to-YOLO Quick Reference

## 🚀 One-Page Cheat Sheet

### Installation
```bash
cd tsv-to-yolo
pip install -r requirements.txt
```

### Conversion
```bash
# Basic conversion
python convert_tsv_to_yolo.py \
    --tsv ../101138.tsv \
    --images ../101141/individual_images \
    --output yolo_dataset

# With sample limiting (faster)
python convert_tsv_to_yolo.py \
    --tsv ../101138.tsv \
    --images ../101141/individual_images \
    --output yolo_dataset \
    --max-per-class 500
```

### Verification
```bash
python verify_annotations.py --dataset yolo_dataset --num-samples 10
```

### Training
```bash
# Nano model (fastest)
python train_yolo.py --data yolo_dataset/data.yaml --model n --epochs 50

# Medium model (more accurate)
python train_yolo.py --data yolo_dataset/data.yaml --model m --epochs 100 --imgsz 640
```

### Inference
```python
from ultralytics import YOLO

model = YOLO('runs/detect/plankton_detector/weights/best.pt')
results = model('image.jpg', conf=0.5)
```

## 📋 Parameter Reference

### Conversion Parameters
| Flag | Description | Default | Example |
|------|-------------|---------|---------|
| `--tsv` | TSV file path | Required | `../101138.tsv` |
| `--images` | Image directory | Required | `../101141/individual_images` |
| `--output` | Output directory | `yolo_dataset` | `my_dataset` |
| `--image-size` | Image size (W H) | `224 224` | `640 640` |
| `--train-split` | Train/val ratio | `0.8` | `0.7` |
| `--max-per-class` | Max samples/class | `None` | `500` |

### Training Parameters
| Flag | Description | Default | Example |
|------|-------------|---------|---------|
| `--data` | data.yaml path | Required | `yolo_dataset/data.yaml` |
| `--model` | Model size | `n` | `s`, `m`, `l`, `x` |
| `--epochs` | Training epochs | `50` | `100` |
| `--imgsz` | Image size | `224` | `640` |
| `--batch` | Batch size | `16` | `8`, `32` |
| `--device` | Device | `0` | `cpu` |

## 🎛️ Model Sizes

| Size | Parameters | Speed | Accuracy | Use Case |
|------|-----------|-------|----------|----------|
| `n` | 3.2M | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | Real-time, Edge devices |
| `s` | 11.2M | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Balanced |
| `m` | 25.9M | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | High accuracy |
| `l` | 43.7M | ⭐⭐ | ⭐⭐⭐⭐⭐ | Maximum accuracy |

## 🔧 Common Commands

### Quick Test (Small Dataset)
```bash
python convert_tsv_to_yolo.py --tsv ../101138.tsv --images ../101141/individual_images --max-per-class 100
python train_yolo.py --data yolo_dataset/data.yaml --model n --epochs 10
```

### Production Training
```bash
python convert_tsv_to_yolo.py --tsv ../101138.tsv --images ../101141/individual_images --max-per-class 500
python train_yolo.py --data yolo_dataset/data.yaml --model m --epochs 100 --imgsz 640
```

### Export Model
```python
from ultralytics import YOLO

model = YOLO('runs/detect/plankton_detector/weights/best.pt')
model.export(format='onnx')  # For deployment
model.export(format='tflite')  # For Raspberry Pi
```

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| Images not found | Check `--images` path, verify filenames match TSV `object_id` |
| Out of memory | Reduce `--batch` to 8 or 4, use smaller model (`--model n`) |
| Bounding boxes wrong | Adjust `--image-size` to match actual image dimensions |
| Training too slow | Use GPU, reduce dataset size with `--max-per-class` |
| Low accuracy | Train longer (`--epochs 100`), use larger model (`--model m`) |

## 📊 Expected Performance

### Dataset (MAX_SAMPLES_PER_CLASS=500)
- Total: ~50,000 samples
- Train: ~40,000 (80%)
- Val: ~10,000 (20%)
- Classes: 100+

### Training (YOLOv8n, 50 epochs, T4 GPU)
- Time: 1-3 hours
- mAP50: 0.85-0.95
- Precision: 0.85-0.90
- Recall: 0.80-0.85

### Inference
- GPU (T4): 60+ FPS
- CPU (i7): 10-15 FPS
- Raspberry Pi 4: 5-8 FPS

## 📁 Output Structure

```
yolo_dataset/
├── images/
│   ├── train/          # Training images
│   └── val/            # Validation images
├── labels/
│   ├── train/          # Training labels (YOLO format)
│   └── val/            # Validation labels
├── data.yaml           # YOLO config
└── conversion_stats.json

runs/detect/plankton_detector/
├── weights/
│   ├── best.pt         # Best model ← Use this
│   ├── best.onnx       # ONNX export
│   └── last.pt         # Last checkpoint
└── Training plots
```

## 🌐 Google Colab

### Setup
1. Upload `101138.tsv` and `101141.zip` to Google Drive
2. Open `Plankton_TSV_to_YOLO_Enhanced.ipynb` in Colab
3. Runtime → Change runtime type → GPU
4. Update paths in Configuration cell
5. Runtime → Run all

### Paths
```python
TSV_PATH = '/content/drive/MyDrive/101138.tsv'
ZIP_PATH = '/content/drive/MyDrive/101141.zip'
```

## 💻 Integration Code

```python
from ultralytics import YOLO
import cv2

# Load model
model = YOLO('best.pt')

# Detect in frame
results = model(frame, conf=0.5)

# Process detections
for box in results[0].boxes:
    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
    confidence = box.conf[0].cpu().numpy()
    class_id = int(box.cls[0].cpu().numpy())
    species = model.names[class_id]
    
    # Draw box
    cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
    cv2.putText(frame, f'{species} {confidence:.2f}', 
                (int(x1), int(y1)-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
```

## 📚 Resources

- **YOLOv8 Docs**: https://docs.ultralytics.com/
- **Full README**: See `README.md` in this directory
- **Analysis**: See `ANALYSIS.md` for detailed workflow

---

**Quick Start**: `python convert_tsv_to_yolo.py --tsv ../101138.tsv --images ../101141/individual_images --max-per-class 500 && python train_yolo.py --data yolo_dataset/data.yaml --model n --epochs 50`
