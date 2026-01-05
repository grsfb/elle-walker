# This script trains an LBPH face recognizer using images in a directory.
# It does NOT require the 'dlib' or 'face_recognition' libraries.

import cv2
import os
import numpy as np
from PIL import Image
import pickle

# --- Configuration ---
KNOWN_FACES_DIR = "known_faces"
TRAINER_FILE = "lbph_trainer.yml"

# --- Initialization ---
# We will use a Haar Cascade for face detection, which is built into OpenCV
cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
face_detector = cv2.CascadeClassifier(cascade_path)

# Create the LBPH Face Recognizer
# Note: You may need to run 'pip install opencv-contrib-python' for this to work
recognizer = cv2.face.LBPHFaceRecognizer_create()

def get_images_and_labels(path):
    """
    Reads images from the directory structure and prepares them for training.
    """
    image_paths = []
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith(('.png', '.jpg', '.jpeg')):
                image_paths.append(os.path.join(root, file))

    face_samples = []
    ids = []
    
    # Create a mapping from name (string) to id (integer)
    label_ids = {}
    current_id = 0

    print("Preparing images for training...")

    for image_path in image_paths:
        # Get the person's name from the directory name
        name = os.path.basename(os.path.dirname(image_path)).replace(" ", "-").lower()
        
        if name not in label_ids:
            label_ids[name] = current_id
            current_id += 1
        id_ = label_ids[name]

        # Open the image and convert to grayscale
        try:
            pil_image = Image.open(image_path).convert('L') # 'L' is grayscale
            image_np = np.array(pil_image, 'uint8')
        except Exception as e:
            print(f"  - Could not process {image_path}: {e}")
            continue

        # Detect faces in the image
        faces = face_detector.detectMultiScale(image_np, scaleFactor=1.1, minNeighbors=5)

        for (x, y, w, h) in faces:
            # Add the face ROI (Region of Interest) to our samples list
            face_samples.append(image_np[y:y+h, x:x+w])
            ids.append(id_)
            print(f"  - Trained on face from {os.path.basename(image_path)} for ID: {id_} ({name})")

    # We need to save the name-to-id mapping for later use during recognition
    # We will save it alongside the trainer file.
    with open('label_ids.pickle', 'wb') as f:
        pickle.dump(label_ids, f)

    return face_samples, ids

if __name__ == '__main__':
    
    # Check if the known_faces directory exists
    if not os.path.isdir(KNOWN_FACES_DIR):
        print(f"Error: Directory '{KNOWN_FACES_DIR}' not found.")
        print("Please create it and add subdirectories for each person with their photos.")
    else:
        faces, ids = get_images_and_labels(KNOWN_FACES_DIR)
        
        if len(faces) > 0:
            print("\nTraining the face recognizer...")
            # Train the recognizer with our face samples and their corresponding IDs
            recognizer.train(faces, np.array(ids))

            # Save the trained model to a file
            recognizer.write(TRAINER_FILE)
            
            print(f"\nTraining complete. {len(np.unique(ids))} people trained.")
            print(f"Model saved to '{TRAINER_FILE}'")
            print(f"Label IDs saved to 'label_ids.pickle'")
        else:
            print("\nNo faces found to train. Please check your image folders.")
