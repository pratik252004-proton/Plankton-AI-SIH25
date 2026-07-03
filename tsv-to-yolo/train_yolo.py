"""
Train YOLOv8 model on converted plankton dataset
"""
from ultralytics import YOLO
from pathlib import Path
import yaml


def train_yolo_model(data_yaml, model_size='n', epochs=50, imgsz=224, batch=16, device=0):
    """
    Train YOLOv8 model
    
    Args:
        data_yaml: Path to data.yaml file
        model_size: Model size ('n', 's', 'm', 'l', 'x')
        epochs: Number of training epochs
        imgsz: Image size
        batch: Batch size
        device: Device to use (0 for GPU, 'cpu' for CPU)
    """
    # Model size mapping
    model_map = {
        'n': 'yolov8n.pt',  # Nano - fastest, smallest
        's': 'yolov8s.pt',  # Small - balanced
        'm': 'yolov8m.pt',  # Medium - more accurate
        'l': 'yolov8l.pt',  # Large - very accurate
        'x': 'yolov8x.pt'   # Extra large - most accurate
    }
    
    model_path = model_map.get(model_size, 'yolov8n.pt')
    
    print("="*60)
    print("YOLOv8 Plankton Detection Training")
    print("="*60)
    print(f"Model: {model_path}")
    print(f"Data: {data_yaml}")
    print(f"Epochs: {epochs}")
    print(f"Image size: {imgsz}")
    print(f"Batch size: {batch}")
    print(f"Device: {device}")
    print("="*60)
    
    # Load model
    model = YOLO(model_path)
    
    # Train model
    results = model.train(
        data=data_yaml,
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        name='plankton_detector',
        patience=10,
        device=device,
        workers=8,
        cache=True,  # Cache images for faster training
        save=True,
        save_period=10,  # Save checkpoint every 10 epochs
        plots=True,  # Generate training plots
        verbose=True
    )
    
    print("\n" + "="*60)
    print("Training Complete!")
    print("="*60)
    
    # Validate model
    print("\nValidating model...")
    metrics = model.val()
    
    print(f"\nValidation Results:")
    print(f"  mAP50: {metrics.box.map50:.4f}")
    print(f"  mAP50-95: {metrics.box.map:.4f}")
    print(f"  Precision: {metrics.box.mp:.4f}")
    print(f"  Recall: {metrics.box.mr:.4f}")
    
    # Export model
    print("\nExporting model...")
    
    # Export to ONNX (for deployment)
    model.export(format='onnx')
    print("  ✓ Exported to ONNX format")
    
    # Export to TFLite (for Raspberry Pi)
    try:
        model.export(format='tflite')
        print("  ✓ Exported to TFLite format")
    except Exception as e:
        print(f"  ✗ TFLite export failed: {e}")
    
    print("\n" + "="*60)
    print("Model saved to: runs/detect/plankton_detector/")
    print("Best weights: runs/detect/plankton_detector/weights/best.pt")
    print("="*60)
    
    return model, metrics


def main():
    """Main training function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Train YOLOv8 on plankton dataset')
    parser.add_argument('--data', type=str, default='yolo_dataset/data.yaml', help='Path to data.yaml')
    parser.add_argument('--model', type=str, default='n', choices=['n', 's', 'm', 'l', 'x'], help='Model size')
    parser.add_argument('--epochs', type=int, default=50, help='Number of epochs')
    parser.add_argument('--imgsz', type=int, default=224, help='Image size')
    parser.add_argument('--batch', type=int, default=16, help='Batch size')
    parser.add_argument('--device', type=str, default='0', help='Device (0 for GPU, cpu for CPU)')
    
    args = parser.parse_args()
    
    # Convert device to int if it's a number
    device = int(args.device) if args.device.isdigit() else args.device
    
    # Train model
    train_yolo_model(
        data_yaml=args.data,
        model_size=args.model,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=device
    )


if __name__ == "__main__":
    main()
