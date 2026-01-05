# This script performs face recognition on a test image using the pre-generated encodings.

import face_recognition
import cv2
import pickle
import os
import datetime

# --- Configuration ---
ENCODINGS_FILE = "encodings.pickle"
# Path to a test image (e.g., from your 'captures' folder, or a new one)
# Make sure this image contains a face you want to test recognition on.
TEST_IMAGE_PATH = "captures/image_20260103_235604.jpg"
OUTPUT_DIR = "captures"
MODEL = "hog" # "hog" is faster on CPU, "cnn" is more accurate but requires a GPU (if available)
TOLERANCE = 0.6 # Lower numbers mean stricter matches. 0.6 is typical.

# --- Main Recognition Function ---
def recognize_faces_in_image(image_path, encodings_data, output_dir=OUTPUT_DIR):
    # Load the test image
    print(f"Loading test image: {image_path}")
    try:
        image = cv2.imread(image_path)
        if image is None:
            raise FileNotFoundError(f"Image not found or could not be loaded: {image_path}")
    except Exception as e:
        print(f"Error loading image: {e}")
        return

    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # Find all face locations and face encodings in the test image
    print("Finding face locations and encodings in test image...")
    face_locations = face_recognition.face_locations(rgb_image, model=MODEL)
    face_encodings = face_recognition.face_encodings(rgb_image, face_locations)

    # Prepare output image
    output_image = image.copy()
    
    recognized_names = []

    # Loop through each face found in the test image
    for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
        # Compare current face with known faces
        matches = face_recognition.compare_faces(encodings_data["face_encodings"], face_encoding, tolerance=TOLERANCE)
        name = "Unknown"

        # Find the best match
        if True in matches:
            matched_indices = [i for i, b in enumerate(matches) if b]
            face_distances = face_recognition.face_distance(encodings_data["face_encodings"], face_encoding)
            
            # Find the best match among those that matched (lowest distance)
            best_match_index = -1
            min_distance = 1.0 # distances are between 0 and 1
            for i in matched_indices:
                if face_distances[i] < min_distance:
                    min_distance = face_distances[i]
                    best_match_index = i
            
            if best_match_index != -1:
                name = encodings_data["names"][best_match_index]

        recognized_names.append(name)
        print(f"  - Detected face: {name}")

        # Draw a box around the face and label it
        cv2.rectangle(output_image, (left, top), (right, bottom), (0, 255, 0), 2)
        cv2.putText(output_image, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 0.8, (0, 255, 0), 1)

    # Save the output image with detections
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = os.path.join(output_dir, f"detected_{timestamp}.jpg")
    cv2.imwrite(output_filename, output_image)
    print(f"\nSaved image with detections to: {output_filename}")
    
    return recognized_names


# --- Main Execution Block ---
if __name__ == '__main__':
    # Ensure output directory exists
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # Load the known faces data
    print(f"Loading encodings from '{ENCODINGS_FILE}'...")
    try:
        with open(ENCODINGS_FILE, "rb") as f:
            encodings_data = pickle.load(f)
    except FileNotFoundError:
        print(f"Error: '{ENCODINGS_FILE}' not found. Please run encode_faces.py first.")
        exit()
    except Exception as e:
        print(f"Error loading encodings: {e}")
        exit()

    # -- IMPORTANT ---
    # !!! You need to update TEST_IMAGE_PATH to point to an actual image file on your Pi
    # !!! that contains a face you want to test.
    # For example:
    # TEST_IMAGE_PATH = "captures/image_20231027_123456.jpg" 
    # Use one of the images you captured with camera_module.py or a new one.

    if not os.path.exists(TEST_IMAGE_PATH):
        print(f"\nWarning: TEST_IMAGE_PATH '{TEST_IMAGE_PATH}' does not exist.")
        print("Please update the 'TEST_IMAGE_PATH' variable in this script ")
        print("to point to a valid image file on your Raspberry Pi before running.")
    else:
        print("\nStarting face recognition process...")
        recognized_people = recognize_faces_in_image(TEST_IMAGE_PATH, encodings_data)
        if recognized_people:
            print(f"\nFinal recognition summary: {', '.join(recognized_people)}")
        else:
            print("\nNo people detected in the test image.")
