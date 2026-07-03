import tensorflow as tf
import numpy as np
import os
import argparse
import csv
from PIL import Image
from tqdm import tqdm

def load_tflite_model(model_path):
    interpreter = tf.lite.Interpreter(model_path=model_path)
    interpreter.allocate_tensors()
    return interpreter

def predict_image(interpreter, image_path, input_details, output_details):
    # Load and preprocess image
    img = Image.open(image_path).convert("RGB")
    img = img.resize((224, 224))
    
    # Normalize if the model expects it (MobileNetV3 usually expects [0,1] or standardized)
    # Our PyTorch training used standard ImageNet normalization:
    # mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]
    # We need to replicate this for TFLite input
    
    img_array = np.array(img).astype(np.float32) / 255.0
    mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
    std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
    img_array = (img_array - mean) / std
    
    # Add batch dimension
    input_data = np.expand_dims(img_array, axis=0)
    
    # Transpose to NCHW if model was converted from PyTorch without layout change
    # PyTorch: NCHW, TFLite from TF usually NHWC.
    # However, ONNX conversion usually preserves NCHW unless specified.
    # Let's check input details shape to be sure.
    input_shape = input_details[0]['shape']
    if input_shape[1] == 3: # NCHW
        input_data = np.transpose(input_data, (0, 3, 1, 2)) # NHWC -> NCHW
        
    # Quantization handling
    if input_details[0]['dtype'] == np.int8:
        scale, zero_point = input_details[0]['quantization']
        input_data = (input_data / scale + zero_point).astype(np.int8)
    
    interpreter.set_tensor(input_details[0]['index'], input_data)
    interpreter.invoke()
    
    output_data = interpreter.get_tensor(output_details[0]['index'])
    return output_data

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model_path', type=str, default='model.tflite')
    parser.add_argument('--input_dir', type=str, required=True, help='Folder containing images to count')
    parser.add_argument('--class_list', type=str, default='classes.txt', help='File containing class names')
    parser.add_argument('--output_csv', type=str, default='plankton_counts.csv')
    args = parser.parse_args()
    
    # Load classes
    with open(args.class_list, 'r') as f:
        classes = [line.strip() for line in f.readlines()]
        
    # Load Model
    interpreter = load_tflite_model(args.model_path)
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    
    counts = {c: 0 for c in classes}
    
    # Process images
    valid_extensions = ('.png', '.jpg', '.jpeg', '.tif', '.tiff')
    image_files = [f for f in os.listdir(args.input_dir) if f.lower().endswith(valid_extensions)]
    
    print(f"Processing {len(image_files)} images...")
    
    for img_file in tqdm(image_files):
        img_path = os.path.join(args.input_dir, img_file)
        try:
            output = predict_image(interpreter, img_path, input_details, output_details)
            predicted_idx = np.argmax(output)
            predicted_class = classes[predicted_idx]
            counts[predicted_class] += 1
        except Exception as e:
            print(f"Error processing {img_file}: {e}")
            
    # Save Report
    print("\n--- Plankton Counts ---")
    with open(args.output_csv, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Species', 'Count'])
        for species, count in counts.items():
            if count > 0:
                print(f"{species}: {count}")
            writer.writerow([species, count])
            
    print(f"\nReport saved to {args.output_csv}")

if __name__ == '__main__':
    main()
