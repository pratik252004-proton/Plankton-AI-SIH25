import torch
import sys
from pathlib import Path

# Add src to path
sys.path.append('src')
from data_loader import get_dataloaders

# Extract class names from data directory
print("Extracting class names from data directory...")
_, _, _, classes, _ = get_dataloaders('d:/Plankton/101141/individual_images', batch_size=1, sample_fraction=0.01)

# Save to JSON
import json
output_file = Path('checkpoints/class_names.json')
with open(output_file, 'w') as f:
    json.dump(classes, f, indent=2)

print(f"✅ Saved {len(classes)} class names to {output_file}")
print(f"First 10 classes: {classes[:10]}")
