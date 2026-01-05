# This script is based on the face_recognition library examples.
# It encodes all faces found in a directory structure and saves the encodings.
# It now also extracts appearance embeddings using a pre-trained ResNet50.

import face_recognition
import os
import pickle
import glob # For robust image file finding

import torch
import torchvision.transforms as T
import torchvision.models as models
from PIL import Image
import numpy as np

# --- Configuration ---
KNOWN_FACES_DIR = "known_faces"
ENCODINGS_FILE = "encodings.pickle"
FACE_DETECTION_MODEL = "hog"  # "hog" is faster on CPU, "cnn" is more accurate but requires a GPU

# --- ResNet50 Re-ID Model Configuration ---
# Use a pre-trained ResNet50 as our backbone.
REID_MODEL = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V1)
REID_MODEL.fc = torch.nn.Identity() # Remove the final classification layer
REID_MODEL.eval() # Set model to evaluation mode

# Image transformations required by the ResNet50 model
reid_transform = T.Compose([
    T.Resize((256, 128)), # Standard input size for Re-ID
    T.ToTensor(), # Convert to [0,1] range
    T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]) # ImageNet mean/std
])

print(f"Processing images in '{KNOWN_FACES_DIR}'...")

# --- Data Initialization ---
known_face_encodings = []
known_reid_embeddings = []
known_names = []

# --- Image Processing Loop ---
# Loop through each person in the training directory
for name in os.listdir(KNOWN_FACES_DIR):
    person_dir = os.path.join(KNOWN_FACES_DIR, name)
    
    # Skip non-directory files
    if not os.path.isdir(person_dir):
        continue
        
    print(f"Processing images for '{name}'...")

    # Loop through each image of the person using glob for robust file finding
    for image_path in glob.glob(os.path.join(person_dir, "*.jp*g")) + glob.glob(os.path.join(person_dir, "*.png")):
        # Load the image
        try:
            image = face_recognition.load_image_file(image_path)
            pil_image = Image.open(image_path).convert("RGB") # Load with PIL for Re-ID model
        except Exception as e:
            print(f"  - Could not load {os.path.basename(image_path)}: {e}")
            continue

        # Find face locations in the image.
        face_locations = face_recognition.face_locations(image, model=FACE_DETECTION_MODEL)
        
        if len(face_locations) > 0:
            print(f"  - Found face in {os.path.basename(image_path)}. Encoding...")
            
            # --- Extract Face Recognition Encoding ---
            # We take the first face found.
            face_encoding = face_recognition.face_encodings(image, face_locations)[0]
            
            # --- Extract Appearance Embedding (Re-ID) ---
            # Crop the detected face from the PIL image
            top, right, bottom, left = face_locations[0]
            face_crop_pil = pil_image.crop((left, top, right, bottom))
            
            try:
                # Preprocess and extract embedding
                img_tensor = reid_transform(face_crop_pil).unsqueeze(0) # Add batch dimension
                with torch.no_grad():
                    appearance_embedding = REID_MODEL(img_tensor)
                appearance_embedding_np = appearance_embedding.squeeze().numpy()
            except Exception as e:
                print(f"  - Error extracting Re-ID embedding from {os.path.basename(image_path)}: {e}")
                appearance_embedding_np = None # Indicate failure

            if appearance_embedding_np is not None:
                known_face_encodings.append(face_encoding)
                known_reid_embeddings.append(appearance_embedding_np)
                known_names.append(name)
            else:
                print(f"  - Skipping {os.path.basename(image_path)} due to Re-ID embedding error.")

        else:
            print(f"  - No face found in {os.path.basename(image_path)}. Skipping.")

# --- Save the Encodings ---
if len(known_face_encodings) > 0:
    print(f"\nSaving {len(known_face_encodings)} combined encodings to '{ENCODINGS_FILE}'...")

    data = {
        "face_encodings": known_face_encodings,
        "reid_embeddings": known_reid_embeddings,
        "names": known_names
    }
    with open(ENCODINGS_FILE, "wb") as f:
        f.write(pickle.dumps(data))
        
    print("Encodings saved successfully.")
else:
    print("\nNo faces were found and encoded. The 'encodings.pickle' file was not created.")
    print("Please ensure your 'known_faces' directory is structured correctly and contains clear photos.")

print("Processing complete.")
