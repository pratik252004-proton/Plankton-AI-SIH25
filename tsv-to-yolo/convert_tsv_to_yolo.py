"""
TSV to YOLO Dataset Converter
Converts EcoTaxa TSV morphological data to YOLO object detection format
"""
import pandas as pd
import numpy as np
from pathlib import Path
import shutil
from tqdm import tqdm
import json


class TSVToYOLOConverter:
    """Convert EcoTaxa TSV data to YOLO format using morphological measurements"""
    
    def __init__(self, tsv_path, image_dir, output_dir, image_size=(224, 224)):
        """
        Initialize converter
        
        Args:
            tsv_path: Path to TSV file with morphological data
            image_dir: Directory containing plankton images
            output_dir: Output directory for YOLO dataset
            image_size: Expected image dimensions (width, height)
        """
        self.tsv_path = Path(tsv_path)
        self.image_dir = Path(image_dir)
        self.output_dir = Path(output_dir)
        self.image_width, self.image_height = image_size
        
        # Create output directories
        self.create_output_structure()
        
        # Load TSV data
        print(f"Loading TSV data from {tsv_path}...")
        self.df = pd.read_csv(tsv_path, sep='\t', low_memory=False)
        print(f"Loaded {len(self.df)} records")
        
        # Get unique species
        self.species_list = self.get_unique_species()
        self.class_mapping = {species: idx for idx, species in enumerate(self.species_list)}
        
        print(f"Found {len(self.species_list)} unique species")
    
    def create_output_structure(self):
        """Create YOLO dataset directory structure"""
        dirs = [
            self.output_dir / 'images' / 'train',
            self.output_dir / 'images' / 'val',
            self.output_dir / 'labels' / 'train',
            self.output_dir / 'labels' / 'val'
        ]
        
        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        print(f"Created output directory structure at {self.output_dir}")
    
    def get_unique_species(self):
        """Extract unique species from TSV"""
        # Filter out non-living and artifacts
        living_df = self.df[
            (~self.df['object_taxon'].str.contains('detritus', na=False)) &
            (~self.df['object_taxon'].str.contains('artefact', na=False)) &
            (~self.df['object_taxon'].str.contains('badfocus', na=False)) &
            (~self.df['object_taxon'].str.contains('fiber', na=False)) &
            (~self.df['object_taxon'].str.contains('bubble', na=False))
        ]
        
        species = sorted(living_df['object_taxon'].dropna().unique())
        return species
    
    def generate_bbox_from_morphology(self, row):
        """
        Generate YOLO bounding box from morphological measurements
        
        Args:
            row: DataFrame row with morphological data
            
        Returns:
            (x_center, y_center, width, height) in YOLO format (normalized 0-1)
        """
        try:
            # Get morphological measurements (in pixels)
            major_axis = float(row.get('object_major', 0))
            minor_axis = float(row.get('object_minor', 0))
            area = float(row.get('object_area', 0))
            
            # If measurements are missing or invalid, use defaults
            if major_axis <= 0 or minor_axis <= 0:
                # Estimate from area if available
                if area > 0:
                    # Assume circular organism
                    diameter = np.sqrt(4 * area / np.pi)
                    major_axis = diameter
                    minor_axis = diameter
                else:
                    # Use conservative default (60% of image)
                    major_axis = self.image_width * 0.6
                    minor_axis = self.image_height * 0.6
            
            # Add margin (10% on each side)
            margin = 1.2
            bbox_width = (major_axis * margin) / self.image_width
            bbox_height = (minor_axis * margin) / self.image_height
            
            # Ensure bounding box is within image bounds
            bbox_width = min(bbox_width, 0.95)
            bbox_height = min(bbox_height, 0.95)
            
            # Assume organism is centered (common in plankton imaging)
            x_center = 0.5
            y_center = 0.5
            
            return (x_center, y_center, bbox_width, bbox_height)
            
        except Exception as e:
            print(f"Warning: Error generating bbox for {row.get('object_id', 'unknown')}: {e}")
            # Return default centered box
            return (0.5, 0.5, 0.7, 0.7)
    
    def find_image_file(self, object_id):
        """
        Find image file corresponding to object_id
        
        Args:
            object_id: Object identifier from TSV
            
        Returns:
            Path to image file or None if not found
        """
        # Common image extensions
        extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff']
        
        # Try to find image with object_id as filename
        for ext in extensions:
            # Try exact match
            img_path = self.image_dir / f"{object_id}{ext}"
            if img_path.exists():
                return img_path
            
            # Try case-insensitive search in subdirectories
            for img_file in self.image_dir.rglob(f"*{object_id}*{ext}"):
                return img_file
        
        return None
    
    def convert_dataset(self, train_split=0.8, max_samples_per_class=None):
        """
        Convert TSV data to YOLO format
        
        Args:
            train_split: Fraction of data for training (rest for validation)
            max_samples_per_class: Maximum samples per class (None = unlimited)
        """
        print("\n" + "="*60)
        print("Starting TSV to YOLO Conversion")
        print("="*60)
        
        stats = {
            'total_processed': 0,
            'images_found': 0,
            'images_not_found': 0,
            'train_samples': 0,
            'val_samples': 0,
            'per_class': {}
        }
        
        # Process each species
        for species in tqdm(self.species_list, desc="Processing species"):
            class_id = self.class_mapping[species]
            
            # Get all samples for this species
            species_df = self.df[self.df['object_taxon'] == species]
            
            # Limit samples if specified
            if max_samples_per_class and len(species_df) > max_samples_per_class:
                species_df = species_df.sample(n=max_samples_per_class, random_state=42)
            
            # Split into train/val
            n_train = int(len(species_df) * train_split)
            train_df = species_df.iloc[:n_train]
            val_df = species_df.iloc[n_train:]
            
            # Process training samples
            train_count = self.process_samples(train_df, class_id, 'train')
            val_count = self.process_samples(val_df, class_id, 'val')
            
            stats['per_class'][species] = {
                'train': train_count,
                'val': val_count,
                'total': train_count + val_count
            }
            stats['train_samples'] += train_count
            stats['val_samples'] += val_count
        
        # Create data.yaml
        self.create_data_yaml()
        
        # Save statistics
        self.save_statistics(stats)
        
        print("\n" + "="*60)
        print("Conversion Complete!")
        print("="*60)
        print(f"Train samples: {stats['train_samples']}")
        print(f"Val samples: {stats['val_samples']}")
        print(f"Total samples: {stats['train_samples'] + stats['val_samples']}")
        print(f"Dataset saved to: {self.output_dir}")
        print("="*60)
    
    def process_samples(self, df, class_id, split):
        """
        Process samples for a specific split
        
        Args:
            df: DataFrame with samples
            class_id: Class ID for YOLO
            split: 'train' or 'val'
            
        Returns:
            Number of successfully processed samples
        """
        count = 0
        
        for idx, row in df.iterrows():
            object_id = row['object_id']
            
            # Find corresponding image
            img_path = self.find_image_file(object_id)
            
            if img_path is None:
                continue
            
            # Generate bounding box from morphology
            bbox = self.generate_bbox_from_morphology(row)
            
            # Copy image to output directory
            output_img_name = f"{object_id}{img_path.suffix}"
            output_img_path = self.output_dir / 'images' / split / output_img_name
            
            try:
                shutil.copy2(img_path, output_img_path)
            except Exception as e:
                print(f"Error copying {img_path}: {e}")
                continue
            
            # Create YOLO annotation
            output_label_path = self.output_dir / 'labels' / split / f"{object_id}.txt"
            
            with open(output_label_path, 'w') as f:
                # YOLO format: class_id x_center y_center width height
                f.write(f"{class_id} {bbox[0]:.6f} {bbox[1]:.6f} {bbox[2]:.6f} {bbox[3]:.6f}\n")
            
            count += 1
        
        return count
    
    def create_data_yaml(self):
        """Create data.yaml configuration file for YOLO"""
        yaml_content = f"""# Plankton Object Detection Dataset (from TSV)
path: {self.output_dir.absolute()}
train: images/train
val: images/val

# Classes
nc: {len(self.species_list)}
names: {self.species_list}
"""
        
        yaml_path = self.output_dir / 'data.yaml'
        with open(yaml_path, 'w') as f:
            f.write(yaml_content)
        
        print(f"\nCreated data.yaml at {yaml_path}")
    
    def save_statistics(self, stats):
        """Save conversion statistics to JSON"""
        stats_path = self.output_dir / 'conversion_stats.json'
        
        with open(stats_path, 'w') as f:
            json.dump(stats, f, indent=2)
        
        print(f"Saved statistics to {stats_path}")


def main():
    """Main conversion function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Convert EcoTaxa TSV to YOLO format')
    parser.add_argument('--tsv', type=str, required=True, help='Path to TSV file')
    parser.add_argument('--images', type=str, required=True, help='Directory with images')
    parser.add_argument('--output', type=str, default='yolo_dataset', help='Output directory')
    parser.add_argument('--image-size', type=int, nargs=2, default=[224, 224], help='Image size (width height)')
    parser.add_argument('--train-split', type=float, default=0.8, help='Training split ratio')
    parser.add_argument('--max-per-class', type=int, default=None, help='Max samples per class')
    
    args = parser.parse_args()
    
    # Create converter
    converter = TSVToYOLOConverter(
        tsv_path=args.tsv,
        image_dir=args.images,
        output_dir=args.output,
        image_size=tuple(args.image_size)
    )
    
    # Convert dataset
    converter.convert_dataset(
        train_split=args.train_split,
        max_samples_per_class=args.max_per_class
    )


if __name__ == "__main__":
    main()
