from gpiozero import OutputDevice
from time import sleep
import sys

def test_pin(gpio_pin):
    try:
        print(f"\n--- Testing GPIO BCM {gpio_pin} ---")
        print("Connecting to the pin...")
        pin = OutputDevice(gpio_pin)
        
        print(f"GPIO {gpio_pin} will now turn ON for 2 seconds, then OFF for 1 second, repeatedly.")
        print("Observe your motor driver board. Do you see any corresponding LEDs light up?")
        print("Press Ctrl+C to stop the test.")
        
        while True:
            pin.on()
            print(f"GPIO {gpio_pin} is ON")
            sleep(2)
            pin.off()
            print(f"GPIO {gpio_pin} is OFF")
            sleep(1)

    except ValueError as e:
        print(f"Error: {e}. Please ensure you enter a valid BCM GPIO number.", file=sys.stderr)
    except KeyboardInterrupt:
        print(f"\nStopped testing GPIO {gpio_pin}.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
    finally:
        if 'pin' in locals():
            pin.close()
            print(f"GPIO {gpio_pin} released.")

if __name__ == '__main__':
    print("This script helps you test individual GPIO pins.")
    print("Enter the BCM GPIO number you want to test (e.g., 20, 21, 16, 19, 26, 13).")
    
    while True:
        try:
            gpio_number_str = input("Enter BCM GPIO number to test (or 'q' to quit): ").strip()
            if gpio_number_str.lower() == 'q':
                break
            
            gpio_number = int(gpio_number_str)
            if not (0 <= gpio_number <= 27): # Basic validation for common GPIO range
                raise ValueError("GPIO number out of typical BCM range (0-27).")

            test_pin(gpio_number)
            
        except ValueError as e:
            print(f"Invalid input: {e}. Please enter an integer BCM GPIO number or 'q'.", file=sys.stderr)
        except Exception as e:
            print(f"An unexpected error occurred: {e}", file=sys.stderr)
            
    print("Exiting pin test script.")
