import numpy as np
import matplotlib.pyplot as plt
import torch
from PIL import Image
from transformers import SamModel, SamProcessor
import cv2

# Load model and processor
model = SamModel.from_pretrained("facebook/sam-vit-base")
processor = SamProcessor.from_pretrained("facebook/sam-vit-base")

# Prepare image
def prepare_image(image_path):
    image = Image.open(image_path).convert("RGB")
    image = np.array(image)
    inputs = processor(images=image, return_tensors="pt")
    return image, inputs

# Extract bounding boxes from the outputs
def extract_bounding_boxes(outputs):
    masks = outputs.pred_masks[0].detach().cpu().numpy()
    bounding_boxes = []
    for mask in masks:
        mask = (mask > 0).astype(np.uint8)  # Ensure mask is binary
        if len(mask.shape) == 3 and mask.shape[2] == 3:  # Ensure mask is single-channel
            mask = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)  # Convert to single-channel
        mask = mask.astype(np.uint8)  # Ensure mask is 8-bit
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            bounding_boxes.append((x, y, x + w, y + h))
    return bounding_boxes

def visualize_bounding_boxes(image, bounding_boxes):
    overlay = image.copy()
    for (x1, y1, x2, y2) in bounding_boxes:
        cv2.rectangle(overlay, (x1, y1), (x2, y2), (0, 255, 0), 2)

    # Display the original image with bounding boxes
    plt.figure(figsize=(10, 10))
    plt.imshow(overlay)
    plt.axis("off")
    plt.show()

# Segment the wireframe image
def segment_wireframe(image_path):
    image, inputs = prepare_image(image_path)

    with torch.no_grad():
        outputs = model(**inputs)

    bounding_boxes = extract_bounding_boxes(outputs)
    return image, bounding_boxes

# Test the model on the wireframe image
wireframe_image_path = "webflow.png"

image, bounding_boxes = segment_wireframe(wireframe_image_path)
visualize_bounding_boxes(image, bounding_boxes)
