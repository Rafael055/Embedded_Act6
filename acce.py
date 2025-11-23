import smbus2
import time
import math

class Accelerometer:
    def __init__(self, bus_number=1, device_address=0x68):
        """
        Initialize accelerometer (MPU6050)
        Default I2C address is 0x68
        Set to 0x69 if AD0 pin is HIGH
        """
        self.bus_number = bus_number
        self.device_address = device_address
        self.bus = None
        self.connected = False
        
        # MPU6050 Registers
        self.PWR_MGMT_1 = 0x6B
        self.ACCEL_XOUT_H = 0x3B
        self.ACCEL_YOUT_H = 0x3D
        self.ACCEL_ZOUT_H = 0x3F
        
        # Accelerometer scaling factor (for ±2g range)
        self.ACCEL_SCALE = 16384.0
        
        # Vertical mounting adjustment (module is mounted vertically on breadboard)
        # When vertical: Z becomes X, X becomes Y, Y becomes -Z
        self.vertical_mount = True
        
        # Auto-reconnection settings
        self.last_reconnect_attempt = 0
        self.reconnect_interval = 0.5  # Try to reconnect every 0.5 seconds
        self.max_read_errors = 2  # Mark as disconnected after 2 errors
        self.consecutive_errors = 0
        self.original_address = device_address  # Save original address
        
    def connect(self):
        """Establish I2C connection to accelerometer"""
        # Try primary address first
        addresses_to_try = [self.original_address, 0x68 if self.original_address != 0x68 else 0x69]
        
        for addr in addresses_to_try:
            try:
                # Close any existing bus connection
                if self.bus:
                    try:
                        self.bus.close()
                    except:
                        pass
                
                # Create new bus connection
                self.bus = smbus2.SMBus(self.bus_number)
                self.device_address = addr
                
                # Wake up the MPU6050 (it starts in sleep mode)
                self.bus.write_byte_data(self.device_address, self.PWR_MGMT_1, 0)
                time.sleep(0.1)
                
                # Test read to verify connection
                self.bus.read_byte_data(self.device_address, self.ACCEL_XOUT_H)
                
                print(f"Accelerometer connected on I2C address 0x{self.device_address:02x}")
                self.connected = True
                self.consecutive_errors = 0
                return True
                
            except Exception as e:
                if addr == addresses_to_try[-1]:
                    print(f"Failed to connect to accelerometer on all addresses: {e}")
                continue
        
        self.connected = False
        return False
    
    def try_reconnect(self):
        """Attempt to reconnect to the accelerometer"""
        current_time = time.time()
        if current_time - self.last_reconnect_attempt < self.reconnect_interval:
            return False
        
        self.last_reconnect_attempt = current_time
        print("\n[ACCEL] Reconnecting...")
        
        success = self.connect()
        if success:
            print("[ACCEL] Reconnection successful!")
        return success
    
    def read_raw_data(self, addr):
        """Read raw 16-bit data from accelerometer"""
        try:
            # Read high and low bytes
            high = self.bus.read_byte_data(self.device_address, addr)
            low = self.bus.read_byte_data(self.device_address, addr + 1)
            
            # Combine high and low bytes
            value = (high << 8) | low
            
            # Convert to signed value
            if value > 32768:
                value = value - 65536
            
            # Reset error counter on successful read
            self.consecutive_errors = 0
            return value
            
        except Exception as e:
            self.consecutive_errors += 1
            if self.consecutive_errors >= self.max_read_errors:
                print(f"\n[ACCEL] Connection lost (OSError or I2C error)")
                self.connected = False
                # Close the bus to allow clean reconnection
                if self.bus:
                    try:
                        self.bus.close()
                        self.bus = None
                    except:
                        pass
            return 0
    
    def read_acceleration(self):
        """Read acceleration data (X, Y, Z) in g's"""
        # Try to reconnect if disconnected
        if not self.connected:
            if not self.try_reconnect():
                return {'x': 0, 'y': 0, 'z': 0, 'magnitude': 0}
        
        try:
            # Read raw accelerometer data
            acc_x_raw = self.read_raw_data(self.ACCEL_XOUT_H)
            acc_y_raw = self.read_raw_data(self.ACCEL_YOUT_H)
            acc_z_raw = self.read_raw_data(self.ACCEL_ZOUT_H)
            
            # Convert to g's
            acc_x = acc_x_raw / self.ACCEL_SCALE
            acc_y = acc_y_raw / self.ACCEL_SCALE
            acc_z = acc_z_raw / self.ACCEL_SCALE
            
            # Adjust for vertical mounting on breadboard
            # When vertical: physical Z → X axis, X → Y axis, Y → -Z axis
            if self.vertical_mount:
                x_adjusted = acc_z
                y_adjusted = acc_x
                z_adjusted = -acc_y
            else:
                x_adjusted = acc_x
                y_adjusted = acc_y
                z_adjusted = acc_z
            
            # Calculate magnitude
            magnitude = math.sqrt(x_adjusted**2 + y_adjusted**2 + z_adjusted**2)
            
            return {
                'x': round(x_adjusted, 3),
                'y': round(y_adjusted, 3),
                'z': round(z_adjusted, 3),
                'magnitude': round(magnitude, 3)
            }
            
        except Exception as e:
            print(f"[ACCEL] Error reading acceleration: {e}")
            self.connected = False
            # Close the bus
            if self.bus:
                try:
                    self.bus.close()
                    self.bus = None
                except:
                    pass
            return {'x': 0, 'y': 0, 'z': 0, 'magnitude': 0}
    
    def get_tilt_angles(self):
        """Calculate tilt angles (pitch and roll) in degrees"""
        # Try to reconnect if disconnected
        if not self.connected:
            if not self.try_reconnect():
                return {'pitch': 0, 'roll': 0}
        try:
            accel = self.read_acceleration()
            
            # Calculate pitch (rotation around Y-axis)
            pitch = math.atan2(accel['x'], math.sqrt(accel['y']**2 + accel['z']**2))
            pitch_deg = math.degrees(pitch)
            
            # Calculate roll (rotation around X-axis)
            roll = math.atan2(accel['y'], math.sqrt(accel['x']**2 + accel['z']**2))
            roll_deg = math.degrees(roll)
            
            return {
                'pitch': round(pitch_deg, 2),
                'roll': round(roll_deg, 2)
            }
            
        except Exception as e:
            print(f"Error calculating tilt: {e}")
            return {'pitch': 0, 'roll': 0}
    
    def disconnect(self):
        """Close I2C connection"""
        if self.bus:
            self.bus.close()
            print("Accelerometer disconnected")

