import threading
import time

# Try to import OLED hardware libraries
try:
    from luma.core.interface.serial import i2c
    from luma.oled.device import ssd1306
    from PIL import Image, ImageDraw, ImageFont
    OLED_AVAILABLE = True
except ImportError as e:
    print(f"OLED hardware libraries not available: {e}")
    print("Running in OLED simulation mode")
    OLED_AVAILABLE = False

class OLEDDisplay:
    def __init__(self, width=128, height=64, address=0x3C):
        """
        Initialize OLED display (SSD1306)
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
            # Create I2C interface (port=1 is default for Raspberry Pi)
            serial = i2c(port=1, address=self.address)
            
            # Create OLED display object
            self.display = ssd1306(serial, width=self.width, height=self.height)
            
            # Clear display
            self.display.clear()
            
            print("OLED display initialized successfully!")
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
                alt = self.gps_data.get('altitude', 'N/A')
                alt_str = f"{alt:.1f}m" if alt != 'N/A' and alt is not None else 'N/A'
                print(f"\r[OLED] Lat: {self.gps_data.get('latitude', 'N/A')} | Lon: {self.gps_data.get('longitude', 'N/A')} | Alt: {alt_str}", end='')
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
                alt = self.gps_data.get('altitude')
                if alt is not None:
                    alt_str = f"Alt: {alt:.1f}m"
                    draw.text((0, 44), alt_str, font=font, fill=255)
                else:
                    draw.text((0, 44), "Alt: N/A", font=font, fill=255)
            else:
                # No GPS fix
                draw.text((0, 0), "GPS Tracker", font=font, fill=255)
                draw.line((0, 12, self.width, 12), fill=255)
                draw.text((0, 20), "Waiting for", font=font, fill=255)
                draw.text((0, 35), "GPS signal...", font=font, fill=255)
                
                draw.text((0, 50), "Alt: N/A", font=font, fill=255)
            
            # Display the image (luma uses display() method)
            self.display.display(image)
            
        except Exception as e:
            print(f"Error drawing on OLED: {e}")
    
    def display_loop(self):
        """Background loop to update display"""
        while self.running:
            try:
                self.draw_gps_info()
                time.sleep(1)
            except Exception as e:
                print(f"Error in display loop: {e}")
                time.sleep(1)
    
    def start(self):
        """Start OLED display in a separate thread"""
        if not self.display and OLED_AVAILABLE:
            if not self.connect():
                return False
        
        self.running = True
        self.thread = threading.Thread(target=self.display_loop, daemon=True)
        self.thread.start()
        print("OLED display thread started")
        return True
    
    def stop(self):
        """Stop OLED display"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        if self.display and OLED_AVAILABLE:
            try:
                self.display.clear()
            except:
                pass  # Ignore cleanup errors
        print("OLED display stopped")

# Global OLED display instance
oled_display = OLEDDisplay()
