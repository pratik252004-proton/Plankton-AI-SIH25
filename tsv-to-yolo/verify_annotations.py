"""
Verify YOLO annotations by visualizing bounding boxes on images
"""
import cv2
import numpy as np
from pathlib import Path
import random


def draw_yolo_bbox(image, bbox, class_name, color=(0, 255, 0)):
    """
    Draw YOLO bounding box on image
    
    Args:
        image: Image array
        bbox: (x_center, y_center, width, height) in normalized format
        class_name: Class name to display
        color: BGR color tuple
    """
    h, w = image.shape[:2]
    
    # Convert from YOLO format to pixel coordinates
    x_center, y_center, width, height = bbox
    
    x1 = int((x_center - width/2) * w)
    y1 = int((y_center - height/2) * h)
    x2 = int((x_center + width/2) * w)
    y2 = int((y_center + height/2) * h)
    
    # Draw bounding box
    cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
    
    # Draw label background
    label = class_name
    (label_w, label_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
    cv2.rectangle(image, (x1, y1 - label_h - 10), (x1 + label_w + 10, y1), color, -1)
    
    # Draw label text
    cv2.putText(image, label, (x1 + 5, y1 - 5), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    return image


def verify_dataset(dataset_dir, num_samples=10, split='train'):
    """
    Verify YOLO dataset by visualizing random samples
    
    Args:
        dataset_dir: Path to YOLO dataset directory
        num_samples: Number of samples to visualize
        split: 'train' or 'val'
    """
    dataset_path = Path(dataset_dir)
    images_dir = dataset_path / 'images' / split
    labels_dir = dataset_path / 'labels' / split
    
    # Load class names from data.yaml
    yaml_path = dataset_path / 'data.yaml'
    class_names = []
    
    if yaml_path.exists():
        with open(yaml_path, 'r') as f:
            lines = f.readlines()
            for line in lines:
                if line.strip().startswith('names:'):
                    # Extract class names from YAML list
                    names_str = line.split('names:')[1].strip()
                    class_names = eval(names_str)  # Convert string list to actual list
                    break
    
    if not class_names:
        print("Warning: Could not load class names from data.yaml")
        class_names = [f"Class_{i}" for i in range(100)]
    
    # Get all image files
    image_files = list(images_dir.glob('*.jpg')) + list(images_dir.glob('*.png'))
    
    if not image_files:
        print(f"No images found in {images_dir}")
        return
    
    # Select random samples
    samples = random.sample(image_files, min(num_samples, len(image_files)))
    
    print(f"\nVerifying {len(samples)} samples from {split} set...")
    print("Press any key to view next image, 'q' to quit\n")
    
    for img_path in samples:
        # Load image
        image = cv2.imread(str(img_path))
        if image is None:
            print(f"Failed to load {img_path}")
            continue
        
        # Load corresponding label
        label_path = labels_dir / f"{img_path.stem}.txt"
        
        if not label_path.exists():
            print(f"Warning: No label found for {img_path.name}")
            continue
        
        # Read YOLO annotations
        with open(label_path, 'r') as f:
            lines = f.readlines()
        
        # Draw each bounding box
        for line in lines:
            parts = line.strip().split()
            if len(parts) != 5:
                continue
            
            class_id = int(parts[0])
            bbox = [float(x) for x in parts[1:5]]
            
            class_name = class_names[class_id] if class_id < len(class_names) else f"Class_{class_id}"
            
            # Generate color based on class_id
            color = (
                (class_id * 50) % 255,
                (class_id * 100) % 255,
                (class_id * 150) % 255
            )
            
            image = draw_yolo_bbox(image, bbox, class_name, color)
        
        # Display image
        window_name = f"Verification: {img_path.name}"
        cv2.imshow(window_name, image)
        
        print(f"Showing: {img_path.name}")
        print(f"  Annotations: {len(lines)}")
        
        # Wait for key press
        key = cv2.waitKey(0)
        cv2.destroyAllWindows()
        
        if key == ord('q'):
            print("Verification stopped by user")
            break
    
    print("\nVerification complete!")


def main():
    """Main verification function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Verify YOLO annotations')
    parser.add_argument('--dataset', type=str, default='yolo_dataset', help='Path to YOLO dataset')
    parser.add_argument('--num-samples', type=int, default=10, help='Number of samples to verify')
    parser.add_argument('--split', type=str, default='train', choices=['train', 'val'], help='Dataset split')
    
    args = parser.parse_args()
    
    verify_dataset(args.dataset, args.num_samples, args.split)


if __name__ == "__main__":
    main()
