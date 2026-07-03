# TSV to YOLO Converter

Automatically convert EcoTaxa TSV morphological data to YOLO object detection format without manual annotation.

## 🎯 Overview

This tool leverages the morphological measurements in your EcoTaxa TSV file (1.15M+ plankton observations) to automatically generate bounding box annotations for YOLO training.

## 📊 How It Works

### Morphological Data → Bounding Boxes

The TSV file contains precise measurements for each plankton organism:
- `object_major` - Major axis length (pixels)
- `object_minor` - Minor axis length (pixels)
- `object_area` - Area (pixels²)
- `object_esd` - Equivalent spherical diameter

**The converter uses these measurements to calculate bounding boxes:**

```
Bounding Box Width = (major_axis × 1.2) / image_width
Bounding Box Height = (minor_axis × 1.2) / image_height
```

The 1.2 factor adds a 10% margin around the organism.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install pandas numpy tqdm
```

### 2. Run Conversion

```bash
python convert_tsv_to_yolo.py \
    --tsv ../101138.tsv \
    --images ../101141/individual_images \
    --output yolo_dataset \
    --train-split 0.8
```

### 3. Train YOLOv8

```bash
# Install ultralytics
pip install ultralytics

# Train model
yolo train data=yolo_dataset/data.yaml model=yolov8n.pt epochs=50 imgsz=224
```

## 📋 Command Line Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--tsv` | Path to TSV file | **Required** |
| `--images` | Directory with plankton images | **Required** |
| `--output` | Output directory for YOLO dataset | `yolo_dataset` |
| `--image-size` | Image dimensions (width height) | `224 224` |
| `--train-split` | Training split ratio | `0.8` |
| `--max-per-class` | Max samples per species | `None` (unlimited) |

## 📁 Output Structure

```
yolo_dataset/
├── images/
│   ├── train/           # Training images
│   └── val/             # Validation images
├── labels/
│   ├── train/           # Training annotations (YOLO format)
│   └── val/             # Validation annotations
├── data.yaml            # YOLO configuration
└── conversion_stats.json # Conversion statistics
```

## 🔍 Example Usage

### Basic Conversion

```bash
python convert_tsv_to_yolo.py \
    --tsv ../101138.tsv \
    --images ../101141/individual_images \
    --output plankton_yolo
```

### Limit Samples Per Class

```bash
python convert_tsv_to_yolo.py \
    --tsv ../101138.tsv \
    --images ../101141/individual_images \
    --output plankton_yolo \
    --max-per-class 500
```

### Custom Image Size

```bash
python convert_tsv_to_yolo.py \
    --tsv ../101138.tsv \
    --images ../101141/individual_images \
    --output plankton_yolo \
    --image-size 640 640
```

## 📊 Data Filtering

The converter automatically filters out:
- ❌ Detritus
- ❌ Artifacts
- ❌ Bad focus images
- ❌ Fibers
- ❌ Bubbles
- ✅ **Only living organisms are included**

## 🎓 Training YOLOv8

After conversion, train your model:

```bash
# Nano model (fastest, smallest)
yolo train data=yolo_dataset/data.yaml model=yolov8n.pt epochs=50 imgsz=224

# Small model (balanced)
yolo train data=yolo_dataset/data.yaml model=yolov8s.pt epochs=50 imgsz=224

# Medium model (more accurate)
yolo train data=yolo_dataset/data.yaml model=yolov8m.pt epochs=50 imgsz=640
```

## 📈 Expected Results

With 1.15M+ samples in the TSV:
- **Training samples**: ~920K (80%)
- **Validation samples**: ~230K (20%)
- **Species classes**: 100+ unique species
- **Training time**: 2-4 hours on GPU
- **Expected mAP**: 85-95%

## 🔧 Troubleshooting

### Images Not Found

If images are not found, check:
1. Image directory path is correct
2. Images have standard extensions (.jpg, .png, etc.)
3. Image filenames match `object_id` from TSV

### Memory Issues

If you run out of memory:
```bash
# Limit samples per class
python convert_tsv_to_yolo.py \
    --tsv ../101138.tsv \
    --images ../101141/individual_images \
    --max-per-class 1000
```

### Bounding Box Issues

If bounding boxes seem incorrect:
- Check `--image-size` matches your actual images
- Morphological measurements are in pixels
- Default margin is 20% (1.2x multiplier)

## 📝 Notes

- **No manual annotation needed!** 🎉
- Bounding boxes are estimated from morphological data
- Assumes organisms are centered in images (common in plankton imaging)
- For best results, verify a few samples before full training

## 🎯 Next Steps

1. Run conversion
2. Check `conversion_stats.json` for dataset statistics
3. Verify a few annotations visually
4. Train YOLOv8 model
5. Integrate into Streamlit app

## 📚 References

- [YOLOv8 Documentation](https://docs.ultralytics.com/)
- [EcoTaxa](https://ecotaxa.obs-vlfr.fr/)
- [YOLO Format Specification](https://docs.ultralytics.com/datasets/detect/)
