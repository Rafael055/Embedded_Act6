from flask import Flask, render_template, jsonify
from gps import gps_module
from oled import oled_display
from acce import accelerometer
from led_buzzer import led_buzzer
import threading
import time
import atexit

app = Flask(__name__)

# Flag to track if GPS and OLED are initialized
system_initialized = False
movement_detected = False

def initialize_systems():
    """Initialize GPS and OLED display systems"""
    global system_initialized
    
    if not system_initialized:
        print("Initializing GPS and OLED systems...")
        
        # Start GPS module
        gps_started = gps_module.start()
        if gps_started:
            print("GPS module started successfully")
        else:
            print("Warning: GPS module failed to start")
        
        # Start OLED display
        oled_started = oled_display.start()
        if oled_started:
            print("OLED display started successfully")
        else:
            print("Warning: OLED display failed to start")
        
        # Start accelerometer
        accel_started = accelerometer.connect()
        if accel_started:
            print("Accelerometer started successfully")
        else:
            print("Warning: Accelerometer failed to start")
        
        # Start LED & Buzzer notification system
        led_started = led_buzzer.start()
        if led_started:
            print("LED & Buzzer notification system started successfully")
        else:
            print("Warning: LED & Buzzer failed to start")
        
        # Start background thread to update OLED with GPS data
        update_thread = threading.Thread(target=update_oled_loop, daemon=True)
        update_thread.start()
        
        # Start background thread to monitor location changes
        monitor_thread = threading.Thread(target=monitor_location_changes, daemon=True)
        monitor_thread.start()
        
        system_initialized = True

def update_oled_loop():
    """Background loop to update OLED with GPS data"""
    while True:
        try:
            gps_data = gps_module.get_current_location()
            oled_display.update_gps_data(gps_data)
            time.sleep(1)
        except Exception as e:
            print(f"Error in OLED update loop: {e}")
            time.sleep(1)

def monitor_location_changes():
    """Background loop to monitor GPS location changes and trigger notifications"""
    global movement_detected
    while True:
        try:
            gps_data = gps_module.get_current_location()
            
            # Only check if we have a valid GPS fix
            if gps_data['has_fix'] and gps_data['latitude'] and gps_data['longitude']:
                # Check if location changed significantly
                if led_buzzer.check_location_change(gps_data['latitude'], gps_data['longitude']):
                    # Trigger notification with pulse pattern
                    led_buzzer.pulse_pattern()
                    movement_detected = True
            
            time.sleep(1)
        except Exception as e:
            print(f"Error in location monitoring loop: {e}")
            time.sleep(1)

def cleanup():
    """Cleanup function to stop GPS, OLED, accelerometer, and LED/Buzzer on exit"""
    print("\nCleaning up...")
    gps_module.stop()
    oled_display.stop()
    accelerometer.disconnect()
    led_buzzer.cleanup()

# Register cleanup function
atexit.register(cleanup)

@app.route('/')
def home():
    """Main page with GPS tracker interface"""
    return render_template('index.html')

@app.route('/api/gps/current')
def get_current_gps():
    """API endpoint to get current GPS location"""
    try:
        location = gps_module.get_current_location()
        return jsonify({
            'success': True,
            'data': location
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/accelerometer/current')
def get_current_accelerometer():
    """API endpoint to get current accelerometer data"""
    try:
        accel_data = accelerometer.read_acceleration()
        tilt_data = accelerometer.get_tilt_angles()
        
        return jsonify({
            'success': True,
            'data': {
                'acceleration': accel_data,
                'tilt': tilt_data
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/gps/trail')
def get_gps_trail():
    """API endpoint to get GPS location history for drawing trail"""
    try:
        history = gps_module.get_location_history()
        return jsonify({
            'success': True,
            'data': history
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/movement/status')
def get_movement_status():
    """API endpoint to check if movement was detected"""
    global movement_detected
    try:
        status = movement_detected
        movement_detected = False  # Reset flag after reading
        return jsonify({
            'success': True,
            'movement_detected': status
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/gps/reset')
def reset_gps_tracking():
    """API endpoint to reset GPS tracking (clear history and position)"""
    try:
        gps_module.clear_history()
        led_buzzer.reset_position()
        return jsonify({
            'success': True,
            'message': 'GPS tracking reset'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    # Initialize systems before starting Flask
    initialize_systems()
    
    # Run Flask app
    print("\nStarting Flask server on http://0.0.0.0:5000")
    print("Press CTRL+C to stop\n")
    app.run(host='0.0.0.0', port=5000, debug=False)