import torch
import torchvision.transforms as T
import torchvision.models as models # Still needed for T.Normalize
from PIL import Image
import numpy as np
import os
import glob
import sys # New import for sys.path

# --- Configuration ---
# Path to the cloned deep-person-reid repository for model definition
REID_REPO_PATH = os.path.join(os.getcwd(), 'reid_models')
# Add the path to sys.path so osnet.py can be imported
sys.path.insert(0, os.path.join(REID_REPO_PATH, 'torchreid', 'models'))

# Import the OSNet model architecture
from osnet import osnet_x0_25

# Path to the downloaded pre-trained weights
WEIGHTS_PATH = os.path.join(REID_REPO_PATH, 'osnet_x0_25_market1501.pth')

print("Loading specialized OSNet Re-ID model...")
# Instantiate OSNet model (num_classes doesn't matter for feature extraction)
REID_MODEL = osnet_x0_25(num_classes=1000, pretrained=False) 
# Load the pre-trained weights
try:
    state_dict = torch.load(WEIGHTS_PATH, map_location='cpu')
    
    # Remove 'classifier' keys if present to avoid loading into nn.Identity (if replaced) or for strict=True
    new_state_dict = {k: v for k, v in state_dict.items() if 'classifier' not in k}
    
    # Load state dict, allowing for strict=False if the model definition doesn't have a classifier (e.g. if we remove it first)
    REID_MODEL.load_state_dict(new_state_dict, strict=False) 
    print(f"Loaded weights from {WEIGHTS_PATH}")
