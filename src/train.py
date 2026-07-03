import torch
import torch.nn as nn
import torch.optim as optim
from tqdm import tqdm
import os
import argparse
from data_loader import get_dataloaders
from model import get_model
from sklearn.metrics import classification_report

def train_one_epoch(model, loader, criterion, optimizer, scaler, device):
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0
    
    pbar = tqdm(loader, desc="Training")
    for images, labels in pbar:
        images, labels = images.to(device), labels.to(device)
        
        optimizer.zero_grad()
        
        # Mixed Precision (only if CUDA is available)
        if device.type == 'cuda':
            with torch.amp.autocast('cuda'):
                outputs = model(images)
                loss = criterion(outputs, labels)
            
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
        else:
            # Standard precision for CPU
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
        
        running_loss += loss.item()
        _, predicted = outputs.max(1)
        total += labels.size(0)
        correct += predicted.eq(labels).sum().item()
        
        pbar.set_postfix({'loss': running_loss/total, 'acc': 100.*correct/total})
        
    return running_loss / len(loader), 100. * correct / total

def validate(model, loader, criterion, device):
    model.eval()
    running_loss = 0.0
    correct = 0
    total = 0
    
    with torch.no_grad():
        for images, labels in loader:
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            loss = criterion(outputs, labels)
            
            running_loss += loss.item()
            _, predicted = outputs.max(1)
            total += labels.size(0)
            correct += predicted.eq(labels).sum().item()
            
    return running_loss / len(loader), 100. * correct / total

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_dir', type=str, default='d:/Plankton/101141/individual_images')
    parser.add_argument('--epochs', type=int, default=20)
    parser.add_argument('--batch_size', type=int, default=32)
    parser.add_argument('--lr', type=float, default=0.001)
    parser.add_argument('--save_dir', type=str, default='checkpoints')
    parser.add_argument('--sample_fraction', type=float, default=1.0, help='Fraction of data to use (0.0 to 1.0)')
    args = parser.parse_args()
    
    os.makedirs(args.save_dir, exist_ok=True)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")
    
    # Data Loaders
    train_loader, val_loader, test_loader, classes, class_weights = get_dataloaders(args.data_dir, args.batch_size, sample_fraction=args.sample_fraction)
    print(f"Classes: {len(classes)}")
    
    # Model
    model = get_model(len(classes)).to(device)
    
    # Loss and Optimizer
    if class_weights is not None:
        criterion = nn.CrossEntropyLoss(weight=class_weights.to(device))
    else:
        criterion = nn.CrossEntropyLoss()
        
    optimizer = optim.Adam(model.parameters(), lr=args.lr)
    
    # Scaler only needed for CUDA
    scaler = torch.amp.GradScaler('cuda') if device.type == 'cuda' else None
    
    best_acc = 0.0
    
    for epoch in range(args.epochs):
        print(f"Epoch {epoch+1}/{args.epochs}")
        train_loss, train_acc = train_one_epoch(model, train_loader, criterion, optimizer, scaler, device)
        val_loss, val_acc = validate(model, val_loader, criterion, device)
        
        print(f"Train Loss: {train_loss:.4f} | Train Acc: {train_acc:.2f}%")
        print(f"Val Loss: {val_loss:.4f} | Val Acc: {val_acc:.2f}%")
        
        if val_acc > best_acc:
            best_acc = val_acc
            torch.save(model.state_dict(), os.path.join(args.save_dir, 'best_model.pth'))
            print("Saved best model!")
            
    print("Training Complete.")

if __name__ == '__main__':
    main()
