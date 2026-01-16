# lcd_display.py
# Complete elegant cyan eyes with all animations

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
        self.blink_interval = random.uniform(3, 6)
        self.is_blinking = False
        self.blink_start_time = 0
        self.blink_duration = 0.18
        self.blink_progress = 0.0

        # Gaze/movement attributes
        self.pupil_offset_x = 0
        self.pupil_offset_y = 0
        self.pupil_target_x = 0
        self.pupil_target_y = 0
        self.last_gaze_shift_time = time.time()
        self.gaze_shift_interval = random.uniform(2.5, 5)
        
        # Micro-movements
        self.microsaccade_x = 0
        self.microsaccade_y = 0
        self.last_microsaccade_time = time.time()

        # Eye shape
        self.eye_radius = 58
        self.eye_y = 100
        self.mouth_y = 200
        
        # Colors
        self.bg_color = (0, 0, 0)
        self.sclera_color = (0, 200, 220)
        self.iris_color = (0, 0, 0)
        self.highlight_color = (100, 240, 255)
        self.mouth_color = (0, 200, 220)
        self.eyebrow_color = (0, 200, 220)
        
        # Iris size
        self.iris_size_base = 0.75
        self.iris_size_current = self.iris_size_base
        self.iris_size_target = self.iris_size_base
        
        # Thinking cloud animation
        self.thinking_cloud_phase = 0
        self.last_cloud_animation_time = time.time()
        self.cloud_animation_interval = 0.5
        
        # Angry screen effect
        self.angry_flash_intensity = 0.3
        self.angry_flash_direction = 1
        
        # Iris pulsing (dilating pupils) - for all emotions
        self.iris_pulse_value = 0
        self.iris_pulse_direction = 1
        self.iris_pulse_speed = 0.006  # Base speed
        self.iris_pulse_range = 0.08  # How much it dilates (±8%)
        
        # Speaking mode - funny smileys animation
        self.smileys = []
        self.last_smiley_spawn = time.time()
        
        # Speaking mode - funny smileys animation
        self.smileys = []
        self.last_smiley_spawn = time.time()
        
        # Listening mode animation
        self.listening_pulse_intensity = 0.5
        self.listening_pulse_direction = 1
        self.listening_wave_heights = [0, 0, 0, 0, 0, 0]  # 6 bars (3 on each side)
        self.last_listening_animation_time = time.time()

    def set_emotion(self, emotion):
        """Set emotion and adjust iris size and pulse characteristics"""
        print(f"DEBUG: Setting emotion to {emotion}")
        self.emotion = emotion
        
        if emotion == "listening":
            self.iris_size_target = 0.70
            self.iris_pulse_speed = 0.005  # Slower calm pulse
            self.iris_pulse_range = 0.05
        elif emotion == "angry":
            self.iris_size_target = 0.68
            self.iris_pulse_speed = 0.012  # Faster aggressive pulse
            self.iris_pulse_range = 0.12  # Larger dilations
        elif emotion == "happy":
            self.iris_size_target = 0.73
            self.iris_pulse_speed = 0.007  # Gentle happy pulse
            self.iris_pulse_range = 0.06
        elif emotion == "sad":
            self.iris_size_target = 0.78
            self.iris_pulse_speed = 0.004  # Very slow sad pulse
            self.iris_pulse_range = 0.04
        elif emotion == "surprised":
            self.iris_size_target = 0.60
            self.iris_pulse_speed = 0.010  # Quick surprised pulse
            self.iris_pulse_range = 0.10
        elif emotion == "thinking":
            self.iris_size_target = 0.75
            self.iris_pulse_speed = 0.006  # Moderate thinking pulse
            self.iris_pulse_range = 0.07
        elif emotion == "speaking":
            self.iris_size_target = 0.73
            self.iris_pulse_speed = 0.008  # Animated speaking pulse
            self.iris_pulse_range = 0.08
            self.smileys = []  # Reset smileys when starting
        else:
            self.iris_size_target = 0.75
            self.iris_pulse_speed = 0.006  # Normal pulse
            self.iris_pulse_range = 0.08
        
        self.draw_eyes()

    def draw_eyes(self):
        """Main drawing function"""
        # Background - red tint for angry, black for others
        if self.emotion == "angry":
            red_intensity = int(80 + self.angry_flash_intensity * 50)
            bg_color = (red_intensity, 0, 0)
            self.draw.rectangle((0, 0, self.disp.height, self.disp.width), fill=bg_color)
        else:
            self.draw.rectangle((0, 0, self.disp.height, self.disp.width), fill=self.bg_color)

        left_eye_x, right_eye_x = 90, 230
        
        # Calculate current iris size with pulse
        pulsed_iris_size = self.iris_size_current + self.iris_pulse_value
        pulsed_iris_size = max(0.3, min(0.9, pulsed_iris_size))  # Clamp between 30% and 90%
        
        # Calculate iris offsets
        left_iris_x = self.pupil_offset_x + self.microsaccade_x
        left_iris_y = self.pupil_offset_y + self.microsaccade_y

        for idx, center_x in enumerate([left_eye_x, right_eye_x]):
            is_left = (idx == 0)
            current_radius = self.eye_radius
            
            if self.emotion == "happy" and self.blink_progress == 0:
                current_radius = int(self.eye_radius * 0.88)
            elif self.emotion == "surprised":
                current_radius = int(self.eye_radius * 1.12)
            
            # Calculate iris position
            raw_iris_x = center_x + left_iris_x
            raw_iris_y = self.eye_y + left_iris_y
            
            iris_radius = current_radius * pulsed_iris_size  # Use pulsed size
            max_offset = current_radius - iris_radius - 3
            
            iris_offset_from_center_x = max(-max_offset, min(max_offset, raw_iris_x - center_x))
            iris_offset_from_center_y = max(-max_offset, min(max_offset, raw_iris_y - self.eye_y))
            
            iris_x = center_x + iris_offset_from_center_x
            iris_y = self.eye_y + iris_offset_from_center_y
            
            # Draw outer glow
            for i in range(4):
                glow_size = 6 - i
                glow_alpha = 0.15 + (i * 0.15)
                glow_color = (
                    int(self.sclera_color[0] * glow_alpha),
                    int(self.sclera_color[1] * glow_alpha),
                    int(self.sclera_color[2] * glow_alpha)
                )
                self.draw.ellipse([
                    center_x - current_radius - glow_size,
                    self.eye_y - current_radius - glow_size,
                    center_x + current_radius + glow_size,
                    self.eye_y + current_radius + glow_size
                ], fill=glow_color, outline=None)
            
            # Draw cyan sclera (with pulsing for listening mode)
            sclera_color = self.sclera_color
            if self.emotion == "listening":
                # Pulse the cyan color brighter/dimmer
                pulse_factor = 0.8 + (self.listening_pulse_intensity * 0.4)  # Range: 0.8 to 1.2
                sclera_color = (
                    min(255, int(self.sclera_color[0] * pulse_factor)),
                    min(255, int(self.sclera_color[1] * pulse_factor)),
                    min(255, int(self.sclera_color[2] * pulse_factor))
                )
            
            self.draw.ellipse([
                center_x - current_radius, self.eye_y - current_radius,
                center_x + current_radius, self.eye_y + current_radius
            ], fill=sclera_color, outline=None)
            
            # Draw highlights on cyan BEFORE drawing black iris
            highlight_offset_x = current_radius * 0.35
            highlight_offset_y = -current_radius * 0.35
            
            self.draw.ellipse([
                center_x + highlight_offset_x - 14,
                self.eye_y + highlight_offset_y - 14,
                center_x + highlight_offset_x + 14,
                self.eye_y + highlight_offset_y + 14
            ], fill=(200, 250, 255), outline=None)
            
            self.draw.ellipse([
                center_x + highlight_offset_x + 10,
                self.eye_y + highlight_offset_y + 12,
                center_x + highlight_offset_x + 18,
                self.eye_y + highlight_offset_y + 20
            ], fill=self.highlight_color, outline=None)
            
            self.draw.ellipse([
                center_x - highlight_offset_x * 0.8 - 4,
                self.eye_y + highlight_offset_y * 1.2 - 4,
                center_x - highlight_offset_x * 0.8 + 4,
                self.eye_y + highlight_offset_y * 1.2 + 4
            ], fill=(150, 220, 240), outline=None)
            
            # Draw pure black iris - NO HIGHLIGHTS ON BLACK
            self.draw.ellipse([
                iris_x - iris_radius, iris_y - iris_radius,
                iris_x + iris_radius, iris_y + iris_radius
            ], fill=self.iris_color, outline=None)

        # Blinking animation
        if self.blink_progress > 0:
            progress_val = self.blink_progress if self.blink_progress <= 0.5 else (1.0 - self.blink_progress)
            progress_val *= 2
            eyelid_height = int((self.eye_radius * 2.2) * progress_val)
            
            for center_x in [left_eye_x, right_eye_x]:
                # Get current background color for eyelids
                if self.emotion == "angry":
                    eyelid_color = (int(80 + self.angry_flash_intensity * 50), 0, 0)
                else:
                    eyelid_color = self.bg_color
                    
                self.draw.rectangle([
                    center_x - self.eye_radius - 10, self.eye_y - self.eye_radius - 10,
                    center_x + self.eye_radius + 10, self.eye_y - self.eye_radius + eyelid_height
                ], fill=eyelid_color, outline=None)
                
                self.draw.rectangle([
                    center_x - self.eye_radius - 10, self.eye_y + self.eye_radius - eyelid_height,
                    center_x + self.eye_radius + 10, self.eye_y + self.eye_radius + 10
                ], fill=eyelid_color, outline=None)

        # Draw eyebrows - ALWAYS visible
        if self.blink_progress == 0:
            if self.emotion == "happy":
                for center_x in [left_eye_x, right_eye_x]:
                    self.draw.arc([
                        center_x - self.eye_radius * 0.8, self.eye_y - self.eye_radius - 28,
                        center_x + self.eye_radius * 0.8, self.eye_y - self.eye_radius - 8
                    ], 180, 0, fill=self.eyebrow_color, width=5)
                    
            elif self.emotion == "listening":
                for center_x in [left_eye_x, right_eye_x]:
                    self.draw.arc([
                        center_x - self.eye_radius * 0.8, self.eye_y - self.eye_radius - 25,
                        center_x + self.eye_radius * 0.8, self.eye_y - self.eye_radius - 5
                    ], 180, 0, fill=self.eyebrow_color, width=5)
                    
            elif self.emotion == "angry":
                # Curved angry eyebrows
                self.draw.arc([
                    left_eye_x - self.eye_radius * 0.9, self.eye_y - self.eye_radius - 30,
                    left_eye_x + self.eye_radius * 0.5, self.eye_y - self.eye_radius - 10
                ], 200, 340, fill=self.eyebrow_color, width=6)
                self.draw.arc([
                    right_eye_x - self.eye_radius * 0.5, self.eye_y - self.eye_radius - 30,
                    right_eye_x + self.eye_radius * 0.9, self.eye_y - self.eye_radius - 10
                ], 200, 340, fill=self.eyebrow_color, width=6)
                
            elif self.emotion == "sad":
                # Sad droopy eyebrows - positioned higher to avoid overlap
                for center_x in [left_eye_x, right_eye_x]:
                    self.draw.arc([
                        center_x - self.eye_radius * 0.8, self.eye_y - self.eye_radius - 25,
                        center_x + self.eye_radius * 0.8, self.eye_y - self.eye_radius - 5
                    ], 0, 180, fill=self.eyebrow_color, width=5)
                    
            elif self.emotion == "surprised":
                for center_x in [left_eye_x, right_eye_x]:
                    self.draw.arc([
                        center_x - self.eye_radius * 0.8, self.eye_y - self.eye_radius - 30,
                        center_x + self.eye_radius * 0.8, self.eye_y - self.eye_radius - 10
                    ], 180, 0, fill=self.eyebrow_color, width=5)
                    
            elif self.emotion == "thinking":
                # One raised, one normal
                self.draw.arc([
                    left_eye_x - self.eye_radius * 0.8, self.eye_y - self.eye_radius - 25,
                    left_eye_x + self.eye_radius * 0.8, self.eye_y - self.eye_radius - 5
                ], 180, 0, fill=self.eyebrow_color, width=5)
                self.draw.arc([
                    right_eye_x - self.eye_radius * 0.8, self.eye_y - self.eye_radius - 20,
                    right_eye_x + self.eye_radius * 0.8, self.eye_y - self.eye_radius
                ], 180, 0, fill=self.eyebrow_color, width=5)
                
            else:
                # Neutral
                for center_x in [left_eye_x, right_eye_x]:
                    self.draw.arc([
                        center_x - self.eye_radius * 0.8, self.eye_y - self.eye_radius - 22,
                        center_x + self.eye_radius * 0.8, self.eye_y - self.eye_radius - 2
                    ], 180, 0, fill=self.eyebrow_color, width=5)
        
        # Draw mouth
        self.draw_mouth()
        
        # Draw listening sound waves
        if self.emotion == "listening":
            self.draw_listening_waves()
        
        # Draw thinking clouds
        if self.emotion == "thinking":
            self.draw_thinking_clouds()

        image_to_show = self.image.rotate(180)
        self.disp.ShowImage(image_to_show)

    def draw_mouth(self):
        """Draw mouth based on emotion"""
        mouth_center_x = 160
        mouth_width = 35
        mouth_height = 20
        
        if self.emotion == "happy":
            self.draw.arc([
                mouth_center_x - mouth_width, self.mouth_y - mouth_height // 2,
                mouth_center_x + mouth_width, self.mouth_y + mouth_height
            ], 0, 180, fill=self.mouth_color, width=5)
            
        elif self.emotion == "sad":
            self.draw.arc([
                mouth_center_x - mouth_width, self.mouth_y - mouth_height,
                mouth_center_x + mouth_width, self.mouth_y + mouth_height // 2
            ], 180, 0, fill=self.mouth_color, width=5)
            
        elif self.emotion == "surprised":
            self.draw.ellipse([
                mouth_center_x - 12, self.mouth_y - 12,
                mouth_center_x + 12, self.mouth_y + 12
            ], outline=self.mouth_color, width=4)
            
        elif self.emotion == "angry":
            self.draw.line([
                (mouth_center_x - mouth_width * 0.8, self.mouth_y),
                (mouth_center_x + mouth_width * 0.8, self.mouth_y)
            ], fill=self.mouth_color, width=4)
            
        elif self.emotion == "thinking":
            self.draw.arc([
                mouth_center_x - mouth_width * 0.7, self.mouth_y - 8,
                mouth_center_x + mouth_width * 0.5, self.mouth_y + 8
            ], 30, 150, fill=self.mouth_color, width=4)
            
        else:
            self.draw.arc([
                mouth_center_x - mouth_width * 0.9, self.mouth_y - mouth_height // 3,
                mouth_center_x + mouth_width * 0.9, self.mouth_y + mouth_height // 2
            ], 10, 170, fill=self.mouth_color, width=4)

    def draw_listening_waves(self):
        """Draw animated sound wave bars on both sides at the bottom"""
        bar_width = 5
        bar_spacing = 7
        max_bar_height = 50  # Taller bars
        base_y = 260  # Lower position for more room
        bar_color = (0, 255, 150)  # Bright green color
        
        # Left side bars (3 bars)
        for i in range(3):
            bar_height = self.listening_wave_heights[i] * max_bar_height
            x_pos = 15 + (i * bar_spacing)
            
            self.draw.rectangle([
                x_pos, base_y - bar_height,
                x_pos + bar_width, base_y
            ], fill=bar_color, outline=None)
        
        # Right side bars (3 bars)
        for i in range(3):
            bar_height = self.listening_wave_heights[i + 3] * max_bar_height
            x_pos = 300 + (i * bar_spacing)
            
            self.draw.rectangle([
                x_pos, base_y - bar_height,
                x_pos + bar_width, base_y
            ], fill=bar_color, outline=None)

    def draw_thinking_clouds(self):
        """Draw animated thinking clouds"""
        show_cloud1 = self.thinking_cloud_phase >= 1
        show_cloud2 = self.thinking_cloud_phase >= 2
        show_cloud3 = self.thinking_cloud_phase >= 3
        
        if show_cloud1:
            cloud1_x, cloud1_y = 280, 60
            self.draw.ellipse([
                cloud1_x - 6, cloud1_y - 6,
                cloud1_x + 6, cloud1_y + 6
            ], fill=self.mouth_color, outline=None)
        
        if show_cloud2:
            cloud2_x, cloud2_y = 295, 40
            self.draw.ellipse([
                cloud2_x - 10, cloud2_y - 10,
                cloud2_x + 10, cloud2_y + 10
            ], fill=self.mouth_color, outline=None)
        
        if show_cloud3:
            cloud3_x, cloud3_y = 305, 20
            self.draw.ellipse([
                cloud3_x - 15, cloud3_y - 12,
                cloud3_x + 12, cloud3_y + 12
            ], fill=self.mouth_color, outline=None)
            self.draw.ellipse([
                cloud3_x - 20, cloud3_y - 5,
                cloud3_x - 8, cloud3_y + 8
            ], fill=self.mouth_color, outline=None)
            self.draw.ellipse([
                cloud3_x + 5, cloud3_y - 8,
                cloud3_x + 15, cloud3_y + 5
            ], fill=self.mouth_color, outline=None)

    def draw_speaking_smileys(self):
        """Draw funny moving smileys all over the screen"""
        # Draw existing smileys
        smileys_to_remove = []
        for smiley in self.smileys:
            # Update position
            smiley['x'] += smiley['vx']
            smiley['y'] += smiley['vy']
            smiley['age'] += 1
            
            # Remove if too old or off screen
            if smiley['age'] > 100 or smiley['x'] < -20 or smiley['x'] > 340 or smiley['y'] < -20 or smiley['y'] > 340:
                smileys_to_remove.append(smiley)
                continue
            
            # Draw smiley face
            size = smiley['size']
            x, y = int(smiley['x']), int(smiley['y'])
            color = smiley['color']
            
            # Face circle
            self.draw.ellipse([
                x - size, y - size,
                x + size, y + size
            ], fill=color, outline=(0, 150, 150))
            
            # Eyes
            eye_offset = size // 3
            eye_size = size // 5
            self.draw.ellipse([
                x - eye_offset - eye_size, y - eye_offset - eye_size,
                x - eye_offset + eye_size, y - eye_offset + eye_size
            ], fill=(0, 0, 0))
            self.draw.ellipse([
                x + eye_offset - eye_size, y - eye_offset - eye_size,
                x + eye_offset + eye_size, y - eye_offset + eye_size
            ], fill=(0, 0, 0))
            
            # Smile
            self.draw.arc([
                x - size // 2, y - size // 3,
                x + size // 2, y + size // 2
            ], 0, 180, fill=(0, 0, 0), width=2)
        
        # Remove old smileys
        for smiley in smileys_to_remove:
            self.smileys.remove(smiley)

    def update_speaking_animation(self):
        """Spawn new funny smileys while speaking"""
        if self.emotion != "speaking":
            self.smileys = []
            return False
        
        print(f"[SMILEYS] Active smileys: {len(self.smileys)}")  # Debug
        
        now = time.time()
        # Spawn new smiley every 0.2 seconds
        if now - self.last_smiley_spawn > 0.2:
            # Random spawn position (from edges)
            side = random.choice(['top', 'bottom', 'left', 'right'])
            if side == 'top':
                x, y = random.randint(0, 320), -10
                vx, vy = random.uniform(-1, 1), random.uniform(1, 3)
            elif side == 'bottom':
                x, y = random.randint(0, 320), 330
                vx, vy = random.uniform(-1, 1), random.uniform(-3, -1)
            elif side == 'left':
                x, y = -10, random.randint(0, 320)
                vx, vy = random.uniform(1, 3), random.uniform(-1, 1)
            else:  # right
                x, y = 330, random.randint(0, 320)
                vx, vy = random.uniform(-3, -1), random.uniform(-1, 1)
            
            # Random smiley properties
            colors = [(255, 255, 0), (0, 255, 200), (255, 150, 200), (150, 255, 150)]
            self.smileys.append({
                'x': x,
                'y': y,
                'vx': vx,
                'vy': vy,
                'size': random.randint(10, 20),
                'age': 0,
                'color': random.choice(colors)
            })
            
            print(f"[SMILEYS] Spawned new smiley at ({x}, {y})")  # Debug
            
            self.last_smiley_spawn = now
        
        return len(self.smileys) > 0  # Needs redraw if there are smileys

    def update_iris_pulse(self):
        """Update iris dilation/pulsing for all emotions"""
        # Smoothly interpolate to target size
        self.iris_size_current += (self.iris_size_target - self.iris_size_current) * 0.08
        
        # Add pulsing effect
        self.iris_pulse_value += self.iris_pulse_speed * self.iris_pulse_direction
        
        if self.iris_pulse_value >= self.iris_pulse_range:
            self.iris_pulse_value = self.iris_pulse_range
            self.iris_pulse_direction = -1
        elif self.iris_pulse_value <= -self.iris_pulse_range:
            self.iris_pulse_value = -self.iris_pulse_range
            self.iris_pulse_direction = 1
        
        return True  # Always needs redraw for smooth pulse

    def draw_speaking_smileys(self):
        """Draw funny moving smileys all over the screen"""
        # Draw existing smileys
        smileys_to_remove = []
        for smiley in self.smileys:
            # Update position
            smiley['x'] += smiley['vx']
            smiley['y'] += smiley['vy']
            smiley['age'] += 1
            
            # Remove if too old or off screen
            if smiley['age'] > 100 or smiley['x'] < -20 or smiley['x'] > 340 or smiley['y'] < -20 or smiley['y'] > 340:
                smileys_to_remove.append(smiley)
                continue
            
            # Draw smiley face
            size = smiley['size']
            x, y = int(smiley['x']), int(smiley['y'])
            color = smiley['color']
            
            # Face circle
            self.draw.ellipse([
                x - size, y - size,
                x + size, y + size
            ], fill=color, outline=(0, 150, 150))
            
            # Eyes
            eye_offset = size // 3
            eye_size = size // 5
            self.draw.ellipse([
                x - eye_offset - eye_size, y - eye_offset - eye_size,
                x - eye_offset + eye_size, y - eye_offset + eye_size
            ], fill=(0, 0, 0))
            self.draw.ellipse([
                x + eye_offset - eye_size, y - eye_offset - eye_size,
                x + eye_offset + eye_size, y - eye_offset + eye_size
            ], fill=(0, 0, 0))
            
            # Smile
            self.draw.arc([
                x - size // 2, y - size // 3,
                x + size // 2, y + size // 2
            ], 0, 180, fill=(0, 0, 0), width=2)
        
        # Remove old smileys
        for smiley in smileys_to_remove:
            self.smileys.remove(smiley)

    def update_speaking_animation(self):
        """Spawn new funny smileys while speaking"""
        if self.emotion != "speaking":
            self.smileys = []
            return False
        
        now = time.time()
        # Spawn new smiley every 0.2 seconds
        if now - self.last_smiley_spawn > 0.2:
            # Random spawn position (from edges)
            side = random.choice(['top', 'bottom', 'left', 'right'])
            if side == 'top':
                x, y = random.randint(0, 320), -10
                vx, vy = random.uniform(-1, 1), random.uniform(1, 3)
            elif side == 'bottom':
                x, y = random.randint(0, 320), 330
                vx, vy = random.uniform(-1, 1), random.uniform(-3, -1)
            elif side == 'left':
                x, y = -10, random.randint(0, 320)
                vx, vy = random.uniform(1, 3), random.uniform(-1, 1)
            else:  # right
                x, y = 330, random.randint(0, 320)
                vx, vy = random.uniform(-3, -1), random.uniform(-1, 1)
            
            # Random smiley properties
            colors = [(255, 255, 0), (0, 255, 200), (255, 150, 200), (150, 255, 150)]
            self.smileys.append({
                'x': x,
                'y': y,
                'vx': vx,
                'vy': vy,
                'size': random.randint(10, 20),
                'age': 0,
                'color': random.choice(colors)
            })
            
            self.last_smiley_spawn = now
        
        return len(self.smileys) > 0  # Needs redraw if there are smileys

    def update_listening_animation(self):
        """Animate listening mode: pulsing glow + sound wave bars"""
        if self.emotion != "listening":
            self.listening_pulse_intensity = 0.5
            self.listening_wave_heights = [0, 0, 0, 0, 0, 0]
            return False
        
        needs_redraw = False
        now = time.time()
        
        # Update pulse (smooth breathing effect)
        self.listening_pulse_intensity += 0.02 * self.listening_pulse_direction
        if self.listening_pulse_intensity >= 1.0:
            self.listening_pulse_intensity = 1.0
            self.listening_pulse_direction = -1
        elif self.listening_pulse_intensity <= 0.3:
            self.listening_pulse_intensity = 0.3
            self.listening_pulse_direction = 1
        needs_redraw = True
        
        # Update wave bars (random heights for audio equalizer effect)
        if now - self.last_listening_animation_time > 0.1:  # Update every 100ms
            for i in range(6):
                # Random height between 0.3 and 1.0
                target_height = random.uniform(0.3, 1.0)
                # Smooth transition
                self.listening_wave_heights[i] += (target_height - self.listening_wave_heights[i]) * 0.3
            self.last_listening_animation_time = now
            needs_redraw = True
        
        return needs_redraw

    def update_thinking_animation(self):
        """Animate thinking clouds"""
        if self.emotion != "thinking":
            self.thinking_cloud_phase = 0
            return False
        
        now = time.time()
        if now - self.last_cloud_animation_time > self.cloud_animation_interval:
            self.thinking_cloud_phase = (self.thinking_cloud_phase + 1) % 4
            self.last_cloud_animation_time = now
            return True
        return False
    
    def update_angry_flash(self):
        """Pulse red background when angry"""
        if self.emotion != "angry":
            self.angry_flash_intensity = 0.3
            return False
        
        # Pulse the red background
        self.angry_flash_intensity += 0.03 * self.angry_flash_direction
        if self.angry_flash_intensity >= 1.0:
            self.angry_flash_intensity = 1.0
            self.angry_flash_direction = -1
        elif self.angry_flash_intensity <= 0.3:
            self.angry_flash_intensity = 0.3
            self.angry_flash_direction = 1
        
        return True

    def update_blinking(self):
        now = time.time()
        needs_redraw = False

        if self.is_blinking:
            time_since_blink_start = now - self.blink_start_time
            
            if time_since_blink_start < self.blink_duration:
                self.blink_progress = time_since_blink_start / self.blink_duration
            else:
                self.blink_progress = 0.0
                self.is_blinking = False
                self.last_blink_time = now
                self.blink_interval = random.uniform(3, 6)
            needs_redraw = True
        
        if not self.is_blinking and (now - self.last_blink_time) > self.blink_interval:
            self.is_blinking = True
            self.blink_start_time = now
            self.blink_progress = 0.0
            needs_redraw = True
        
        return needs_redraw

    def update_gaze(self):
        now = time.time()
        needs_redraw = False

        if now - self.last_microsaccade_time > random.uniform(0.1, 0.25):
            self.microsaccade_x = random.uniform(-0.5, 0.5)
            self.microsaccade_y = random.uniform(-0.5, 0.5)
            self.last_microsaccade_time = now
            needs_redraw = True

        if now - self.last_gaze_shift_time > self.gaze_shift_interval:
            max_offset = 12
            self.pupil_target_x = random.uniform(-max_offset, max_offset)
            self.pupil_target_y = random.uniform(-max_offset, max_offset)
            self.last_gaze_shift_time = now
            self.gaze_shift_interval = random.uniform(2.5, 5)

        dx = self.pupil_target_x - self.pupil_offset_x
        dy = self.pupil_target_y - self.pupil_offset_y
        
        if abs(dx) > 0.2:
            self.pupil_offset_x += dx * 0.08
            needs_redraw = True
        else:
            self.pupil_offset_x = self.pupil_target_x

        if abs(dy) > 0.2:
            self.pupil_offset_y += dy * 0.08
            needs_redraw = True
        else:
            self.pupil_offset_y = self.pupil_target_y
        
        return needs_redraw

    def update(self):
        needs_redraw = self.update_blinking()
        needs_redraw |= self.update_gaze()
        needs_redraw |= self.update_iris_pulse()  # Pulse for all emotions
        needs_redraw |= self.update_listening_animation()
        
        # Debug speaking animation
        if self.emotion == "speaking":
            print(f"[UPDATE] Speaking mode active, calling update_speaking_animation()")
        speaking_redraw = self.update_speaking_animation()  # NEW: Speaking smileys
        needs_redraw |= speaking_redraw
        
        needs_redraw |= self.update_thinking_animation()
        needs_redraw |= self.update_angry_flash()
            
        if needs_redraw:
            self.draw_eyes()

    def show_message(self, message, font_size=20, color="WHITE"):
        self.draw.rectangle((0, 0, self.disp.height, self.disp.width), fill=self.bg_color)
        font = FONT_DEFAULT_LG if font_size >= 25 else FONT_DEFAULT_SM
        self.draw.text((10, 10), message, font=font, fill=color)
        image_to_show = self.image.rotate(180)
        self.disp.ShowImage(image_to_show)

    def cleanup(self):
        self.disp.module_exit()
        logging.info("Display cleaned up.")
