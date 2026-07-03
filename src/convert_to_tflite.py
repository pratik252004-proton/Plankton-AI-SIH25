import torch
import tensorflow as tf
import onnx
import os
import subprocess
from model import get_model
from data_loader import get_dataloaders
import numpy as np

def convert(model_path, num_classes, output_path='model.tflite'):
    # 1. Load PyTorch Model
    print("Loading PyTorch model...")
    model = get_model(num_classes, pretrained=False)
    model.load_state_dict(torch.load(model_path, map_location='cpu'))
    model.eval()
    
    # 2. Export to ONNX (Opset 18 as recommended)
    print("Exporting to ONNX (Opset 18)...")
    dummy_input = torch.randn(1, 3, 224, 224)
    onnx_path = 'model.onnx'
    torch.onnx.export(model, dummy_input, onnx_path, opset_version=18, 
                      input_names=['input'], output_names=['output'])
    print(f"Exported to {onnx_path}")
    
    # 3. Simplify ONNX (Required for onnx2tf)
    print("Simplifying ONNX model...")
    simplified_onnx_path = 'model_simplified.onnx'
    # Run onnxsim as a subprocess via python module
    import sys
    try:
        subprocess.check_call([sys.executable, '-m', 'onnxsim', onnx_path, simplified_onnx_path])
        print(f"Simplified model saved to {simplified_onnx_path}")
    except Exception as e:
        print(f"Warning: onnxsim failed or not found ({e}). Proceeding with manual shape inference.")
        # Fallback: Manual shape inference using ONNX library
        # This is often enough to fix "axes don't match" errors in onnx2tf
        try:
            print("Running ONNX shape inference...")
            onnx_model = onnx.load(onnx_path)
            onnx_model = onnx.shape_inference.infer_shapes(onnx_model)
            onnx.save(onnx_model, simplified_onnx_path)
            print(f"Shape-inferred model saved to {simplified_onnx_path}")
        except Exception as e2:
            print(f"Warning: Shape inference failed ({e2}). Using original model.")
            simplified_onnx_path = onnx_path

    # 4. Convert ONNX to TF SavedModel using onnx2tf
    print("Converting to TF SavedModel using onnx2tf...")
    # Flags recommended by user: -osd -b 1 -kt -onwdt
    cmd = [
        'onnx2tf',
        '-i', simplified_onnx_path,
        '-o', 'saved_model_tf',
        '-osd',       # Optimize shape
        '-b', '1',    # Static batch size 1
        '-kt', 'input', # Keep Topology (fix kernel transpose)
        '-onwdt',     # Avoid weight dequantization issues
    ]
    
    subprocess.check_call(cmd)
    print("Converted to TF SavedModel via onnx2tf")
    
    # 5. Convert TF SavedModel to TFLite
    print("Converting TF SavedModel to TFLite...")
    converter = tf.lite.TFLiteConverter.from_saved_model('saved_model_tf')
    
    # Optional: INT8 Quantization (commented out for now to ensure basic conversion works first)
    # converter.optimizations = [tf.lite.Optimize.DEFAULT]
    # converter.representative_dataset = representative_dataset_gen
    # converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
    # converter.inference_input_type = tf.int8
    # converter.inference_output_type = tf.int8
    
    tflite_model = converter.convert()
    
    with open(output_path, 'wb') as f:
        f.write(tflite_model)
        
    print(f"Saved TFLite model to {output_path}")

if __name__ == '__main__':
    # Check if best_model.pth exists
    model_path = 'checkpoints/best_model.pth'
    if not os.path.exists(model_path):
        print(f"Error: {model_path} not found. Train the model first.")
    else:
        # We need to know num_classes. 
        # In a real scenario, we'd save this metadata. 
        # For now, we'll reload the dataset to count classes or hardcode if we know it.
        # Let's quickly count folders again to be safe.
        data_dir = 'd:/Plankton/101141/individual_images'
        # Re-use data loader logic to get class count
        # Use a small fraction to avoid loading too much, but > 0 to avoid DataLoader error
        _, _, _, classes, _ = get_dataloaders(data_dir, batch_size=1, sample_fraction=0.01) 
        num_classes = len(classes)
        print(f"Detected {num_classes} classes.")
        
        convert(model_path, num_classes)
