# lcd_display.py
# A module to control the 2-inch ST7789V LCD display and show facial expressions.

import os
import sys
import time
import spidev
import logging
import random
import math
from PIL import Image, ImageDraw, ImageFont

# Add the Waveshare Python library path to sys.path
WAVESHARE_LIB_PATH = os.path.join(os.path.dirname(__file__), "LCD_Module_RPI_code/RaspberryPi/python")
if WAVESHARE_LIB_PATH not in sys.path:
    sys.path.append(WAVESHARE_LIB_PATH)

from lib import LCD_2inch

# --- Configuration ---
# Raspberry Pi pin configuration:
RST = 27
DC = 25
BL = 18
bus = 0
device = 0

# LCD dimensions
LCD_WIDTH = 240
LCD_HEIGHT = 320

# Font path
WAVESHARE_FONT_PATH = os.path.join(WAVESHARE_LIB_PATH, "Font/Font01.ttf")
try:
    FONT_DEFAULT_SM = ImageFont.truetype(WAVESHARE_FONT_PATH, 20)
    FONT_DEFAULT_LG = ImageFont.truetype(WAVESHARE_FONT_PATH, 30)
except IOError:
    FONT_DEFAULT_SM = ImageFont.load_default()
    FONT_DEFAULT_LG = ImageFont.load_default()


