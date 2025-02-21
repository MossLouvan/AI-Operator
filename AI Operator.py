import torch
from huggingface_hub import InferenceClient 
from PIL import Image
import requests
import numpy as np
import pyautogui  # For clicking
from transformers import CLIPProcessor, CLIPModel

# Load CLIP Model and Processor
model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

# --- Take a Screenshot of the Screen ---
screenshot = pyautogui.screenshot()
screenshot = screenshot.convert("RGB")  # Ensure it's RGB format

# --- Define UI-related Text Prompts ---
instructions = [
    "a login button", 
    "a search bar", 
    "a submit button", 
    "a navigation menu", 
    "a close button"
]

# --- Process Image and Prompts ---
inputs = processor(text=instructions, images=screenshot, return_tensors="pt", padding=True)
outputs = model(**inputs)

# --- Compute Similarity Scores ---
logits_per_image = outputs.logits_per_image  # Image-text similarity scores
probs = logits_per_image.softmax(dim=1)  # Convert to probabilities

# --- Get Most Likely UI Element ---
best_match_index = torch.argmax(probs).item()
best_match_text = instructions[best_match_index]
print(f"Best match: {best_match_text} with confidence {probs[0][best_match_index]:.4f}")

# --- Find Click Position (Advanced) ---
# We would need an object detection model (like DETR or YOLO) to localize elements in the UI.

# --- Simulate Click (Placeholder) ---
if "button" in best_match_text:
    x, y = pyautogui.locateCenterOnScreen("button.png", confidence=0.8)  # Example method
    pyautogui.click(x, y)
    print(f"Clicked on {best_match_text} at ({x}, {y})")
