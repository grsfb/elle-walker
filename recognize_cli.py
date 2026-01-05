# This script performs person detection using YOLOv8, and then attempts
# face recognition, falling back to appearance recognition (Re-ID) if face is unknown.

import cv2
import os
import pickle
import sys
import datetime
import face_recognition
from ultralytics import YOLO
import time

import torch
import torchvision.transforms as T
import torchvision.models as models
from PIL import Image
import numpy as np

# --- Configuration ---
ENCODINGS_FILE = "encodings.pickle"
OUTPUT_DIR = "captures"
YOLO_MODEL = YOLO('yolov8n.pt') # Initialize YOLOv8 model

# --- ResNet50 Re-ID Model Configuration ---
REID_MODEL = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V1)
REID_MODEL.fc = torch.nn.Identity() # Remove the final classification layer
REID_MODEL.eval() # Set model to evaluation mode

# Image transformations required by the ResNet50 model for Re-ID
reid_transform = T.Compose([
    T.Resize((256, 128)), # Standard input size for Re-ID
    T.ToTensor(), # Convert to [0,1] range
    T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]) # ImageNet mean/std
])

# Threshold for Re-ID cosine similarity (adjust as needed based on test_reid.py results)
# A higher threshold means stricter matching.
REID_THRESHOLD = 0.65 

# --- Helper Functions ---
def cosine_similarity(embedding1, embedding2):
    """
    Calculates the cosine similarity between two embeddings.
    """
    return np.dot(embedding1, embedding2) / (np.linalg.norm(embedding1) * np.linalg.norm(embedding2))


