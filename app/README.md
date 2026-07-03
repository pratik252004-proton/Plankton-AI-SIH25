# 🔬 Plankton Detection & Analysis System

A scientific web application for automated marine plankton identification and counting using deep learning.

## Features

### 🎯 Core Capabilities
- **Image Analysis**: Upload single or multiple plankton images for species identification
- **Video Analysis**: Frame-by-frame analysis of microscopy videos
- **Real-time Processing**: Live detection with confidence scoring
- **Scientific Visualization**: Professional charts and graphs for data analysis
- **Export Functionality**: Download results in CSV, JSON formats

### 📊 Analysis Tools
- Species distribution bar charts
- Composition pie charts
- Confidence score histograms
- Detailed detection tables
- Summary statistics

### 🎨 Scientific UI
- Professional dark theme optimized for scientific work
- Gradient-based color schemes
- Interactive visualizations
- Responsive layout for all screen sizes

## Installation

### Prerequisites
- Python 3.8 or higher
- CUDA-capable GPU (optional, for faster inference)

### Setup

1. **Clone or navigate to the project directory:**
```bash
cd d:/Plankton
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Verify model checkpoints exist:**
```
checkpoints/
├── best_model.pth
└── epoch1.pth
```

## Usage

### Starting the Application

Run the Streamlit app:
```bash
streamlit run app/streamlit_app.py
```

The application will open in your default web browser at `http://localhost:8501`

### Using the Interface

#### 1. Image Analysis
1. Navigate to the **📸 Image Analysis** tab
2. Upload one or more plankton images (PNG, JPG, TIFF)
3. Click **🔍 Analyze Images**
4. View results:
   - Summary metrics (total detections, unique species, avg confidence)
   - Species distribution charts
   - Confidence analysis
   - Detailed results table
5. Export results using the download buttons

#### 2. Video Analysis
1. Navigate to the **🎥 Video Analysis** tab
2. Upload a microscopy video (MP4, AVI, MOV)
3. Review video information (duration, FPS, resolution)
4. Adjust frame sampling rate in the sidebar (default: 1 FPS)
5. Click **🎬 Analyze Video**
6. View frame-by-frame detection timeline
7. Export results and summary statistics

#### 3. Configuration

**Sidebar Settings:**
- **Model Selection**: Choose between `best_model.pth` or `epoch1.pth`
- **Confidence Threshold**: Set minimum confidence (0.0 - 1.0)
- **Video Frame Sampling**: Adjust frames per second to extract

## System Architecture

```
┌─────────────────────────────────────────┐
│         Streamlit Web Interface         │
└─────────────────┬───────────────────────┘
                  │
        ┌─────────┴──────────┐
        │                    │
┌───────▼────────┐  ┌────────▼────────┐
│ Image Processor│  │ Video Processor │
└───────┬────────┘  └────────┬────────┘
        │                    │
        └─────────┬──────────┘
                  │
        ┌─────────▼──────────┐
        │  Inference Engine  │
        │  (MobileNetV3)     │
        └─────────┬──────────┘
                  │
        ┌─────────▼──────────┐
        │   Visualization    │
        │   & Export Tools   │
        └────────────────────┘
```

## File Structure

```
d:/Plankton/
├── app/
│   └── streamlit_app.py       # Main Streamlit application
├── src/
│   ├── model.py               # Model architecture
│   ├── data_loader.py         # Dataset handling
│   ├── inference_pytorch.py   # PyTorch inference
│   ├── video_processor.py     # Video frame extraction
│   └── utils.py               # Visualization & export
├── checkpoints/
│   ├── best_model.pth         # Best trained model
│   └── epoch1.pth             # Epoch 1 checkpoint
└── requirements.txt           # Python dependencies
```

## Technical Details

### Model
- **Architecture**: MobileNetV3-Small
- **Input Size**: 224x224 RGB images
- **Preprocessing**: ImageNet normalization
- **Device**: Auto-detects CUDA/CPU

### Processing
- **Image Formats**: PNG, JPG, JPEG, TIFF, TIF
- **Video Formats**: MP4, AVI, MOV
- **Frame Sampling**: Configurable (0.5 - 5.0 FPS)
- **Batch Processing**: Supported for multiple images

### Export Formats
- **CSV**: Tabular data with species, confidence, timestamps
- **JSON**: Structured data with full details
- **Summary**: Aggregated statistics and metadata

## Performance Tips

1. **GPU Acceleration**: If CUDA is available, the system will automatically use GPU for faster inference
2. **Video Sampling**: For long videos, use lower FPS (0.5-1.0) to reduce processing time
3. **Confidence Threshold**: Adjust based on your accuracy requirements:
   - High threshold (0.7-0.9): Fewer but more confident detections
   - Low threshold (0.3-0.5): More detections but may include false positives

## Troubleshooting

### Model Loading Issues
- Ensure checkpoint files exist in `checkpoints/` directory
- Verify the data directory path is correct: `d:/Plankton/101141/individual_images`

### Memory Issues
- Reduce video frame sampling rate
- Process fewer images at once
- Use CPU instead of GPU if VRAM is limited

### Visualization Issues
- Ensure matplotlib backend is set correctly
- Check that all visualization dependencies are installed

## Future Enhancements

- [ ] Batch processing for multiple videos
- [ ] Real-time webcam/microscope feed
- [ ] Advanced filtering and search
- [ ] Comparative analysis across samples
- [ ] PDF report generation
- [ ] Database integration for long-term storage
- [ ] Object detection with bounding boxes
- [ ] Species-specific analytics

## Citation

If you use this system in your research, please cite:

```
Marine Plankton Detection System
Automated species identification using MobileNetV3 deep learning
2025
```

## License

For research and educational purposes.

## Support

For issues or questions, please refer to the main project documentation.

---

**Built with ❤️ for marine biology research**
