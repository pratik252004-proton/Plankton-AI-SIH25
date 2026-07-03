import os
import torch
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from PIL import Image
import numpy as np
from collections import Counter

# Increase PIL's decompression bomb limit for large microscopy images
Image.MAX_IMAGE_PIXELS = None  # Disable the limit (images are resized to 224x224 anyway)

class PlanktonDataset(Dataset):
    def __init__(self, root_dir, split='train', transform=None, sample_fraction=1.0):
        self.root_dir = root_dir
        self.transform = transform
        self.split = split
        self.sample_fraction = sample_fraction
        self.classes = []
        self.class_to_folder = {}
        self.image_paths = []
        self.labels = []
        
        # Artifact keywords to ignore
        # Added 'bract' as it is a part/artifact often not counted as an individual organism in this context
        self.ignore_keywords = ["badfocus", "bubble", "artefact", "dead", "part_", "detritus", "bract"]
        
        self._load_dataset()
        
    def _load_dataset(self):
        all_folders = sorted(os.listdir(self.root_dir))
        
        temp_paths = []
        temp_labels = []
        
        class_idx = 0
        
        for folder_name in all_folders:
            # Check if directory
            if not os.path.isdir(os.path.join(self.root_dir, folder_name)):
                continue
                
            # Check ignore keywords
            if any(k in folder_name.lower() for k in self.ignore_keywords):
                continue
                
            # Clean class name (remove __ID suffix)
            # e.g., Acartiidae__61996 -> Acartiidae
            clean_name = folder_name.split('__')[0]
            
            # Handle duplicates if multiple folders map to same clean name (unlikely but good to be safe)
            if clean_name not in self.classes:
                self.classes.append(clean_name)
                self.class_to_folder[clean_name] = []
            
            self.class_to_folder[clean_name].append(folder_name)
            
            # Use the index of the clean name in self.classes as the label
            current_label = self.classes.index(clean_name)
            
            class_dir = os.path.join(self.root_dir, folder_name)
            for img_name in os.listdir(class_dir):
                if img_name.lower().endswith(('.png', '.jpg', '.jpeg', '.tif', '.tiff')):
                    temp_paths.append(os.path.join(class_dir, img_name))
                    temp_labels.append(current_label)
                    
        # Simple split logic (deterministic based on index)
        # 70% Train, 15% Val, 15% Test
        total_len = len(temp_paths)
        indices = list(range(total_len))
        # Shuffle with seed for reproducibility
        np.random.seed(42)
        np.random.shuffle(indices)
        
        # Apply sampling if requested
        if self.sample_fraction < 1.0:
            sample_size = int(total_len * self.sample_fraction)
            indices = indices[:sample_size]
            total_len = sample_size
        
        train_end = int(0.7 * total_len)
        val_end = int(0.85 * total_len)
        
        if self.split == 'train':
            self.indices = indices[:train_end]
        elif self.split == 'val':
            self.indices = indices[train_end:val_end]
        else:
            self.indices = indices[val_end:]
            
        self.image_paths = [temp_paths[i] for i in self.indices]
        self.labels = [temp_labels[i] for i in self.indices]

    def __len__(self):
        return len(self.image_paths)

    def __getitem__(self, idx):
        img_path = self.image_paths[idx]
        label = self.labels[idx]
        
        # Open image and convert to RGB (handling grayscale)
        image = Image.open(img_path).convert("RGB")
        
        if self.transform:
            image = self.transform(image)
            
        return image, label

    def get_class_weights(self):
        # Compute weights based on training set
        if self.split != 'train':
            return None
            
        counter = Counter(self.labels)
        total = len(self.labels)
        weights = []
        for i in range(len(self.classes)):
            count = counter.get(i, 0)
            if count > 0:
                weights.append(total / (len(self.classes) * count))
            else:
                weights.append(0) # Or handle rare classes differently
        return torch.FloatTensor(weights)

def get_transforms(split):
    if split == 'train':
        return transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.RandomRotation(15),
            transforms.RandomHorizontalFlip(),
            transforms.RandomVerticalFlip(),
            transforms.ColorJitter(brightness=0.2, contrast=0.2), # RandomContrast/Brightness
            transforms.RandomApply([transforms.GaussianBlur(3)], p=0.1),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
    else:
        return transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])

def get_dataloaders(root_dir, batch_size=32, num_workers=4, sample_fraction=1.0):
    train_dataset = PlanktonDataset(root_dir, split='train', transform=get_transforms('train'), sample_fraction=sample_fraction)
    val_dataset = PlanktonDataset(root_dir, split='val', transform=get_transforms('val'), sample_fraction=sample_fraction)
    test_dataset = PlanktonDataset(root_dir, split='test', transform=get_transforms('test'), sample_fraction=sample_fraction)
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=num_workers, pin_memory=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=num_workers, pin_memory=True)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False, num_workers=num_workers, pin_memory=True)
    
    return train_loader, val_loader, test_loader, train_dataset.classes, train_dataset.get_class_weights()