# --- Main Recognition Function ---
def perform_recognition(image_path):
    """
    Performs person detection, face recognition, and falls back to appearance recognition.
    """
    # --- Timing Initialization ---
    total_start_time = time.time()
    
    # --- Load known embeddings if available ---
    known_face_encodings = []
    known_reid_embeddings = []
    known_names = []
    
    try:
        with open(ENCODINGS_FILE, "rb") as f:
            data = pickle.load(f)
        known_face_encodings = data.get("face_encodings", [])
        known_reid_embeddings = data.get("reid_embeddings", [])
        known_names = data.get("names", [])
        # print("INFO: Successfully loaded face and Re-ID embeddings.", file=sys.stderr)
    except FileNotFoundError:
        print("WARNING: Embeddings file not found. Will only detect persons.", file=sys.stderr)
    except Exception as e:
        print(f"ERROR: Could not load embeddings file '{ENCODINGS_FILE}': {e}", file=sys.stderr)
        
    has_known_faces = len(known_face_encodings) > 0
    has_known_reid = len(known_reid_embeddings) > 0

    # --- Image and Detection ---
    if not os.path.exists(image_path):
        print(f"ERROR: Image file not found at {image_path}", file=sys.stderr)
        return
        
    image = cv2.imread(image_path)
    if image is None:
        print(f"ERROR: Could not read image file at {image_path}", file=sys.stderr)
        return

    # Convert to RGB for face_recognition and PIL for Re-ID
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(rgb_image)

    t0 = time.time()
    # 1. Find all face locations and encodings in the full image (for initial face recognition)
    all_face_locations = []
    all_face_encodings = []
    if has_known_faces:
        all_face_locations = face_recognition.face_locations(rgb_image, model="hog")
        all_face_encodings = face_recognition.face_encodings(rgb_image, all_face_locations)
    print(f"INFO: All face locations: {all_face_locations}", file=sys.stderr)
    t1 = time.time()

    # 2. Use YOLOv8 to detect all persons in the image
    results = YOLO_MODEL(rgb_image, classes=[0], verbose=False)
    t2 = time.time()
    
    recognized_names_list = [] # List to store names of all recognized persons

    # 3. Loop through each detected person
    for r in results:
        boxes = r.boxes
        for person_box in boxes:
            # Get person's bounding box coordinates
            x1, y1, x2, y2 = person_box.xyxy[0]
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            print(f"INFO: Detected person box: ({x1},{y1},{x2},{y2})", file=sys.stderr)
            
            current_person_name = "Unknown"
            
            # --- Attempt 1: Face Recognition ---
            # Try to associate a face with this person's bounding box
            best_face_match_distance = 1.0 # Lower is better for face_recognition
            best_face_match_name = "Unknown"

            if has_known_faces and all_face_encodings:
                for i, face_location in enumerate(all_face_locations):
                    top, right, bottom, left = face_location
                    face_cx = (left + right) // 2
                    face_cy = (top + bottom) // 2
                    print(f"INFO: Checking face at center ({face_cx},{face_cy}) for person box.", file=sys.stderr)

                    # If face center is inside the person's bounding box
                    if x1 < face_cx < x2 and y1 < face_cy < y2:
                        print(f"INFO: Face center ({face_cx},{face_cy}) is INSIDE person box.", file=sys.stderr)
                        # Compare this face to known face encodings
                        face_distances = face_recognition.face_distance(known_face_encodings, all_face_encodings[i])
                        print(f"INFO: Face distances for match: {face_distances}", file=sys.stderr)
                        # Find the best match (lowest distance)
                        min_distance_index = np.argmin(face_distances)
                        min_distance = face_distances[min_distance_index]

                        if min_distance < best_face_match_distance: # Compare to threshold for actual identity
                            best_face_match_distance = min_distance
                            # Set a threshold for face recognition (e.g., 0.6 is common)
                            if min_distance < 0.6: 
                                best_face_match_name = known_names[min_distance_index]
                                print(f"INFO: Best face match name: {best_face_match_name} (distance: {min_distance:.4f})", file=sys.stderr)
                            else:
                                best_face_match_name = "Unknown" # Too far away from any known face
                                print(f"INFO: Face match 'Unknown' (distance: {min_distance:.4f} >= 0.6)", file=sys.stderr)
                        # Don't break here, one person box could contain multiple faces
                        # but we prioritize the best face match within this person box

            current_person_name = best_face_match_name # Update name based on best face match
            print(f"INFO: Current person name after face recognition: {current_person_name}", file=sys.stderr)

            # --- Attempt 2: Appearance Recognition (Re-ID) if face is Unknown ---
            if current_person_name == "Unknown" and has_known_reid:
                print(f"INFO: Attempting Re-ID for person in box ({x1},{y1},{x2},{y2}).", file=sys.stderr)
                person_crop_pil = pil_image.crop((x1, y1, x2, y2))
                
                try:
                    current_reid_embedding_tensor = reid_transform(person_crop_pil).unsqueeze(0)
                    with torch.no_grad():
                        current_reid_embedding = REID_MODEL(current_reid_embedding_tensor).squeeze().numpy()
                    
                    best_reid_similarity = REID_THRESHOLD
                    best_reid_name = "Unknown"

                    for i, known_emb in enumerate(known_reid_embeddings):
                        similarity = cosine_similarity(current_reid_embedding, known_emb)
                        if similarity > best_reid_similarity:
                            best_reid_similarity = similarity
                            best_reid_name = known_names[i]
                    
                    current_person_name = best_reid_name # Update name if Re-ID found a match
                    print(f"INFO: Current person name after Re-ID: {current_person_name} (similarity: {best_reid_similarity:.4f})", file=sys.stderr)

                except Exception as e:
                    print(f"WARNING: Error during Re-ID for person in box ({x1},{y1},{x2},{y2}): {e}", file=sys.stderr)
            else:
                print(f"INFO: Skipping Re-ID. current_person_name: '{current_person_name}', has_known_reid: {has_known_reid}", file=sys.stderr)


            recognized_names_list.append(current_person_name)
            
            # --- Draw the person's bounding box and name on the original image ---
            cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
            label_y = y1 - 10 if y1 - 10 > 10 else y1 + 10
            cv2.putText(image, current_person_name, (x1, label_y), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

    t3 = time.time()
    # --- Save and Output Results ---
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = os.path.join(OUTPUT_DIR, f"cli_recognition_result_{timestamp}.jpg")
    cv2.imwrite(output_filename, image)
    # --- Print Timing Info to stderr ---
    total_time = t3 - total_start_time
    face_time = t1 - t0
    yolo_time = t2 - t1
    processing_time = t3 - t2
    num_persons = len(recognized_names_list)

    print("\n--- BENCHMARK ---", file=sys.stderr)
    print(f"Face Detection.......: {face_time:.4f}s", file=sys.stderr)
    print(f"YOLO Person Detection: {yolo_time:.4f}s", file=sys.stderr)
    print(f"Processing ({num_persons} persons): {processing_time:.4f}s", file=sys.stderr)
    print("-------------------", file=sys.stderr)
    print(f"TOTAL TIME...........: {total_time:.4f}s", file=sys.stderr)
    print("-------------------\n", file=sys.stderr)
    
    # Print recognized names to stdout
    if recognized_names_list:
        print(",".join(recognized_names_list))
    else:
        print("No persons detected.")

# --- Main Execution Block ---
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python recognize_cli.py <image_path>", file=sys.stderr)
        sys.exit(1)
    
    image_path_arg = sys.argv[1]
    perform_recognition(image_path_arg)

