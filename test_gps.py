#!/usr/bin/env python3
"""
GPS Test Script - Check if GPS module is working and waiting for signal lock
This will help determine if the GPS is functioning even without a satellite fix
"""

import serial
import time
import sys

def test_gps_connection(port='/dev/serial0', baudrate=9600, test_duration=30):
    """
    Test GPS module connectivity and signal reception
    
    Args:
        port: Serial port for GPS module
        baudrate: Communication speed (default 9600 for Neo 6M)
        test_duration: How long to monitor in seconds
    """
    print("=" * 60)
    print("GPS MODULE TEST")
    print("=" * 60)
    print(f"Port: {port}")
    print(f"Baudrate: {baudrate}")
    print(f"Test Duration: {test_duration} seconds")
    print("=" * 60)
    
    # Try to connect to GPS
    try:
        ser = serial.Serial(port, baudrate, timeout=1)
        print("✓ Successfully opened serial connection")
        print(f"  Port: {ser.name}")
        print(f"  Baudrate: {ser.baudrate}")
        print("=" * 60)
    except serial.SerialException as e:
        print(f"✗ FAILED to open serial port: {e}")
        print("\nTroubleshooting:")
        print("  1. Check if GPS is properly connected")
        print("  2. Verify UART is enabled (run 'sudo raspi-config')")
        print("  3. Check if port exists: ls -l /dev/serial*")
        print("  4. Try with sudo: sudo python3 test_gps.py")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False
    
    # Monitor GPS output
    print("\nMonitoring GPS output...")
    print("Looking for NMEA sentences and satellite information...")
    print("-" * 60)
    
    start_time = time.time()
    sentences_received = 0
    gga_sentences = 0
    rmc_sentences = 0
    gsv_sentences = 0
    satellites_visible = 0
    fix_status = "No Fix"
    last_sentence_types = set()
    
    try:
        while (time.time() - start_time) < test_duration:
            if ser.in_waiting > 0:
                try:
                    line = ser.readline().decode('ascii', errors='ignore').strip()
                    
                    if line.startswith('$'):
                        sentences_received += 1
                        
                        # Extract sentence type
                        sentence_type = line.split(',')[0] if ',' in line else line[:6]
                        last_sentence_types.add(sentence_type)
                        
                        # Print raw sentence for debugging
                        if sentences_received <= 10 or sentences_received % 20 == 0:
                            print(f"[{sentences_received:04d}] {line[:80]}")
                        
                        # Check GGA sentences (GPS Fix Data)
                        if '$GPGGA' in line or '$GNGGA' in line:
                            gga_sentences += 1
                            parts = line.split(',')
                            if len(parts) > 7:
                                fix_quality = parts[6] if len(parts[6]) > 0 else '0'
                                num_sats = parts[7] if len(parts[7]) > 0 else '0'
                                
                                if fix_quality == '0':
                                    fix_status = "No Fix (Searching...)"
                                elif fix_quality == '1':
                                    fix_status = "GPS Fix (Standard)"
                                elif fix_quality == '2':
                                    fix_status = "DGPS Fix"
                                
                                try:
                                    satellites_visible = max(satellites_visible, int(num_sats))
                                except:
                                    pass
                        
                        # Check RMC sentences (Recommended Minimum)
                        elif '$GPRMC' in line or '$GNRMC' in line:
                            rmc_sentences += 1
                        
                        # Check GSV sentences (Satellites in View)
                        elif '$GPGSV' in line or '$GNGSV' in line:
                            gsv_sentences += 1
                            parts = line.split(',')
                            if len(parts) > 3:
                                try:
                                    sats_in_view = int(parts[3]) if parts[3] else 0
                                    satellites_visible = max(satellites_visible, sats_in_view)
                                except:
                                    pass
                    
                    # Print status update every 5 seconds
                    elapsed = int(time.time() - start_time)
                    if elapsed > 0 and elapsed % 5 == 0 and sentences_received > 0:
                        print(f"\n[STATUS @ {elapsed}s] Sentences: {sentences_received} | "
                              f"Satellites: {satellites_visible} | Fix: {fix_status}")
                        
                except UnicodeDecodeError:
                    pass  # Ignore decode errors
            else:
                time.sleep(0.1)
    
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    finally:
        ser.close()
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Duration: {int(time.time() - start_time)} seconds")
    print(f"Total NMEA sentences received: {sentences_received}")
    print(f"  - GGA (Fix Data): {gga_sentences}")
    print(f"  - RMC (Recommended Minimum): {rmc_sentences}")
    print(f"  - GSV (Satellites in View): {gsv_sentences}")
    print(f"Satellites detected: {satellites_visible}")
    print(f"Fix status: {fix_status}")
    print(f"Sentence types seen: {', '.join(sorted(last_sentence_types))}")
    print("=" * 60)
    
    # Provide verdict
    print("\n" + "=" * 60)
    print("VERDICT")
    print("=" * 60)
    
    if sentences_received == 0:
        print("✗ GPS MODULE NOT RESPONDING")
        print("\nThe GPS is not sending any data. Possible issues:")
        print("  1. GPS module is not powered or not connected properly")
        print("  2. Wrong serial port (try /dev/ttyAMA0 or /dev/ttyS0)")
        print("  3. UART not enabled in Raspberry Pi config")
        print("  4. Damaged GPS module")
        return False
    
    elif sentences_received > 0 and satellites_visible == 0:
        print("⚠ GPS MODULE IS WORKING BUT NO SATELLITES DETECTED")
        print("\nThe GPS is communicating but can't see any satellites.")
        print("This could be due to:")
        print("  1. Indoor location or heavy weather (like your rainy day)")
        print("  2. Antenna not connected or damaged")
        print("  3. GPS needs more time to cold start (can take 30+ seconds)")
        print("\n✓ Your GPS board is FUNCTIONING - just needs better sky view")
        return True
    
    elif satellites_visible > 0 and fix_status == "No Fix (Searching...)":
        print(f"✓ GPS MODULE IS WORKING! Detected {satellites_visible} satellite(s)")
        print("\nThe GPS is functioning properly and actively searching for a fix.")
        print(f"It can see {satellites_visible} satellite(s) but needs more for a position lock.")
        print("\nReasons for no fix:")
        print("  1. Not enough satellites visible (need at least 4 for 3D fix)")
        print("  2. Weak signal due to weather or obstacles")
        print("  3. GPS still calculating (give it more time)")
        print("\n✓ Your GPS board is WORKING CORRECTLY!")
        return True
    
    elif "Fix" in fix_status and fix_status != "No Fix (Searching...)":
        print(f"✓ GPS MODULE IS WORKING PERFECTLY!")
        print(f"\nGPS has acquired a {fix_status} with {satellites_visible} satellite(s)")
        print("Your GPS board is functioning normally.")
        return True
    
    else:
        print("⚠ GPS MODULE STATUS UNCLEAR")
        print(f"\nReceived {sentences_received} sentences but status is inconclusive.")
        print("Try running the test for a longer duration.")
        return True

if __name__ == "__main__":
    print("\nStarting GPS test...")
    print("This will help determine if your GPS is working during bad weather.\n")
    
    # You can modify these parameters
    port = '/dev/serial0'  # Try '/dev/ttyAMA0' or '/dev/ttyS0' if this doesn't work
    baudrate = 9600
    duration = 30  # Test for 30 seconds
    
    # Parse command line arguments if provided
    if len(sys.argv) > 1:
        duration = int(sys.argv[1])
    
    result = test_gps_connection(port, baudrate, duration)
    
    print("\n" + "=" * 60)
    if result:
        print("Test completed. GPS board appears to be functional.")
    else:
        print("Test completed. GPS board may have issues.")
    print("=" * 60)