# Global accelerometer instance
accelerometer = Accelerometer()

# Test function for debugging
def test_accelerometer():
    """Test accelerometer readings"""
    print("=" * 50)
    print("Accelerometer Test")
    print("=" * 50)
    
    if accelerometer.connect():
        print("\n✓ Accelerometer connected successfully!")
        print("\nReading acceleration data (Ctrl+C to stop)...\n")
        
        try:
            while True:
                accel = accelerometer.read_acceleration()
                tilt = accelerometer.get_tilt_angles()
                
                print(f"X: {accel['x']:+.3f}g | Y: {accel['y']:+.3f}g | Z: {accel['z']:+.3f}g | "
                      f"Mag: {accel['magnitude']:.3f}g | "
                      f"Pitch: {tilt['pitch']:+.1f}° | Roll: {tilt['roll']:+.1f}°", end='\r')
                
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\n\nTest stopped")
            accelerometer.disconnect()
    else:
        print("\n✗ Failed to connect to accelerometer")
        print("\nTroubleshooting:")
        print("1. Check I2C is enabled: sudo raspi-config")
        print("2. Check wiring connections")
        print("3. Run: i2cdetect -y 1")
        print("   Should show device at 0x68 or 0x69")

if __name__ == '__main__':
    test_accelerometer()