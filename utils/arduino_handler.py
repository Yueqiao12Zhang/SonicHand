"""
Arduino serial communication handler for ultrasonic distance sensor.
Reads distance values and applies smoothing filters.
"""
import serial
import time
from collections import deque
import math

class ArduinoHandler:
    """Manages serial communication with Arduino and distance sensor data."""
    
    def __init__(self, port='/dev/cu.usbserial-1130', baudrate=115200, timeout=0.02, smooth_window=5):
        """
        Initialize Arduino serial connection.
        
        Args:
            port: Serial port (e.g., '/dev/cu.usbserial-1130' on macOS, 'COM3' on Windows)
            baudrate: Serial communication speed
            timeout: Serial read timeout
            smooth_window: Moving average window size for smoothing (default 2 for fast response)
                          Use 3-5 for smoother but slower response
        """
        self.ser = None
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.smooth_window = smooth_window
        self.distance_buffer = deque(maxlen=smooth_window)
        self.min_distance = 5.0  # cm
        self.max_distance = 50.0  # cm (wider range = more responsive)
        self.is_connected = False
    
    def connect(self):
        """
        Establish serial connection to Arduino.
        
        Returns: bool - True if successful, False otherwise
        """
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
            time.sleep(2)  # Wait for Arduino to initialize
            self.ser.reset_input_buffer()  # Drop startup noise / stale lines
            self.is_connected = True
            print(f"✓ Connected to Arduino on {self.port}")
            return True
        except Exception as e:
            print(f"✗ Failed to connect to Arduino: {e}")
            self.is_connected = False
            return False
    
    def read_distance(self):
        """
        Read distance value from Arduino.
        
        Returns: tuple (raw_distance, smoothed_distance, normalized_distance)
                 raw_distance: cm value
                 smoothed_distance: moving average (cm)
                 normalized_distance: 0.0-1.0 based on 5-50cm range
        """
        if not self.is_connected or self.ser is None:
            return None, None, None
        
        try:
            # Drain all queued serial lines and keep the newest valid reading.
            # This prevents seconds of lag when producer (Arduino) is faster than consumer loop.
            latest_distance = None
            while self.ser.in_waiting:
                raw_line = self.ser.readline()
                line = raw_line.decode('utf-8', errors='ignore').strip()

                if line:
                    try:
                        distance_cm = float(line)
                    except ValueError:
                        continue

                    if math.isfinite(distance_cm) and 5 <= distance_cm <= 100:
                        latest_distance = distance_cm

            if latest_distance is not None:
                # Add to buffer for smoothing
                self.distance_buffer.append(latest_distance)

                # Calculate smoothed value
                smoothed_distance = sum(self.distance_buffer) / len(self.distance_buffer)

                # Normalize to 0.0-1.0 based on 5-50cm range
                distance_span = self.max_distance - self.min_distance
                if distance_span <= 0:
                    return latest_distance, smoothed_distance, None

                normalized = (smoothed_distance - self.min_distance) / distance_span
                normalized = max(0.0, min(1.0, normalized))  # Clamp to [0, 1]

                if not math.isfinite(normalized):
                    return latest_distance, smoothed_distance, None

                return latest_distance, smoothed_distance, normalized
        except (ValueError, UnicodeDecodeError):
            # Skip invalid data silently (happens with serial noise)
            pass
        except Exception as e:
            print(f"✗ Error reading from Arduino: {e}")
        
        return None, None, None
    
    def disconnect(self):
        if self.ser:
            self.ser.close()
            self.is_connected = False
            print("✓ Disconnected from Arduino")
    
    def __del__(self):
        self.disconnect()
