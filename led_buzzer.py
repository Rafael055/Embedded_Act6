import RPi.GPIO as GPIO
import threading
import time
from math import radians, cos, sin, asin, sqrt

class LEDBuzzer:
    def __init__(self, pin=17, threshold_meters=5):
        """
        Initialize LED & Buzzer module (both connected to same GPIO pin)
        
        Args:
            pin: GPIO pin number (BCM mode) for LED & Buzzer
            threshold_meters: Distance threshold in meters to trigger notification
        """
        self.pin = pin
        self.threshold_meters = threshold_meters
        self.is_active = False
        self.last_position = None
        self.thread = None
        self.running = False
        
        # Setup GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.pin, GPIO.OUT)
        GPIO.output(self.pin, GPIO.LOW)
        
        print(f"LED & Buzzer initialized on GPIO {self.pin}")
    
    def haversine_distance(self, lat1, lon1, lat2, lon2):
        """
        Calculate the great circle distance between two points 
        on the earth (specified in decimal degrees)
        Returns distance in meters
        """
        # Convert decimal degrees to radians
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        
        # Haversine formula
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        
        # Radius of earth in meters
        r = 6371000
        return c * r
    
    def check_location_change(self, current_lat, current_lon):
        """
        Check if location has changed significantly
        Returns True if movement detected beyond threshold
        """
        if self.last_position is None:
            # First position, store it
            self.last_position = (current_lat, current_lon)
            return False
        
        # Calculate distance from last position
        distance = self.haversine_distance(
            self.last_position[0], 
            self.last_position[1],
            current_lat, 
            current_lon
        )
        
        # Check if distance exceeds threshold
        if distance >= self.threshold_meters:
            print(f"Movement detected! Distance: {distance:.2f}m")
            self.last_position = (current_lat, current_lon)
            return True
        
        return False
    
    def trigger_notification(self, duration=0.5):
        """
        Trigger LED & Buzzer for a specified duration
        
        Args:
            duration: How long to keep LED & Buzzer on (seconds)
        """
        if not self.is_active:
            return
        
        try:
            # Turn on LED & Buzzer
            GPIO.output(self.pin, GPIO.HIGH)
            time.sleep(duration)
            # Turn off LED & Buzzer
            GPIO.output(self.pin, GPIO.LOW)
        except Exception as e:
            print(f"Error triggering notification: {e}")
    
    def pulse_pattern(self):
        """Create a pulsing pattern for notification (3 short beeps)"""
        if not self.is_active:
            return
        
        for i in range(3):
            GPIO.output(self.pin, GPIO.HIGH)
            time.sleep(0.15)
            GPIO.output(self.pin, GPIO.LOW)
            time.sleep(0.1)
    
    def start(self):
        """Start the LED & Buzzer notification system"""
        self.is_active = True
        GPIO.output(self.pin, GPIO.LOW)
        print("LED & Buzzer notification system started")
        return True
    
    def stop(self):
        """Stop the LED & Buzzer notification system"""
        self.is_active = False
        GPIO.output(self.pin, GPIO.LOW)
        print("LED & Buzzer notification system stopped")
    
    def cleanup(self):
        """Cleanup GPIO resources"""
        self.stop()
        # GPIO.cleanup(self.pin)  # Don't cleanup if other modules use GPIO
        print("LED & Buzzer cleanup complete")
    
    def reset_position(self):
        """Reset the last known position (useful for restarting tracking)"""
        self.last_position = None
        print("Position tracking reset")

# Global LED & Buzzer instance
led_buzzer = LEDBuzzer(pin=17, threshold_meters=5)
