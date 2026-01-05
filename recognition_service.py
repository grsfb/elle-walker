# This file encapsulates the recognition logic into a reusable service.
# It loads all models once upon initialization to avoid reloading on every request.

import cv2
import os
import pickle
import sys
from PIL import Image
import numpy as np
import torch
import torchvision.transforms as T
import torchvision.models as models
import face_recognition
from ultralytics import YOLO

def cosine_similarity(embedding1, embedding2):
    """Calculates the cosine similarity between two embeddings."""
    return np.dot(embedding1, embedding2) / (np.linalg.norm(embedding1) * np.linalg.norm(embedding2))

class RecognitionService:
    def __init__(self, encodings_file="encodings.pickle", yolo_model_path='yolov8n.pt'):
        print("Initializing RecognitionService...")
        
        # --- Model Configuration ---
        self.reid_transform = T.Compose([
            T.Resize((256, 128)),
            T.ToTensor(),
            T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        self.reid_threshold = 0.65

        # --- Load Models (once) ---
        print("Loading YOLO model...")
        self.yolo_model = YOLO(yolo_model_path)
        
        print("Loading Re-ID model...")
        self.reid_model = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V1)
        self.reid_model.fc = torch.nn.Identity()
        self.reid_model.eval()
        
        # --- Load Known Embeddings (once) ---
        print(f"Loading embeddings from '{encodings_file}'...")
        self.known_face_encodings = []
        self.known_reid_embeddings = []
        self.known_names = []
        try:
            with open(encodings_file, "rb") as f:
                data = pickle.load(f)
            self.known_face_encodings = data.get("face_encodings", [])
            self.known_reid_embeddings = data.get("reid_embeddings", [])
            self.known_names = data.get("names", [])
            print(f"Loaded {len(self.known_names)} known persons.")
        except Exception as e:
            print(f"ERROR: RecognitionService could not load embeddings file: {e}", file=sys.stderr)
        
        self.has_known_faces = len(self.known_face_encodings) > 0
        self.has_known_reid = len(self.known_reid_embeddings) > 0
        print("RecognitionService initialized successfully.")

    def recognize(self, image_bgr):
        """
        Performs the full recognition pipeline on a given image.
        :param image_bgr: The image to process in BGR format (from cv2.imread).
        :return: A tuple containing (list_of_recognized_names, annotated_bgr_image).
        """
        annotated_image = image_bgr.copy()
        
        # Convert to RGB for face_recognition and PIL for Re-ID
        rgb_image = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(rgb_image)

        # 1. Use YOLOv8 to detect all objects
        results = self.yolo_model(rgb_image, verbose=False)
        
        recognized_names_list = []

        # 2. Loop through each detected object
        for r in results:
            # Find all face locations once before the loop
            all_face_locations = face_recognition.face_locations(rgb_image, model="hog")
            all_face_encodings = face_recognition.face_encodings(rgb_image, all_face_locations)
            
            for box in r.boxes:
                # --- Get Object Class and Coordinates ---
                x1, y1, x2, y2 = [int(coord) for coord in box.xyxy[0]]
                class_id = int(box.cls[0])
                object_class_name = self.yolo_model.names[class_id]
                
                final_name = object_class_name # Default name is the object class

                # --- Stage 2: If the object is a person, try to identify WHO it is ---
                if object_class_name == 'person':
                    person_name = "Unknown" # Default to Unknown if it's a person
                    
                    # Attempt 1: Face Recognition
                    best_face_match_name = "Unknown"
                    if self.has_known_faces and all_face_encodings:
                        for i, face_location in enumerate(all_face_locations):
                            top, right, bottom, left = face_location
                            face_cx, face_cy = (left + right) // 2, (top + bottom) // 2
                            # Check if the center of the face is within the person's bounding box
                            if x1 < face_cx < x2 and y1 < face_cy < y2:
                                face_distances = face_recognition.face_distance(self.known_face_encodings, all_face_encodings[i])
                                min_distance_index = np.argmin(face_distances)
                                if face_distances[min_distance_index] < 0.6:
                                    best_face_match_name = self.known_names[min_distance_index]
                                    break # Found a match, no need to check other faces for this person
                        person_name = best_face_match_name

                    # Attempt 2: Re-ID if face recognition failed
                    if person_name == "Unknown" and self.has_known_reid:
                        person_crop_pil = pil_image.crop((x1, y1, x2, y2))
                        try:
                            embedding_tensor = self.reid_transform(person_crop_pil).unsqueeze(0)
                            with torch.no_grad():
                                current_embedding = self.reid_model(embedding_tensor).squeeze().numpy()
                            
                            best_reid_name = "Unknown"
                            best_reid_similarity = self.reid_threshold
                            for i, known_emb in enumerate(self.known_reid_embeddings):
                                similarity = cosine_similarity(current_embedding, known_emb)
                                if similarity > best_reid_similarity:
                                    best_reid_similarity = similarity
                                    best_reid_name = self.known_names[i]
                            person_name = best_reid_name
                        except Exception as e:
                            print(f"WARNING: Error during Re-ID: {e}", file=sys.stderr)
                    
                    # If a specific person was identified, use their name
                    if person_name != "Unknown":
                        final_name = person_name
                    else:
                        final_name = "Unknown Person" # More descriptive than just 'person'

                recognized_names_list.append(final_name)
                
                # --- Draw annotations on the image ---
                # Use different colors for recognized people vs. other objects
                color = (0, 255, 0) if final_name not in ["Unknown Person", object_class_name] else (255, 128, 0)
                cv2.rectangle(annotated_image, (x1, y1), (x2, y2), color, 2)
                label_y = y1 - 10 if y1 - 10 > 10 else y1 + 10
                cv2.putText(annotated_image, final_name, (x1, label_y), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

        return recognized_names_list, annotated_image
