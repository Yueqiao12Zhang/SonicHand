"""
Enhanced gesture classification for hand postures.
Maps hand configurations to discrete states (0-5) and retrieves continuous modulation data.
"""
import math

class GestureClassifier:
    """Classifies hand gestures based on MediaPipe landmarks."""
    
    def __init__(self):
        """Initialize gesture thresholds."""
        self.extended_threshold = 0.05  # PIP to tip distance threshold
    
    def distance(self, p1, p2):
        """Calculate Euclidean distance between two points."""
        return math.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2)
    
    def is_finger_extended(self, landmarks, tip_idx, pip_idx):
        """
        Check if finger is extended by comparing tip position with PIP (vertical).
        For regular fingers (index, middle, ring, pinky).
        """
        tip = landmarks[tip_idx]
        pip = landmarks[pip_idx]
        # Finger is extended if tip is significantly above PIP (y-coordinate is smaller)
        return (pip.y - tip.y) > self.extended_threshold
    
    def is_thumb_extended(self, landmarks):
        """
        Check if thumb is extended horizontally.
        Thumb extends from ~0.5 (MCP) to 4 (tip)
        Extended if tip.x is significantly different from MCP
        """
        thumb_mcp = landmarks[2]
        thumb_tip = landmarks[4]
        # Thumb is extended if tip is far from MCP horizontally
        horizontal_dist = abs(thumb_tip.x - thumb_mcp.x)
        vertical_dist = abs(thumb_tip.y - thumb_mcp.y)
        # Extended if horizontal distance > vertical (sideways extension)
        return horizontal_dist > vertical_dist * 1.5
    
    def classify_posture(self, landmarks):
        """
        Classify hand posture into 6 discrete states (0-5).
        
        0: Open Hand (all fingers extended)
        1: Closed Fist (no fingers extended)
        2: Fist + Thumb Out
        3: Fist + Index Out
        4: Fist + Thumb + Index Out
        5: Peace Sign (Index & Middle out, others closed)
        
        Returns: int (0-5)
        """
        # Check each finger
        thumb_extended = self.is_thumb_extended(landmarks)
        index_extended = self.is_finger_extended(landmarks, 8, 6)
        middle_extended = self.is_finger_extended(landmarks, 12, 10)
        ring_extended = self.is_finger_extended(landmarks, 16, 14)
        pinky_extended = self.is_finger_extended(landmarks, 20, 18)
        
        # Count extended fingers (excluding thumb)
        fingers_extended = [index_extended, middle_extended, ring_extended, pinky_extended]
        extended_count = sum(fingers_extended)
        
        # Classification logic
        if extended_count >= 3:
            # Open hand (at least 3 fingers extended)
            return 0
        
        elif extended_count == 0 and not thumb_extended:
            # Closed fist
            return 1
        
        elif extended_count == 0 and thumb_extended:
            # Fist + Thumb out
            return 2
        
        elif extended_count == 1 and index_extended and not thumb_extended:
            # Fist + Index out (but not thumb)
            return 3
        
        elif extended_count == 1 and index_extended and thumb_extended:
            # Fist + Thumb + Index out
            return 4
        
        elif index_extended and middle_extended and extended_count == 2 and not thumb_extended:
            # Peace sign (Index & Middle, no thumb)
            return 5
        
        # Default to closed fist if ambiguous
        return 1
    
    def get_tilt_roll(self, landmarks):
        """
        Calculate hand tilt (roll) - side-to-side rotation.
        Uses the vector from wrist (0) to middle finger tip (12).
        
        Returns: roll_angle in degrees (-90 to 90, 0 = vertical, positive = tilted right)
        """
        wrist = landmarks[0]
        middle_tip = landmarks[12]
        
        # Calculate vector
        dx = middle_tip.x - wrist.x
        dy = middle_tip.y - wrist.y
        
        # Calculate angle in radians then convert to degrees
        angle_rad = math.atan2(dy, dx)
        angle_deg = math.degrees(angle_rad)
        angle_deg -= 90  # Adjust so 0 is vertical, positive is tilted right
        
        # Convert to -90 to 90 range
        if angle_deg > 90:
            angle_deg = angle_deg - 180
        elif angle_deg < -90:
            angle_deg = angle_deg + 180
        
        return angle_deg
    
    def get_tilt_pitch(self, landmarks):
        """
        Calculate hand pitch - forward/backward inclination.
        Uses depth estimation between wrist and middle finger MCP.
        Since MediaPipe 2D doesn't provide Z directly, we estimate using hand size variations.
        
        Returns: pitch_angle in degrees (-90 to 90, 0 = neutral, positive = tilted forward)
        """
        wrist = landmarks[0]
        middle_mcp = landmarks[9]
        middle_tip = landmarks[12]
        
        # Calculate hand size (distance from wrist to middle tip)
        hand_size = math.sqrt((middle_tip.x - wrist.x)**2 + (middle_tip.y - wrist.y)**2)
        
        # Calculate MCP depth ratio (proxy for pitch)
        # If fingers are more extended below wrist, hand is tilted forward
        mcp_to_wrist_y = middle_mcp.y - wrist.y
        
        # Map to pitch angle (-90 to 90)
        # Forward (positive y) = forward tilt (positive angle)
        pitch_angle = mcp_to_wrist_y * 180 - 90
        
        # Clamp to range
        pitch_angle = max(-90, min(90, pitch_angle))
        
        return pitch_angle
