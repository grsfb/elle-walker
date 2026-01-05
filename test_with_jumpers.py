import RPi.GPIO as GPIO
from time import sleep

GPIO.setmode(GPIO.BCM)

# Setup motor control pins only (no enable pins needed with jumpers)
GPIO.setup(20, GPIO.OUT, initial=GPIO.LOW)  # Left forward
GPIO.setup(21, GPIO.OUT, initial=GPIO.LOW)  # Left backward
GPIO.setup(19, GPIO.OUT, initial=GPIO.LOW)  # Right forward
GPIO.setup(26, GPIO.OUT, initial=GPIO.LOW)  # Right backward

print("Testing LEFT motor forward (5 seconds)...")
GPIO.output(20, GPIO.HIGH)
GPIO.output(21, GPIO.LOW)
sleep(5)
GPIO.output(20, GPIO.LOW)

sleep(2)

print("Testing RIGHT motor forward (5 seconds)...")
GPIO.output(19, GPIO.HIGH)
GPIO.output(26, GPIO.LOW)
sleep(5)
GPIO.output(19, GPIO.LOW)

sleep(2)

print("Testing BOTH motors forward (5 seconds)...")
GPIO.output(20, GPIO.HIGH)
GPIO.output(19, GPIO.HIGH)
sleep(5)
GPIO.output(20, GPIO.LOW)
GPIO.output(19, GPIO.LOW)

GPIO.cleanup()
print("Test complete")