except FileNotFoundError:
    print(f"ERROR: Weights file not found at {WEIGHTS_PATH}. Please ensure it is in the 'reid_models' folder.", file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(f"ERROR: Could not load OSNet weights: {e}", file=sys.stderr)
    sys.exit(1)

# Crucial step for feature extraction: Replace the classifier with an identity layer
# This ensures the model outputs the feature vector directly.
REID_MODEL.classifier = torch.nn.Identity()

REID_MODEL.eval() # Set model to evaluation mode
print("Specialized OSNet Re-ID model loaded successfully for feature extraction.")

# Image transformations required by OSNet
transform = T.Compose([
    T.Resize((256, 128)), # Standard input size for OSNet
    T.ToTensor(),
    T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

# --- Helper Functions ---
def extract_embedding(image_path):
    """
    Extracts a feature embedding from a person's image using the Re-ID model.
    """
    if not os.path.exists(image_path):
        print(f"Error: Image file not found at {image_path}")
        return None
    
    try:
        img = Image.open(image_path).convert("RGB")
        img_tensor = transform(img).unsqueeze(0) # Add batch dimension
        
        with torch.no_grad(): # No need to calculate gradients for inference
            embedding = REID_MODEL(img_tensor)
        return embedding.squeeze().numpy() # Convert to numpy array
    except Exception as e:
        print(f"Error extracting embedding from {image_path}: {e}")
        return None

def cosine_similarity(embedding1, embedding2):
    """
    Calculates the cosine similarity between two embeddings.
    """
    return np.dot(embedding1, embedding2) / (np.linalg.norm(embedding1) * np.linalg.norm(embedding2))

# --- Main Test Execution ---
if __name__ == '__main__':
    KNOWN_FACES_DIR = "known_faces"
    
    print("--- Automatically Finding Test Images ---")
    try:
        if not os.path.isdir(KNOWN_FACES_DIR):
            raise FileNotFoundError(f"Directory '{KNOWN_FACES_DIR}' not found. Please create it and add images.")

        people = sorted([d for d in os.listdir(KNOWN_FACES_DIR) if os.path.isdir(os.path.join(KNOWN_FACES_DIR, d))])
        if len(people) < 3:
            raise ValueError(f"Need at least three people in '{KNOWN_FACES_DIR}' for a comprehensive comparison. Found {len(people)}.")

        # Get images for Person 1
        person1_name = people[0]
        person1_images = sorted(glob.glob(os.path.join(KNOWN_FACES_DIR, person1_name, "*.jp*g")) + \
                                glob.glob(os.path.join(KNOWN_FACES_DIR, person1_name, "*.png")))
        if len(person1_images) < 2:
            raise ValueError(f"Need at least two images for '{person1_name}' to perform a same-person comparison.")
        image_path1_1 = person1_images[0] # First image of person 1
        image_path1_2 = person1_images[1] # Second image of person 1

        # Get images for Person 2
        person2_name = people[1]
        person2_images = sorted(glob.glob(os.path.join(KNOWN_FACES_DIR, person2_name, "*.jp*g")) + \
                                glob.glob(os.path.join(KNOWN_FACES_DIR, person2_name, "*.png")))
        if not person2_images:
            raise ValueError(f"No images found for '{person2_name}'.")
        image_path2_1 = person2_images[0] # First image of person 2

        # Get images for Person 3
        person3_name = people[2]
        person3_images = sorted(glob.glob(os.path.join(KNOWN_FACES_DIR, person3_name, "*.jp*g")) + \
                                glob.glob(os.path.join(KNOWN_FACES_DIR, person3_name, "*.png")))
        if not person3_images:
            raise ValueError(f"No images found for '{person3_name}'.")
        image_path3_1 = person3_images[0] # First image of person 3


        print(f"Test Cases:")
        print(f"  Same Person: '{person1_name}' (1) vs '{person1_name}' (2)")
        print(f"  Different People: '{person1_name}' (1) vs '{person2_name}' (1)")
        print(f"  Different People: '{person1_name}' (1) vs '{person3_name}' (1)")
        print(f"  Different People: '{person2_name}' (1) vs '{person3_name}' (1)")

    except (FileNotFoundError, ValueError) as e:
        print(f"\nERROR: Could not set up test images automatically: {e}", file=sys.stderr)
        print("Please ensure your 'known_faces' directory is set up correctly with at least three people, each with at least one image (and the first person with at least two images).", file=sys.stderr)
        sys.exit(1)

    print("\n--- Running Re-ID Test ---")

    # Extract embeddings needed
    emb1_1 = extract_embedding(image_path1_1)
    emb1_2 = extract_embedding(image_path1_2)
    emb2_1 = extract_embedding(image_path2_1)
    emb3_1 = extract_embedding(image_path3_1)

    # Comparisons
    print(f"\nComparing {os.path.basename(image_path1_1)} ({person1_name}) and {os.path.basename(image_path1_2)} ({person1_name}) (expected: high similarity)")
    if emb1_1 is not None and emb1_2 is not None:
        similarity = cosine_similarity(emb1_1, emb1_2)
        print(f"Similarity: {similarity:.4f}")
    else:
        print("Could not extract embeddings for comparison.")

    print(f"\nComparing {os.path.basename(image_path1_1)} ({person1_name}) and {os.path.basename(image_path2_1)} ({person2_name}) (expected: low similarity)")
    if emb1_1 is not None and emb2_1 is not None:
        similarity = cosine_similarity(emb1_1, emb2_1)
        print(f"Similarity: {similarity:.4f}")
    else:
        print("Could not extract embeddings for comparison.")

    print(f"\nComparing {os.path.basename(image_path1_1)} ({person1_name}) and {os.path.basename(image_path3_1)} ({person3_name}) (expected: low similarity)")
    if emb1_1 is not None and emb3_1 is not None:
        similarity = cosine_similarity(emb1_1, emb3_1)
        print(f"Similarity: {similarity:.4f}")
    else:
        print("Could not extract embeddings for comparison.")
    
    print(f"\nComparing {os.path.basename(image_path2_1)} ({person2_name}) and {os.path.basename(image_path3_1)} ({person3_name}) (expected: low similarity)")
    if emb2_1 is not None and emb3_1 is not None:
        similarity = cosine_similarity(emb2_1, emb3_1)
        print(f"Similarity: {similarity:.4f}")
    else:
        print("Could not extract embeddings for comparison.")

    print("\n--- Test Complete ---")
