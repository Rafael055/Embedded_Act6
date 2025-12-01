import threading
import time
import queue
import subprocess
import shutil

class VoiceAssistant:
    def __init__(self):
        """
        Initialize Voice Assistant using espeak for text-to-speech
        Falls back to pyttsx3 if espeak is not available
        """
        self.running = False
        self.speech_queue = queue.Queue()
        self.speech_thread = None
        self.initialized = False
        self.use_espeak = False
        self.engine = None
        # Queue for web notifications (browser will poll this)
        self.web_notifications = queue.Queue()
        
    def connect(self):
        """Initialize the TTS engine"""
        try:
            # First try espeak directly (more reliable on Raspberry Pi)
            if shutil.which('espeak'):
                self.use_espeak = True
                self.initialized = True
                print("Voice Assistant initialized with espeak")
                return True
            
            # Fallback to pyttsx3
            import pyttsx3
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', 150)
            self.engine.setProperty('volume', 1.0)
            self.use_espeak = False
            self.initialized = True
            print("Voice Assistant initialized with pyttsx3")
            return True
        except Exception as e:
            print(f"Failed to initialize Voice Assistant: {e}")
            return False
    
    def _speak_espeak(self, message):
        """Speak using espeak command"""
        try:
            subprocess.run(
                ['espeak', '-s', '150', message],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=30
            )
        except Exception as e:
            print(f"Error speaking with espeak: {e}")
    
    def _speak_pyttsx3(self, message):
        """Speak using pyttsx3 engine"""
        try:
            self.engine.say(message)
            self.engine.runAndWait()
        except Exception as e:
            print(f"Error speaking with pyttsx3: {e}")
    
    def _speech_worker(self):
        """Worker thread to handle speech queue"""
        while self.running:
            try:
                # Get message from queue with timeout
                message = self.speech_queue.get(timeout=1)
                if message and self.initialized:
                    if self.use_espeak:
                        self._speak_espeak(message)
                    elif self.engine:
                        self._speak_pyttsx3(message)
                self.speech_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Speech worker error: {e}")
    
    def start(self):
        """Start the voice assistant"""
        if not self.initialized:
            if not self.connect():
                return False
        
        self.running = True
        self.speech_thread = threading.Thread(target=self._speech_worker, daemon=True)
        self.speech_thread.start()
        print("Voice Assistant started")
        return True
    
    def speak(self, message):
        """
        Add a message to the speech queue
        
        Args:
            message: Text to be spoken
        """
        if self.running and self.initialized:
            self.speech_queue.put(message)
            # Also add to web notifications queue for browser TTS
            self.web_notifications.put(message)
            print(f"Voice: {message}")
    
    def get_web_notification(self):
        """
        Get pending voice notification for web browser
        Returns None if no notification pending
        """
        try:
            return self.web_notifications.get_nowait()
        except queue.Empty:
            return None
    
    def speak_gps_searching(self):
        """Announce GPS is searching for satellites"""
        self.speak("GPS Searching")
    
    def speak_movement_detected(self, meters=5):
        """Announce that user has moved from previous location"""
        self.speak(f"You moved {meters} meters from your previous location")
    
    def speak_gps_locked(self):
        """Announce GPS has locked onto satellites"""
        self.speak("GPS signal locked")
    
    def stop(self):
        """Stop the voice assistant"""
        self.running = False
        if self.speech_thread:
            self.speech_thread.join(timeout=2)
        if self.engine:
            try:
                self.engine.stop()
            except:
                pass
        print("Voice Assistant stopped")
    
    def cleanup(self):
        """Cleanup resources"""
        self.stop()
        print("Voice Assistant cleanup complete")


class GPSVoiceMonitor:
    def __init__(self, voice_assistant, gps_module, search_interval=30):
        """
        Monitor GPS status and provide voice feedback
        
        Args:
            voice_assistant: VoiceAssistant instance
            gps_module: GPS module instance
            search_interval: Seconds between "GPS Searching" announcements
        """
        self.voice = voice_assistant
        self.gps = gps_module
        self.search_interval = search_interval
        self.running = False
        self.monitor_thread = None
        self.last_search_announcement = 0
        self.was_locked = False
        self.original_position = None
        self.movement_announced = False
        self.threshold_meters = 5
        
    def _haversine_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance between two GPS coordinates in meters"""
        from math import radians, cos, sin, asin, sqrt
        
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        r = 6371000  # Radius of earth in meters
        return c * r
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                gps_data = self.gps.get_current_location()
                current_time = time.time()
                
                has_fix = gps_data.get('has_fix', False)
                
                if has_fix:
                    # GPS is locked
                    if not self.was_locked:
                        # Just got lock, announce it
                        self.voice.speak_gps_locked()
                        self.was_locked = True
                        # Set original position when first locked
                        self.original_position = (
                            gps_data['latitude'],
                            gps_data['longitude']
                        )
                        self.movement_announced = False
                    
                    # Check for movement from original position
                    if self.original_position and not self.movement_announced:
                        current_lat = gps_data['latitude']
                        current_lon = gps_data['longitude']
                        
                        if current_lat and current_lon:
                            distance = self._haversine_distance(
                                self.original_position[0],
                                self.original_position[1],
                                current_lat,
                                current_lon
                            )
                            
                            if distance >= self.threshold_meters:
                                self.voice.speak_movement_detected(self.threshold_meters)
                                self.movement_announced = True
                                # Update original position for next movement detection
                                self.original_position = (current_lat, current_lon)
                                # Reset flag to detect next movement
                                self.movement_announced = False
                else:
                    # No GPS fix
                    self.was_locked = False
                    self.original_position = None
                    self.movement_announced = False
                    
                    # Announce "GPS Searching" every search_interval seconds
                    if current_time - self.last_search_announcement >= self.search_interval:
                        self.voice.speak_gps_searching()
                        self.last_search_announcement = current_time
                
                time.sleep(1)
                
            except Exception as e:
                print(f"GPS Voice Monitor error: {e}")
                time.sleep(1)
    
    def start(self):
        """Start the GPS voice monitor"""
        self.running = True
        self.last_search_announcement = 0  # Trigger immediate announcement if no fix
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        print("GPS Voice Monitor started")
        return True
    
    def stop(self):
        """Stop the GPS voice monitor"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        print("GPS Voice Monitor stopped")
    
    def reset_original_position(self):
        """Reset the original position (for new tracking session)"""
        self.original_position = None
        self.movement_announced = False
        print("Original position reset")


# Global instances
voice_assistant = VoiceAssistant()
gps_voice_monitor = None  # Will be initialized in app.py with GPS module
