# eye_daemon.py
import socket
import time
import logging
from lcd_display import LCD_Display

# --- Configuration ---
UDP_IP = "127.0.0.1"
UDP_PORT = 11000

def main():
    # logging.basicConfig(level=logging.INFO)
    
    # # Initialize the display
    # display = LCD_Display()
    # display.set_emotion("neutral") # Default emotion
    
    # # Create a UDP socket
    # sock = socket.socket(socket.AF_DEye daemon listening on {UDP_IP}:{UDP_PORT}}")

    # try:
    #     while True:
    #         # Check for incoming messages
    #         try:
    #             data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
    #             emotion = data.decode().strip()
    #             logging.info(f"Received emotion: {emotion}")
    #             display.set_emotion(emotion)
    #         except socket.error:
    #             # No data received, continue
    #             pass

    #         # Update the display animations
    #         display.update()
            
    #         # Small sleep to prevent busy-waiting
    #         time.sleep(0.05)

    # except KeyboardInterrupt:
    #     logging.info("Eye daemon shutting down.")
    # finally:
    #     display.cleanup()
    #     sock.close()
    pass

if __name__ == "__main__":
    main()
