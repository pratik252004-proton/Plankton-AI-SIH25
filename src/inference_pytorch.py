import torch
import numpy as np
import os
import argparse
import csv
from PIL import Image
from tqdm import tqdm
from torchvision import transforms
from model import get_model

def load_pytorch_model(model_path, num_classes, device='cpu'):
    """Load trained PyTorch model"""
    model = get_model(num_classes, pretrained=False)
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.to(device)
    model.eval()
    return model

def get_transform():
    """Get the same transforms used during training (without augmentation)"""
    return transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                           std=[0.229, 0.224, 0.225])
    ])

def predict_image(model, image_path, transform, device='cpu'):
    """Predict class for a single image"""
    # Load and preprocess image
    img = Image.open(image_path).convert("RGB")
    img_tensor = transform(img).unsqueeze(0).to(device)
    
    # Predict
    with torch.no_grad():
        output = model(img_tensor)
        probabilities = torch.nn.functional.softmax(output, dim=1)
        predicted_idx = torch.argmax(probabilities, dim=1).item()
        confidence = probabilities[0, predicted_idx].item()
    
    return predicted_idx, confidence

def main():
    parser = argparse.ArgumentParser(description='PyTorch Plankton Inference')
    parser.add_argument('--model_path', type=str, default='checkpoints/best_model.pth',
                       help='Path to trained PyTorch model')
    parser.add_argument('--input_dir', type=str, required=True,
                       help='Folder containing images to classify')
    parser.add_argument('--data_dir', type=str, default='d:/Plankton/101141/individual_images',
                       help='Original data directory (to get class names)')
    parser.add_argument('--output_csv', type=str, default='plankton_counts.csv',
                       help='Output CSV file for counts')
    parser.add_argument('--confidence_threshold', type=float, default=0.0,
                       help='Minimum confidence threshold (0.0-1.0)')
    args = parser.parse_args()
    
    # Determine device
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"Using device: {device}")
    
    # Load class names from data directory
    from data_loader import get_dataloaders
    print("Loading class names...")
    _, _, _, classes, _ = get_dataloaders(args.data_dir, batch_size=1, sample_fraction=0.01)
    num_classes = len(classes)
    print(f"Loaded {num_classes} classes")
    
    # Load model
    print(f"Loading model from {args.model_path}...")
    model = load_pytorch_model(args.model_path, num_classes, device)
    
    # Get transform
    transform = get_transform()
    
    # Initialize counts
    counts = {c: 0 for c in classes}
    low_confidence_count = 0
    
    # Process images
    valid_extensions = ('.png', '.jpg', '.jpeg', '.tif', '.tiff', '.bmp')
    image_files = [f for f in os.listdir(args.input_dir) 
                   if f.lower().endswith(valid_extensions)]
    
    print(f"\nProcessing {len(image_files)} images...")
    
    for img_file in tqdm(image_files):
        img_path = os.path.join(args.input_dir, img_file)
        try:
            predicted_idx, confidence = predict_image(model, img_path, transform, device)
            
            if confidence >= args.confidence_threshold:
                predicted_class = classes[predicted_idx]
                counts[predicted_class] += 1
            else:
                low_confidence_count += 1
                
        except Exception as e:
            print(f"\nError processing {img_file}: {e}")
    
    # Save Report
    print("\n" + "="*50)
    print("PLANKTON CLASSIFICATION RESULTS")
    print("="*50)
    
    total_classified = sum(counts.values())
    
    with open(args.output_csv, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Species', 'Count', 'Percentage'])
        
        # Sort by count (descending)
        sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        
        for species, count in sorted_counts:
            if count > 0:
                percentage = (count / total_classified * 100) if total_classified > 0 else 0
                print(f"{species:40s}: {count:5d} ({percentage:5.2f}%)")
                writer.writerow([species, count, f"{percentage:.2f}"])
    
    print("="*50)
    print(f"Total classified: {total_classified}")
    if low_confidence_count > 0:
        print(f"Low confidence (< {args.confidence_threshold}): {low_confidence_count}")
    print(f"\nReport saved to {args.output_csv}")

if __name__ == '__main__':
    main()
