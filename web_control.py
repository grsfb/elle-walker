from flask import Flask, render_template, redirect, url_for, jsonify, send_from_directory
from motor_control import ScoutBot
from camera_module import ScoutCamera
from recognition_service import RecognitionService # <-- IMPORT
import atexit
import subprocess
import os
import sys
import threading
from uuid import uuid4
import cv2 # <-- IMPORT
import datetime # <-- IMPORT

# --- Initialization ---
app = Flask(__name__)
CAPTURE_DIR = "captures"

# In-memory store for background job statuses
summary_jobs = {}

# Initialize Hardware Control Objects & Recognition Service
scout_bot = ScoutBot()
scout_camera = ScoutCamera()
recognition_service = RecognitionService() # <-- CREATE SINGLE INSTANCE

# Register cleanup functions
def cleanup_all():
    print("Cleaning up resources...")
    scout_bot.cleanup()
    scout_camera.cleanup()
atexit.register(cleanup_all)


def run_summary_in_background(job_id, image_path):
    """
    Runs the summarizer script in a background thread and updates the job status.
    """
    print(f"[{job_id}] Starting background summarization for {image_path}")
    summary_jobs[job_id] = {'status': 'processing', 'summary': 'Summarizing...'}
    
    try:
        summarizer_venv_python = os.path.expanduser("~/elle-walker/.llm_venv/bin/python")
        summarizer_script_path = os.path.expanduser("~/elle-walker/summarize_cli.py")
        
        summary_result = subprocess.run(
            [summarizer_venv_python, summarizer_script_path, image_path],
            capture_output=True, text=True, check=True, timeout=300 # 5 minute timeout
        )
        summary = summary_result.stdout.strip()
        summary_jobs[job_id] = {'status': 'completed', 'summary': summary}
        print(f"[{job_id}] Summarization completed.")
        
    except subprocess.TimeoutExpired:
        print(f"[{job_id}] Summarization timed out.", file=sys.stderr)
        summary_jobs[job_id] = {'status': 'error', 'summary': 'Error: Summarization timed out.'}
    except subprocess.CalledProcessError as e:
        # Capture stderr to get the error message from the script
        error_output = e.stderr.strip() if e.stderr else "An unknown error occurred in the script."
        print(f"[{job_id}] Summarization script failed: {error_output}", file=sys.stderr)
        summary_jobs[job_id] = {'status': 'error', 'summary': f"Error: {error_output}"}
    except Exception as e:
        print(f"[{job_id}] An unexpected error occurred in background task: {e}", file=sys.stderr)
        summary_jobs[job_id] = {'status': 'error', 'summary': f"An unexpected error occurred: {e}"}


# --- Web Routes ---
@app.route('/')
def index():
    return render_template('index.html')

# Route to serve images from the 'captures' directory
@app.route('/captures/<path:filename>')
def serve_capture(filename):
    return send_from_directory(CAPTURE_DIR, filename)

# --- Motor Control Routes ---
@app.route('/forward', methods=['POST'])
def forward():
    scout_bot.forward()
    return redirect(url_for('index'))

@app.route('/backward', methods=['POST'])
def backward():
    scout_bot.backward()
    return redirect(url_for('index'))

@app.route('/left', methods=['POST'])
def left():
    scout_bot.left()
    return redirect(url_for('index'))

@app.route('/right', methods=['POST'])
def right():
    scout_bot.right()
    return redirect(url_for('index'))

@app.route('/stop', methods=['POST'])
def stop():
    scout_bot.stop()
    return redirect(url_for('index'))

# --- Main Application Route ---
@app.route('/find_person', methods=['POST'])
def find_person():
    print("\n--- Initiating Find Sequence (Optimized) ---")
    
    try:
        # 1. Capture a new image
        raw_image_path = scout_camera.capture_image()
        print(f"Image captured: {raw_image_path}")

        # 2. Read the image with OpenCV for processing
        image_bgr = cv2.imread(raw_image_path)
        if image_bgr is None:
            raise Exception(f"Could not read image file: {raw_image_path}")

        # 3. Perform recognition using the pre-loaded service
        recognized_names, annotated_image = recognition_service.recognize(image_bgr)
        print(f"Recognition completed. Found: {recognized_names}")

        # 4. Save the annotated image
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        recognition_image_filename = f"recognition_result_{timestamp}.jpg"
        recognition_image_path = os.path.join(CAPTURE_DIR, recognition_image_filename)
        cv2.imwrite(recognition_image_path, annotated_image)
        print(f"Annotated image saved: {recognition_image_path}")
        
        job_id = None
        # 5. If a known person was recognized, start summarizer in the background
        if recognized_names and "Unknown" not in recognized_names:
            job_id = str(uuid4())
            # Use the annotated image for summarization
            thread = threading.Thread(target=run_summary_in_background, args=(job_id, recognition_image_path))
            thread.start()
            print(f"Started background summarization with job_id: {job_id}")
        else:
            print("No known person found or only 'Unknown' found. Skipping summarization.")

        return jsonify({
            'status': 'success',
            'names': recognized_names,
            'result_image_path': recognition_image_filename,
            'job_id': job_id
        })
        
    except Exception as e:
        error_message = f"An unexpected error occurred: {e}"
        print(error_message, file=sys.stderr)
        # It's good to also log the traceback for debugging
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': error_message}), 500


@app.route('/summary_status/<job_id>')
def summary_status(job_id):
    """Endpoint for the frontend to poll for summary results."""
    job = summary_jobs.get(job_id, {'status': 'not_found', 'summary': 'Job not found.'})
    return jsonify(job)


# --- Main Execution ---
if __name__ == '__main__':
    print("Starting web server...")
    print("Open your browser and navigate to http://scout.local:5000")
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
