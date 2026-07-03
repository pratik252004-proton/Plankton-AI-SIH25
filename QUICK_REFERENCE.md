# Plankton AI System - Quick Reference

## 🚀 Quick Start Commands

### 1. Full Training
```powershell
# Train on full dataset
d:/Plankton/venv/Scripts/python d:/Plankton/src/train.py --epochs 20 --batch_size 32 --save_dir checkpoints

# Train on subset (for testing)
d:/Plankton/venv/Scripts/python d:/Plankton/src/train.py --epochs 5 --batch_size 32 --sample_fraction 0.1
```

### 2. Inference (PyTorch)
```powershell
# Run inference on a folder
d:/Plankton/venv/Scripts/python d:/Plankton/src/inference_pytorch.py --input_dir <path_to_images> --output_csv results.csv

# With confidence threshold
d:/Plankton/venv/Scripts/python d:/Plankton/src/inference_pytorch.py --input_dir <path_to_images> --output_csv results.csv --confidence_threshold 0.7
```

### 3. Test Setup
```powershell
# Verify data loader and model
d:/Plankton/venv/Scripts/python d:/Plankton/src/test_setup.py
```

---

## 📊 Model Performance

### Current Status
- **Classes**: 113 organism types
- **Model**: MobileNetV3-Small
- **Training**: Tested on 5% data (2 epochs)
- **Inference Speed**: ~20-30 images/sec (CPU)

### Expected Performance (After Full Training)
- **Accuracy**: 85-95% (typical for plankton classification)
- **Inference Speed**: 
  - CPU: 20-30 images/sec
  - GPU: 100-200 images/sec
  - Embedded (TFLite): 5-15 images/sec

---

## 🔧 Troubleshooting

### Issue: Out of Memory During Training
**Solution**: Reduce batch size
```powershell
d:/Plankton/venv/Scripts/python d:/Plankton/src/train.py --batch_size 16
```

### Issue: Training Too Slow
**Solution**: Use GPU or reduce sample fraction
```powershell
# Use subset
d:/Plankton/venv/Scripts/python d:/Plankton/src/train.py --sample_fraction 0.5
```

### Issue: TFLite Conversion Fails
**Solutions**:
1. Use ONNX Runtime instead
2. Use Docker with compatible versions
3. Use Python 3.10 environment
4. Use PyTorch Mobile

---

## 📁 Important Files

| File | Purpose | Status |
|------|---------|--------|
| `src/train.py` | Training pipeline | ✅ Working |
| `src/inference_pytorch.py` | PyTorch inference | ✅ Working |
| `src/data_loader.py` | Data loading | ✅ Working |
| `src/model.py` | Model definition | ✅ Working |
| `checkpoints/best_model.pth` | Trained model | ⏳ Pending full training |
| `src/convert_to_tflite.py` | TFLite conversion | ⚠️ Blocked |

---

## 🎯 Deployment Options

### Option 1: ONNX Runtime (Easiest)
```powershell
# Export to ONNX (already in convert_to_tflite.py)
# Then deploy with ONNX Runtime on embedded device
```
**Pros**: Cross-platform, no dependency issues
**Cons**: Slightly larger model size

### Option 2: TFLite (Best for Mobile/Embedded)
**Status**: Blocked by dependency conflicts
**Workaround**: Use Docker or Python 3.10

### Option 3: PyTorch Mobile
**Pros**: Native PyTorch, good performance
**Cons**: Larger model size than TFLite

---

## 📈 Next Steps Priority

1. **HIGH**: Run full training (20 epochs)
2. **HIGH**: Evaluate on test set
3. **MEDIUM**: Choose deployment strategy
4. **MEDIUM**: Optimize model (quantization)
5. **LOW**: Build production API

---

## 💡 Tips

- Start with small `sample_fraction` for quick testing
- Monitor validation accuracy during training
- Use confidence thresholding to filter uncertain predictions
- Save multiple checkpoints during training
- Test inference on diverse samples before deployment

---

## 🆘 Getting Help

If you encounter issues:
1. Check the error message carefully
2. Verify file paths are correct
3. Ensure virtual environment is activated
4. Check available memory/disk space
5. Review the walkthrough.md for detailed guidance
