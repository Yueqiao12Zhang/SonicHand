"""
OSC (Open Sound Control) manager for sending data to PlugData/Pure Data.
Handles UDP OSC messages to a local or remote server.
"""
from pythonosc import udp_client
from collections import deque
import math
import time

class OSCManager:
    """Manages OSC communication with PlugData/Pure Data synthesis engine."""
    
    def __init__(self, ip='127.0.0.1', port=9999, tilt_smooth_window=5):
        """
        Initialize OSC client.
        
        Args:
            ip: Target IP address (default: localhost)
            port: Target UDP port (default: 9999)
            tilt_smooth_window: Moving average window for tilt smoothing
        """
        self.client = udp_client.SimpleUDPClient(ip, port)
        self.ip = ip
        self.port = port
        self.tilt_smooth_window = tilt_smooth_window
        self.tilt_roll_buffer = deque(maxlen=tilt_smooth_window)
        self.tilt_pitch_buffer = deque(maxlen=tilt_smooth_window)
        self.last_mode = None
        self.last_volume = None
        self.last_debug_print_time = 0.0
        print(f"✓ OSC Manager initialized: {ip}:{port}")
    
    def send_pitch(self, value):
        """
        Send normalized pitch value (0.0-1.0) to PlugData.
        
        Args:
            value: float 0.0-1.0 representing pitch
        """
        if value is None or not math.isfinite(value):
            return
        value = max(0.0, min(1.0, value))
        self.client.send_message('/synth/pitch', value)
    
    def send_mode(self, gesture_state):
        """
        Send gesture mode (0-5) to PlugData.
        Only sends if value has changed to reduce OSC traffic.
        
        Args:
            gesture_state: int 0-5 representing hand posture
        """
        gesture_state = int(gesture_state) % 6
        if gesture_state != self.last_mode:
            self.client.send_message('/synth/mode', gesture_state)
            self.last_mode = gesture_state

    
    def send_vibrato(self, tilt_roll):
        """
        Send vibrato control based on hand roll (side-to-side tilt).
        Applies smoothing and maps to 0.0-1.0 range.
        
        Args:
            tilt_roll: float in degrees (-90 to 90)
        """
        if tilt_roll is None or not math.isfinite(tilt_roll):
            return

        # Add to buffer for smoothing
        self.tilt_roll_buffer.append(tilt_roll)
        smoothed_roll = sum(self.tilt_roll_buffer) / len(self.tilt_roll_buffer)

        if not math.isfinite(smoothed_roll):
            return
        
        # Map from -90 to 90 degrees to 0.0 to 1.0
        vibrato_value = abs(smoothed_roll) / 60
        vibrato_value = max(0.0, min(1.0, vibrato_value))
        
        self.client.send_message('/synth/vibrato', vibrato_value)
    
    # def send_expression(self, tilt_pitch):
    #     """
    #     Send expression control based on hand pitch (forward/backward tilt).
    #     Applies smoothing and maps to 0.0-1.0 range.
        
    #     Args:
    #         tilt_pitch: float in degrees (-90 to 90)
    #     """
    #     # Add to buffer for smoothing
    #     self.tilt_pitch_buffer.append(tilt_pitch)
    #     smoothed_pitch = sum(self.tilt_pitch_buffer) / len(self.tilt_pitch_buffer)
        
    #     # Map from -90 to 90 degrees to 0.0 to 1.0
    #     expression_value = (smoothed_pitch + 90) / 180.0
    #     expression_value = max(0.0, min(1.0, expression_value))
        
    #     self.client.send_message('/synth/expression', expression_value)
    
    def send_volume(self, value):
        """
        Send volume control to PlugData.
        Only sends if value has changed significantly.
        
        Args:
            value: float 0.0-1.0 representing volume
        """
        if value is None or not math.isfinite(value):
            return
        value = max(0.0, min(1.0, value))
        if self.last_volume is None or abs(value - self.last_volume) >= 0.01:
            self.client.send_message('/synth/volume', value)
            self.last_volume = value
    
    def send_all(self, pitch, mode, tilt_roll, volume):
        """
        Convenience method to send all parameters at once.
        
        Args:
            pitch: float 0.0-1.0
            mode: int 0-5
            tilt_roll: float in degrees (-90 to 90)
            tilt_pitch: float in degrees (-90 to 90)
            volume: float 0.0-1.0
        """
        now = time.time()
        safe_pitch = None if pitch is None or not math.isfinite(pitch) else max(0.0, min(1.0, pitch))
        safe_roll = None if tilt_roll is None or not math.isfinite(tilt_roll) else tilt_roll
        safe_volume = None if volume is None or not math.isfinite(volume) else max(0.0, min(1.0, volume))

        if now - self.last_debug_print_time >= 0.25:
            pitch_text = f"{safe_pitch:.2f}" if safe_pitch is not None else "invalid"
            roll_text = f"{safe_roll:.1f}" if safe_roll is not None else "invalid"
            volume_text = f"{safe_volume:.2f}" if safe_volume is not None else "invalid"
            print(f"Sending OSC - Pitch: {pitch_text}, Mode: {mode}, Roll: {roll_text}°, Volume: {volume_text}")
            self.last_debug_print_time = now

        if safe_pitch is None or safe_roll is None or safe_volume is None:
            return

        self.send_pitch(safe_pitch)
        self.send_mode(mode)
        self.send_vibrato(safe_roll)
        # self.send_expression(tilt_pitch)
        self.send_volume(safe_volume)
    
    def send_panic(self):
        """Send emergency stop message to PlugData (volume 0)."""
        self.client.send_message('/synth/volume', 0.0)
        self.client.send_message('/synth/panic', 1)
        print("⚠ PANIC: Sent volume 0 to PlugData")
