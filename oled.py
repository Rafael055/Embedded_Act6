import threading
import time
import board
import busio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306

# Try to initialize OLED with Adafruit library
OLED_AVAILABLE = False

try:
    # Initialize I2C
    i2c = busio.I2C(board.SCL, board.SDA)
    print("I2C initialized successfully")
    OLED_AVAILABLE = True
except Exception as e:
    print(f"Failed to initialize I2C: {e}")
    print("Running in OLED simulation mode")
    OLED_AVAILABLE = False

class OLEDDisplay:
    def __init__(self, width=128, height=64, address=0x3C):
        """
        Initialize OLED display (SSD1306) using Adafruit library
        Default I2C address is 0x3C for most OLED displays
        """
        self.width = width
        self.height = height
        self.address = address
        self.display = None
        self.running = False
        self.thread = None
        self.gps_data = None
        
    def connect(self):
        """Initialize I2C connection and OLED display"""
        if not OLED_AVAILABLE:
            print("OLED hardware not available - running in simulation mode")
            return True
            
        try:
            # Create the SSD1306 OLED class
            self.display = adafruit_ssd1306.SSD1306_I2C(
                self.width, 
                self.height, 
                i2c, 
                addr=self.address
            )
            
            # Clear display
            self.display.fill(0)
            self.display.show()
            
            print("✓ OLED display initialized successfully with Adafruit library!")
            return True
            
        except Exception as e:
            print(f"Failed to initialize OLED: {e}")
            return False
    
    def update_gps_data(self, gps_data):
        """Update GPS data to be displayed"""
        self.gps_data = gps_data
    
    def draw_gps_info(self):
        """Draw GPS information on OLED screen"""
        if not OLED_AVAILABLE or not self.display:
            # Simulation mode - print to console
            if self.gps_data:
                lat = self.gps_data.get('latitude', 'N/A')
                lon = self.gps_data.get('longitude', 'N/A')
                alt = self.gps_data.get('altitude', 'N/A')
                sats = self.gps_data.get('satellites', 0)
                has_fix = self.gps_data.get('has_fix', False)
                
                if lat != 'N/A' and isinstance(lat, (int, float)):
                    lat_str = f"{lat:.6f}"
                else:
                    lat_str = str(lat)
                    
                if lon != 'N/A' and isinstance(lon, (int, float)):
                    lon_str = f"{lon:.6f}"
                else:
                    lon_str = str(lon)
                    
                if alt != 'N/A' and isinstance(alt, (int, float)):
                    alt_str = f"{alt:.1f}m"
                else:
                    alt_str = "N/A"
                
                status = "FIX" if has_fix else "NO FIX"
                print(f"\r[OLED] {status} | Lat: {lat_str} | Lon: {lon_str} | Alt: {alt_str} | Sats: {sats}", end='', flush=True)
            return
        
        try:
            # Create blank image for drawing
            image = Image.new("1", (self.width, self.height))
            draw = ImageDraw.Draw(image)
            
            # Try to load a font, fallback to default if not available
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)
            except:
                font = ImageFont.load_default()
            
            if self.gps_data and self.gps_data.get('has_fix'):
                # Display GPS coordinates
                lat = self.gps_data.get('latitude')
                lon = self.gps_data.get('longitude')
                alt = self.gps_data.get('altitude')
                sats = self.gps_data.get('satellites', 0)
                
                # Title
                draw.text((0, 0), "GPS Tracker", font=font, fill=255)
                draw.line((0, 12, self.width, 12), fill=255)
                
                # Latitude
                if lat is not None:
                    lat_str = f"Lat: {lat:.6f}"
                    draw.text((0, 16), lat_str, font=font, fill=255)
                
                # Longitude
                if lon is not None:
                    lon_str = f"Lon: {lon:.6f}"
                    draw.text((0, 30), lon_str, font=font, fill=255)
                
                # Altitude
                if alt is not None:
                    alt_str = f"Alt: {alt:.1f}m"
                    draw.text((0, 44), alt_str, font=font, fill=255)
                else:
                    draw.text((0, 44), "Alt: N/A", font=font, fill=255)
                
                # Satellites
                sat_str = f"Sats: {sats}"
                draw.text((0, 54), sat_str, font=font, fill=255)
            else:
                # No GPS fix
                draw.text((0, 0), "GPS Tracker", font=font, fill=255)
                draw.line((0, 12, self.width, 12), fill=255)
                draw.text((0, 20), "Waiting for", font=font, fill=255)
                draw.text((0, 35), "GPS signal...", font=font, fill=255)
                draw.text((0, 50), "Alt: N/A", font=font, fill=255)
            
            # Display the image on OLED
            self.display.image(image)
            self.display.show()
            
        except Exception as e:
            print(f"\nError drawing on OLED: {e}")
    
    def display_loop(self):
        """Background loop to update display"""
        while self.running:
            try:
                self.draw_gps_info()
                time.sleep(1)
            except Exception as e:
                print(f"\nError in display loop: {e}")
                time.sleep(1)
    
    def start(self):
        """Start OLED display in a separate thread"""
        if not self.display and OLED_AVAILABLE:
            if not self.connect():
                return False
        
        self.running = True
        self.thread = threading.Thread(target=self.display_loop, daemon=True)
        self.thread.start()
        
        if OLED_AVAILABLE:
            print("OLED display thread started (Adafruit hardware mode)")
        else:
            print("OLED display thread started (simulation mode)")
        return True
    
    def stop(self):
        """Stop OLED display"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        if self.display and OLED_AVAILABLE:
            try:
                self.display.fill(0)
                self.display.show()
            except:
                pass  # Ignore cleanup errors
        print("\nOLED display stopped")

# Global OLED display instance
oled_display = OLEDDisplay()