class LCD_Display:
    def __init__(self):
        # Hardware setup
        self.disp = LCD_2inch.LCD_2inch(spi=spidev.SpiDev(bus, device), spi_freq=10000000, rst=RST, dc=DC, bl=BL)
        self.disp.Init()
        self.disp.clear()
        self.disp.bl_DutyCycle(50)
        self.image = Image.new("RGB", (self.disp.height, self.disp.width), "BLACK")
        self.draw = ImageDraw.Draw(self.image)

        # Eye state attributes
        self.emotion = "neutral"
        
        # Blinking attributes
        self.last_blink_time = time.time()
        self.blink_interval = random.uniform(2, 5)
        self.is_blinking = False
        self.blink_start_time = 0
        self.blink_duration = 0.15

        # Gaze/rolling attributes
        self.pupil_offset_x = 0
        self.pupil_offset_y = 0
        self.pupil_target_x = 0
        self.pupil_target_y = 0
        self.last_gaze_shift_time = time.time()
        self.gaze_shift_interval = random.uniform(1, 3)

    def set_emotion(self, emotion):
        self.emotion = emotion
        self.draw_eyes()

    def draw_eyes(self):
        self.draw.rectangle((0, 0, self.disp.height, self.disp.width), fill="BLACK")

        # Eye parameters
        iris_color = (0, 150, 255)  # A brighter blue
        left_eye_x, right_eye_x = 80, 240
        eye_y = 120
        size = 60  # Bigger eyes

        if self.is_blinking:
            # Draw a thick arc for a more pronounced blink with "eyelashes"
            self.draw.arc((left_eye_x - size, eye_y - size, left_eye_x + size, eye_y + size), 180, 0, fill="WHITE", width=15)
            self.draw.arc((right_eye_x - size, eye_y - size, right_eye_x + size, eye_y + size), 180, 0, fill="WHITE", width=15)
        else:
            for center_x in [left_eye_x, right_eye_x]:
                # Sclera (eye white)
                self.draw.ellipse((center_x - size, eye_y - size, center_x + size, eye_y + size), fill="WHITE", outline="GRAY", width=2)
                
                # Iris
                iris_radius = size * 0.7
                self.draw.ellipse((center_x - iris_radius, eye_y - iris_radius, center_x + iris_radius, eye_y + iris_radius), fill=iris_color)

                # Pupil (with rolling offset)
                pupil_radius = size * 0.4
                pupil_x = center_x + self.pupil_offset_x
                pupil_y = eye_y + self.pupil_offset_y
                self.draw.ellipse((pupil_x - pupil_radius, pupil_y - pupil_radius, pupil_x + pupil_radius, pupil_y + pupil_radius), fill="BLACK")

                # Highlights
                self.draw.ellipse((center_x + size * 0.2, eye_y - size * 0.5, center_x + size * 0.5, eye_y - size * 0.2), fill="WHITE")
                self.draw.ellipse((center_x - size * 0.5, eye_y + size * 0.3, center_x - size * 0.3, eye_y + size * 0.5), fill="WHITE")

            # Emotion-specific modifications
            if self.emotion == "happy":
                self.draw.arc((left_eye_x - size, eye_y - size, left_eye_x + size, eye_y + size), 180, 0, fill="BLACK", width=8)
                self.draw.arc((right_eye_x - size, eye_y - size, right_eye_x + size, eye_y + size), 180, 0, fill="BLACK", width=8)
            elif self.emotion == "sad":
                self.draw.arc((left_eye_x - size, eye_y, left_eye_x + size, eye_y + size*1.5), 0, 180, fill="BLACK", width=8)
                self.draw.arc((right_eye_x - size, eye_y, right_eye_x + size, eye_y + size*1.5), 0, 180, fill="BLACK", width=8)
            elif self.emotion == "angry":
                self.draw.line((left_eye_x - 35, eye_y - 25, left_eye_x + 35, eye_y + 15), fill="BLACK", width=10)
                self.draw.line((right_eye_x - 35, eye_y + 15, right_eye_x + 35, eye_y - 25), fill="BLACK", width=10)

        image_to_show = self.image.rotate(180)
        self.disp.ShowImage(image_to_show)

    def update_blinking(self):
        now = time.time()
        if self.is_blinking and (now - self.blink_start_time) > self.blink_duration:
            self.is_blinking = False
            self.last_blink_time = now
            self.blink_interval = random.uniform(2, 5)
            return True # Indicates a redraw is needed

        if not self.is_blinking and (now - self.last_blink_time) > self.blink_interval:
            self.is_blinking = True
            self.blink_start_time = now
            return True # Indicates a redraw is needed
        return False

    def update_gaze(self):
        now = time.time()
        if now - self.last_gaze_shift_time > self.gaze_shift_interval:
            max_offset = 15
            self.pupil_target_x = random.uniform(-max_offset, max_offset)
            self.pupil_target_y = random.uniform(-max_offset, max_offset)
            self.last_gaze_shift_time = now
            self.gaze_shift_interval = random.uniform(1, 3)

        # Smoothly move pupils towards the target
        dx = self.pupil_target_x - self.pupil_offset_x
        dy = self.pupil_target_y - self.pupil_offset_y
        
        # A simple linear interpolation for smooth movement
        self.pupil_offset_x += dx * 0.1
        self.pupil_offset_y += dy * 0.1
        
        # If the pupil is close to the target, it might not need a redraw every frame
        if abs(dx) > 0.1 or abs(dy) > 0.1:
            return True # Indicates a redraw is needed
        return False

    def update(self):
        needs_redraw = self.update_blinking()
        needs_redraw |= self.update_gaze()
        if needs_redraw:
            self.draw_eyes()

    def show_message(self, message, font_size=20, color="WHITE"):
        self.draw.rectangle((0,0,self.disp.height, self.disp.width), fill="BLACK")
        font = FONT_DEFAULT_LG
        if font_size < 25:
            font = FONT_DEFAULT_SM
        self.draw.text((10, 10), message, font=font, fill=color)
        image_to_show = self.image.rotate(180)
        self.disp.ShowImage(image_to_show)

    def cleanup(self):
        self.disp.module_exit()
        logging.info("Display cleaned up.")

if __name__ == "__main__":
    display = None
    try:
        logging.basicConfig(level=logging.INFO)
        display = LCD_Display()
        start_time = time.time()
        current_emotion = "neutral"
        display.set_emotion(current_emotion)

        while time.time() - start_time < 30:
            display.update()

            # Emotion change logic
            elapsed = int(time.time() - start_time)
            new_emotion = current_emotion
            if 3 <= elapsed < 6:
                new_emotion = "happy"
            elif 6 <= elapsed < 9:
                new_emotion = "listening"
            elif 9 <= elapsed < 12:
                new_emotion = "thinking"
            elif 12 <= elapsed < 15:
                new_emotion = "sad"
            elif 15 <= elapsed < 18:
                new_emotion = "angry"
            elif elapsed >= 18:
                new_emotion = "neutral"

            if new_emotion != current_emotion:
                current_emotion = new_emotion
                display.set_emotion(current_emotion)

            time.sleep(0.05) # Reduced sleep for smoother animation

        display.show_message("All done!", font_size=30, color="CYAN")
        time.sleep(3)

    except KeyboardInterrupt:
        logging.info("Display test interrupted.")
    except Exception as e:
        logging.error(f"An error occurred: {e}")
    finally:
        if display:
            display.cleanup()