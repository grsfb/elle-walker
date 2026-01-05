from picamera2 import Picamera2, Preview
from libcamera import controls
from time import sleep, time
import os
import datetime

# Directory to save captured images and videos
CAPTURE_DIR = "captures"

class ScoutCamera:
    """
    A class to manage the Raspberry Pi Camera for image and video capture.
    """
    def __init__(self, save_dir=CAPTURE_DIR):
        self.picam2 = Picamera2()
        self.save_dir = save_dir
        
        # Create separate configurations for still and video
        self.still_config = self.picam2.create_still_configuration(main={"size": (640, 480)})
        self.video_config = self.picam2.create_video_configuration(main={"size": (640, 480)})
        
        # Configure camera for stills by default
        self.picam2.configure(self.still_config)
        
        # Set some initial camera controls for better image quality
        self.picam2.set_controls({"AeExposureMode": controls.AeExposureModeEnum.Short,
                                  "AwbEnable": True,
                                  "FrameRate": 30})
        
        # Ensure the save directory exists
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
            
        # Start the camera once at initialization
        self.picam2.start()
        print("ScoutCamera initialized and started.")

    def start_preview(self):
        """Starts the camera preview."""
        self.picam2.start_preview(Preview.QTGL)
        self.picam2.start()
        print("Camera preview started.")

    def stop_preview(self):
        """Stops the camera preview."""
        self.picam2.stop_preview()
        self.picam2.stop()
        print("Camera preview stopped.")

    def capture_image(self, filename=None):
        """
        Captures a still image.
        :param filename: Optional filename. If None, a timestamped filename is used.
        :return: The full path to the saved image.
        """
        # Switch to still configuration
        self.picam2.switch_mode(self.still_config)
        
        if filename is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"image_{timestamp}.jpg"
        
        file_path = os.path.join(self.save_dir, filename)
        
        self.picam2.capture_file(file_path)
        print(f"Image captured: {file_path}")
        return file_path

    def record_video(self, duration=5, filename=None):
        """
        Records a video for a specified duration.
        :param duration: Duration of the video in seconds.
        :param filename: Optional filename. If None, a timestamped filename is used.
        :return: The full path to the saved video.
        """
        # Switch to video configuration
        self.picam2.switch_mode(self.video_config)

        if filename is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"video_{timestamp}.mp4"
            
        file_path = os.path.join(self.save_dir, filename)

        print(f"Recording video to {file_path} for {duration} seconds...")
        self.picam2.start_and_record_video(file_path, duration=duration)
        print(f"Video recorded: {file_path}")
        return file_path

    def cleanup(self):
        """Cleans up camera resources."""
        if self.picam2.started:
            self.picam2.stop()
        self.picam2.close()
        print("ScoutCamera resources cleaned up.")

# ===========================================================================
# EXAMPLE USAGE
# ===========================================================================
if __name__ == '__main__':
    camera = ScoutCamera()
    
    try:
        # Test image capture
        print("\n--- Testing Image Capture ---")
        camera.capture_image()
        sleep(1) # Give some time for file to write

        # Test video recording
        print("\n--- Testing Video Recording ---")
        camera.record_video(duration=3) # Record a 3-second video
        sleep(1) # Give some time for file to write

        print("\n--- Camera Tests Complete ---")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        camera.cleanup()
