import serial
import pynmea2
import threading
import time

class GPS:
    def __init__(self, port='/dev/serial0', baudrate=9600):
        """
        Initialize GPS module for Neo 6M
        Default port for Raspberry Pi UART is /dev/serial0
        """
        self.port = port
        self.baudrate = baudrate
        self.serial_connection = None
        self.current_data = {
            'latitude': None,
            'longitude': None,
            'altitude': None,
            'satellites': 0,
            'fix_quality': 0
        }
        self.running = False
        self.thread = None
        self.location_history = []  # Track location history for trail
        
    def connect(self):
        """Establish serial connection to GPS module"""
        try:
            self.serial_connection = serial.Serial(
                self.port, 
                self.baudrate, 
                timeout=1
            )
            print(f"GPS connected on {self.port}")
            return True
        except Exception as e:
            print(f"Failed to connect to GPS: {e}")
            return False
    
    def parse_nmea(self, sentence):
        """Parse NMEA sentence from GPS"""
        try:
            if sentence.startswith('$GPGGA') or sentence.startswith('$GNGGA'):
                msg = pynmea2.parse(sentence)
                if msg.latitude and msg.longitude:
                    self.current_data['latitude'] = msg.latitude
                    self.current_data['longitude'] = msg.longitude
                    self.current_data['altitude'] = msg.altitude
                    self.current_data['fix_quality'] = msg.gps_qual
                    self.current_data['satellites'] = msg.num_sats
                    
                    # Add to location history for trail
                    self.location_history.append({
                        'lat': msg.latitude,
                        'lon': msg.longitude,
                        'timestamp': time.time()
                    })
                    
                    # Keep only last 1000 points
                    if len(self.location_history) > 1000:
                        self.location_history.pop(0)
        except Exception as e:
            pass
    
    def read_gps_data(self):
        """Continuously read GPS data from serial port"""
        while self.running:
            try:
                if self.serial_connection and self.serial_connection.in_waiting > 0:
                    line = self.serial_connection.readline().decode('ascii', errors='ignore').strip()
                    if line.startswith('$'):
                        self.parse_nmea(line)
            except Exception as e:
                print(f"Error reading GPS data: {e}")
                time.sleep(1)
    
    def start(self):
        """Start GPS data collection in a separate thread"""
        if not self.serial_connection:
            if not self.connect():
                return False
        
        self.running = True
        self.thread = threading.Thread(target=self.read_gps_data, daemon=True)
        self.thread.start()
        print("GPS data collection started")
        return True
    
    def stop(self):
        """Stop GPS data collection"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        if self.serial_connection:
            self.serial_connection.close()
        print("GPS stopped")
    
    def get_current_location(self):
        """Get current GPS location data"""
        has_fix = (
            self.current_data['latitude'] is not None and 
            self.current_data['longitude'] is not None and
            self.current_data['fix_quality'] > 0
        )
        
        return {
            'latitude': self.current_data['latitude'],
            'longitude': self.current_data['longitude'],
            'altitude': self.current_data['altitude'],
            'satellites': self.current_data['satellites'],
            'fix_quality': self.current_data['fix_quality'],
            'has_fix': has_fix
        }
    
    def get_location_history(self):
        """Get location history for drawing trail"""
        return self.location_history.copy()
    
    def clear_history(self):
        """Clear location history"""
        self.location_history = []

# Global GPS instance
gps_module = GPS()
