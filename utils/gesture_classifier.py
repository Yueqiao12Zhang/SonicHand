"""
Enhanced gesture classification for hand postures.
Maps hand configurations to discrete states (0-5) and retrieves continuous modulation data.
"""
import math

class GestureClassifier:
    """Classifies hand gestures based on MediaPipe landmarks."""
    
    def __init__(self):
        """Initialize gesture thresholds."""
        self.extended_threshold = 0.01  # Base threshold in normalized image coords
        self.roll_relaxed_threshold_deg = 35  # Relax rules when hand is strongly rolled
    
    def distance(self, p1, p2):
        """Calculate Euclidean distance between two points."""
        return math.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2)
    
    def is_finger_extended(self, landmarks, tip_idx, pip_idx):
        """
        Tilt-aware finger extension check for index/middle/ring/pinky.
        Uses wrist-relative radial growth + palm-axis projection so detection works
        even when the hand is rotated (roll).
        """
        wrist = landmarks[0]
        middle_mcp = landmarks[9]
        tip = landmarks[tip_idx]
        pip = landmarks[pip_idx]

        # Adaptive threshold based on hand size in frame
        hand_size = self.distance(wrist, middle_mcp)
        min_extension = max(self.extended_threshold * 0.6, hand_size * 0.12)

        # 1) Radial test: tip should be farther from wrist than PIP
        radial_gain = self.distance(wrist, tip) - self.distance(wrist, pip)
        radial_extended = radial_gain > min_extension

        # 2) Axis test: tip should advance in the palm-forward direction
        axis_x = middle_mcp.x - wrist.x
        axis_y = middle_mcp.y - wrist.y
        axis_norm = math.sqrt(axis_x * axis_x + axis_y * axis_y) + 1e-9
        axis_x /= axis_norm
        axis_y /= axis_norm

        tip_vec_x = tip.x - pip.x
        tip_vec_y = tip.y - pip.y
        axis_progress = tip_vec_x * axis_x + tip_vec_y * axis_y
        axis_extended = axis_progress > (min_extension * 0.45)

        return radial_extended and axis_extended
    
    def is_thumb_extended(self, landmarks):
        """
        Tilt-aware thumb extension check.
        Avoids hard-coding a left/right x-direction rule.
        """
        metrics = self.get_thumb_extension_metrics(landmarks)
        return (
            metrics["segment_growth"] > metrics["min_extension"]
            and metrics["radial_gain"] > metrics["radial_threshold"]
            and metrics["thumb_orientation"] < 0
        )

    def get_thumb_extension_metrics(self, landmarks):
        """
        Compute thumb extension metrics for debugging/visualization.

        Returns: dict with segment_growth, radial_gain, min_extension, radial_threshold
        """
        wrist = landmarks[0]
        thumb_mcp = landmarks[2]
        thumb_ip = landmarks[3]
        thumb_tip = landmarks[4]

        hand_size = self.distance(wrist, landmarks[9])
        min_extension = max(self.extended_threshold, hand_size * 0.13)

        # Thumb is extended if MCP->tip is noticeably longer than MCP->IP
        segment_growth = self.distance(thumb_mcp, thumb_tip) - self.distance(thumb_mcp, thumb_ip)

        # And tip is farther from wrist than IP (helps reject folded-thumb fist)
        radial_gain = self.distance(wrist, thumb_tip) - self.distance(wrist, thumb_ip)

        return {
            "segment_growth": segment_growth,
            "radial_gain": radial_gain,
            "min_extension": min_extension,
            "radial_threshold": min_extension * 0.3,
            "thumb_orientation": thumb_tip.x - thumb_ip.x  # Positive if thumb points right, negative if left
        }
    
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
        # Tilt-aware adaptation: when roll is high, one non-thumb finger may look folded in 2D.
        # Keep open-hand strict enough to avoid classifying generic 3-finger poses as open hand.
        roll_abs = abs(self.get_tilt_roll(landmarks))

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
        is_open_hand = (
            extended_count >= 4
            or (
                roll_abs >= self.roll_relaxed_threshold_deg
                and extended_count == 3
                and thumb_extended
            )
        )

        if is_open_hand:
            # Open hand (tilt-aware)
            return 0
        
        elif extended_count == 0 and not thumb_extended:
            # Closed fist
            return 1
        
        elif extended_count == 0 and thumb_extended:
            # Fist + Thumb out
            return 2
        
        elif extended_count == 1 and index_extended and thumb_extended:
            # Fist + Thumb + Index out
            return 3
        
        elif extended_count == 2 and index_extended and thumb_extended and middle_extended:
            # Fist + Thumb + Index + Middle out
            return 4
        
        # Default to closed if ambiguous
        return 1
    
    def get_tilt_roll(self, landmarks):
        """
        Calculate hand tilt (roll) - side-to-side rotation.
        Uses the vector from wrist (0) to middle finger MCP (9),
        which is more stable across different finger poses.
        
        Returns: roll_angle in degrees (-90 to 90, 0 = vertical, positive = tilted right)
        """
        wrist = landmarks[0]
        middle_mcp = landmarks[9]
        
        # Calculate vector
        dx = middle_mcp.x - wrist.x
        dy = middle_mcp.y - wrist.y
        
        # 0 deg when pointing up (negative y), positive when tilted right
        angle_deg = math.degrees(math.atan2(dx, -dy))
        
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
        
        # Calculate MCP depth ratio (proxy for pitch)
        # If fingers are more extended below wrist, hand is tilted forward
        mcp_to_wrist_y = middle_mcp.y - wrist.y
        
        # Map to pitch angle (-90 to 90)
        # Forward (positive y) = forward tilt (positive angle)
        pitch_angle = mcp_to_wrist_y * 180 - 90
        
        # Clamp to range
        pitch_angle = max(-90, min(90, pitch_angle))
        
        return pitch_angle
