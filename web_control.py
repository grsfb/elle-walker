from flask import Flask, render_template, redirect, url_for, jsonify, send_from_directory, request
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
import time # <-- IMPORT

# --- Initialization ---
app = Flask(__name__)
CAPTURE_DIR = "captures"

# In-memory store for background job statuses
summary_jobs = {}
find_jobs = {}

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


def _check_view_for_person(job_id, target_name):
    """
    Helper function: Captures one image, runs recognition, and updates the job status if the person is found.
    Returns True if person is found, False otherwise.
    """
    try:
        find_jobs[job_id]['action'] = 'Analyzing view'
        
        # Capture and recognize
        raw_image_path = scout_camera.capture_image()
        image_bgr = cv2.imread(raw_image_path)
        if image_bgr is None:
            print(f"[{job_id}] Warning: Could not read image file.")
            return False

        recognized_names, annotated_image = recognition_service.recognize(image_bgr, target_name=target_name)

        if target_name in recognized_names:
            print(f"[{job_id}] Found '{target_name}'!")
            
            # Save the successful image
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            image_filename = f"recognition_result_{timestamp}.jpg"
            image_path = os.path.join(CAPTURE_DIR, image_filename)
            cv2.imwrite(image_path, annotated_image)
            print(f"[{job_id}] Saved annotated image to {image_path}")

            # Record a 5-second video clip
            video_path = scout_camera.record_video(duration=5)
            video_filename = os.path.basename(video_path)
            print(f"[{job_id}] Saved video clip to {video_path}")
            
            # Automatically start the summarization task
            summary_job_id = str(uuid4())
            summary_thread = threading.Thread(target=run_summary_in_background, args=(summary_job_id, image_path))
            summary_thread.start()
            print(f"[{job_id}] Dispatched summarization job {summary_job_id}")

            # Update status with the final result
            find_jobs[job_id] = {
                'status': 'found',
                'names': recognized_names,
                'result_image_path': image_filename,
                'result_video_path': video_filename,
                'summary_job_id': summary_job_id
            }
            return True # Person found
            
        return False # Person not found

    except Exception as e:
        print(f"[{job_id}] Error in _check_view_for_person: {e}", file=sys.stderr)
        find_jobs[job_id] = {'status': 'error', 'message': str(e)}
        return True # Return True to stop the search loop on error


def run_find_person_in_background(job_id, target_name, timeout=60):
    """
    Runs the pan-and-scan recognition loop in a background thread.
    Updates the find_jobs dictionary with the status.
    """
    print(f"[{job_id}] Starting pan-and-scan search for '{target_name}'")
    find_jobs[job_id] = {'status': 'searching', 'action': 'Starting scan'}
    
    start_time = time.time()

    try:
        while time.time() - start_time < timeout:
            # 1. Look Center
            if _check_view_for_person(job_id, target_name): return

            # 2. Pan Left
            print(f"[{job_id}] Action: Panning left")
            find_jobs[job_id]['action'] = 'Panning left'
            scout_bot.left(duration=1.5)
            if _check_view_for_person(job_id, target_name): return
            
            # 3. Pan Right (past center)
            print(f"[{job_id}] Action: Panning right")
            find_jobs[job_id]['action'] = 'Panning right'
            scout_bot.right(duration=3.0)
            if _check_view_for_person(job_id, target_name): return
            
            # 4. Return to Center
            print(f"[{job_id}] Action: Re-centering")
            find_jobs[job_id]['action'] = 'Re-centering'
            scout_bot.left(duration=1.5)
            # Loop will continue until timeout

    except Exception as e:
        print(f"[{job_id}] Critical error in find loop: {e}", file=sys.stderr)
        find_jobs[job_id] = {'status': 'error', 'message': str(e)}
        return
            
    # If the loop finishes without finding the person
    print(f"[{job_id}] Search timed out after {timeout} seconds.")
    find_jobs[job_id] = {'status': 'not_found_timeout'}


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
    data = request.get_json()
    target_name = data.get('name') if data else None

    if not target_name:
        return jsonify({'status': 'error', 'message': 'No name provided to search for.'}), 400

    job_id = str(uuid4())
    # Start the search loop in a background thread
    thread = threading.Thread(target=run_find_person_in_background, args=(job_id, target_name))
    thread.start()
    
    print(f"Dispatched background search for '{target_name}' with job_id: {job_id}")
    
    # Immediately return the job_id so the frontend can start polling
    return jsonify({'status': 'searching', 'job_id': job_id})


@app.route('/summary_status/<job_id>')
def summary_status(job_id):
    """Endpoint for the frontend to poll for summary results."""
    job = summary_jobs.get(job_id, {'status': 'not_found', 'summary': 'Job not found.'})
    return jsonify(job)


@app.route('/find_status/<job_id>')
def find_status(job_id):
    """Endpoint for the frontend to poll for find person results."""
    job = find_jobs.get(job_id, {'status': 'not_found', 'message': 'Job not found.'})
    return jsonify(job)


# --- Main Execution ---
if __name__ == '__main__':
    print("Starting web server...")
    print("Open your browser and navigate to http://scout.local:5000")
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
