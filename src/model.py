import torch
import torch.nn as nn
from torchvision import models

def get_model(num_classes, pretrained=True):
    # Load MobileNetV3 Small
    # Using 'DEFAULT' weights which are the best available
    weights = models.MobileNet_V3_Small_Weights.DEFAULT if pretrained else None
    model = models.mobilenet_v3_small(weights=weights)
    
    # Modify the classifier head
    # MobileNetV3 small classifier structure:
    # (classifier): Sequential(
    #   (0): Linear(in_features=576, out_features=1024, bias=True)
    #   (1): Hardswish()
    #   (2): Dropout(p=0.2, inplace=True)
    #   (3): Linear(in_features=1024, out_features=1000, bias=True)
    # )
    
    in_features = model.classifier[3].in_features
    model.classifier[3] = nn.Linear(in_features, num_classes)
    
    return model
