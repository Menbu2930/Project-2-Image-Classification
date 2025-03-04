# -*- coding: utf-8 -*-
"""predict.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1w95KGeOSfPB0NnB8lXkfaQa8Zz7g-t3M
"""

import argparse
import json
import torch
from torchvision import models
from PIL import Image
import os
from collections import OrderedDict
import numpy as np

def parse_args(args_dict=None):
    parser = argparse.ArgumentParser(description='Predict flower class')
    parser.add_argument('--checkpoint', type=str, required=True,
                        help='Path to checkpoint file')
    parser.add_argument('--image_path', type=str, required=True,
                        help='Path to image file')
    parser.add_argument('--top_k', type=int, default=5,
                        help='Number of top predictions to show')
    parser.add_argument('--category_names', type=str,
                        help='JSON file mapping categories to names')
    parser.add_argument('--gpu', action='store_true',
                        help='Use GPU if available')

    if args_dict:
        return parser.parse_args(args_dict)
    else:
        return parser.parse_args()

def load_checkpoint(checkpoint_path):
    """Loads a checkpoint"""
    checkpoint = torch.load(checkpoint_path)
    arch = checkpoint['arch']

    if arch == 'resnet50':
        model = models.resnet50(pretrained=True)
    elif arch == 'vgg16':
        model = models.vgg16(pretrained=True)
    elif arch == 'densenet121':
        model = models.densenet121(pretrained=True)

    model.fc = checkpoint['classifier']
    model.load_state_dict(checkpoint['state_dict'])
    model.class_to_idx = checkpoint['class_to_idx']

    return model

def process_image(image_path):
    """Processes an image for prediction"""
    img = Image.open(image_path)

    # Resize
    img = img.resize((256, 256))

    # Center crop
    width = 224
    height = 224
    left = (img.width - width) / 2
    top = (img.height - height) / 2
    right = (img.width + width) / 2
    bottom = (img.height + height) / 2
    img = img.crop((left, top, right, bottom))

    # Convert to numpy array
    np_img = np.array(img) / 255

    # Normalize
    mean = np.array([0.485, 0.456, 0.406])
    std = np.array([0.229, 0.224, 0.225])
    np_img = (np_img - mean) / std

    # Transpose dimensions
    np_img = np_img.transpose((2, 0, 1))

    return torch.from_numpy(np_img)

def predict(image_path, model, device, top_k=5):
    """Makes predictions on an image"""
    model.eval()
    model.to(device)

    # Process image
    image = process_image(image_path)
    image = image.unsqueeze(0).to(device)

    # Get predictions
    with torch.no_grad():
        outputs = model.forward(image)
        ps = torch.exp(outputs)
        top_p, top_class = ps.topk(top_k, dim=1)

    # Convert to lists
    top_p = top_p.cpu().numpy()[0]
    top_class = top_class.cpu().numpy()[0]

    # Map indices to class labels
    idx_to_class = {v: k for k, v in model.class_to_idx.items()}
    top_classes = [idx_to_class[i] for i in top_class]

    return top_p, top_classes

def main(args_dict=None):
    args = parse_args(args_dict)

    # Set up device
    device = torch.device("cuda" if args.gpu and torch.cuda.is_available() else "cpu")
    print(f"\nUsing device: {device}")

    # Load checkpoint
    model = load_checkpoint(args.checkpoint)

    # Load category names if provided
    cat_to_name = None
    if args.category_names:
        with open(args.category_names, 'r') as f:
            cat_to_name = json.load(f)

    # Make prediction
    probs, classes = predict(args.image_path, model, device, args.top_k)

    # Print results
    print("\nPrediction Results:")
    for i in range(len(probs)):
        class_name = cat_to_name[classes[i]] if cat_to_name else classes[i]
        print(f"{i+1}. {class_name}: {probs[i]*100:.2f}%")

if __name__ == "__main__":
    main()

