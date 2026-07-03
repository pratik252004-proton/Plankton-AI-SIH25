import sys
import os
sys.path.append('d:/Plankton/src')
from data_loader import get_dataloaders
from model import get_model
import torch

def test_setup():
    print("Testing Data Loader...")
    data_dir = 'd:/Plankton/101141/individual_images'
    try:
        train_loader, val_loader, test_loader, classes, weights = get_dataloaders(data_dir, batch_size=4, num_workers=0)
        print(f"Successfully loaded {len(classes)} classes.")
        print(f"Sample classes: {classes[:5]}")
        print(f"Class weights shape: {weights.shape if weights is not None else 'None'}")
        
        # Test getting one batch
        images, labels = next(iter(train_loader))
        print(f"Batch shape: {images.shape}")
        print(f"Labels: {labels}")
        
    except Exception as e:
        print(f"Data Loader failed: {e}")
        return

    print("\nTesting Model Instantiation...")
    try:
        model = get_model(len(classes), pretrained=True)
        print("Model instantiated successfully.")
        
        # Test forward pass
        output = model(images)
        print(f"Output shape: {output.shape}")
        
    except Exception as e:
        print(f"Model failed: {e}")
        return
        
    print("\nSetup Verification Passed!")

if __name__ == '__main__':
    test_setup()
