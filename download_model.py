import os
import urllib.request

# Download the hand landmarker model
model_url = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker.task"
model_path = "hand_landmarker.task"

if not os.path.exists(model_path):
    print(f"Downloading hand landmarker model...")
    urllib.request.urlretrieve(model_url, model_path)
    print(f"Model saved to {model_path}")
else:
    print(f"Model already exists at {model_path}")
