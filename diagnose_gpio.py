import RPi.GPIO as GPIO
from time import sleep

# Use BCM pin numbering
GPIO.setmode(GPIO.BCM)

pins_to_check = [20, 21, 19, 26, 16, 13]

print("Setting all pins as outputs with initial LOW...")
for pin in pins_to_check:
    GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)
    print(f"GPIO {pin} initialized")

sleep(1)

print("\nReading current state of all pins:")
for pin in pins_to_check:
    state = GPIO.input(pin)
    print(f"GPIO {pin}: {'HIGH' if state else 'LOW'}")

print("\n--- Testing Enable Pins ---")
print("Setting GPIO 16 (left enable) HIGH")
GPIO.output(16, GPIO.HIGH)
sleep(0.5)
print(f"GPIO 16 state: {'HIGH' if GPIO.input(16) else 'LOW'}")

print("Setting GPIO 13 (right enable) HIGH")
GPIO.output(13, GPIO.HIGH)
sleep(0.5)
print(f"GPIO 13 state: {'HIGH' if GPIO.input(13) else 'LOW'}")

print("\n--- Testing Motor Control Sequence ---")
print("Left motor forward: GPIO 20=HIGH, 21=LOW, 16=HIGH")
GPIO.output(16, GPIO.HIGH)  # Enable
GPIO.output(20, GPIO.HIGH)  # Forward
GPIO.output(21, GPIO.LOW)   # Backward OFF
sleep(3)
print("Stopping left motor")
GPIO.output(20, GPIO.LOW)

GPIO.cleanup()
print("\nGPIO cleanup complete")
