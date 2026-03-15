import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import math
import numpy as np

# --- INITIALIZE MEDIAPIPE ---
base_options = python.BaseOptions(model_asset_path='hand_landmarker.task')
options = vision.HandLandmarkerOptions(
    base_options=base_options,
    num_hands=1,
    min_hand_detection_confidence=0.7
)
hand_landmarker = vision.HandLandmarker.create_from_options(options)

# --- HELPER FUNCTIONS ---
def distance(p1, p2):
    """Calculate Euclidean distance between two points"""
    return math.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2)

def classify_hand_posture(landmarks):
    """
    Classify hand posture: Open Hand or Closed Fist
    Returns a tuple: (posture, thumb_pointing, index_pointing)
    """
    def is_finger_extended(tip_idx, pip_idx):
        """Check if finger is extended by comparing tip position with PIP (vertical)"""
        return landmarks[tip_idx].y < landmarks[pip_idx].y
    
    def is_thumb_extended(tip_idx, pip_idx):
        """Check if thumb is extended by comparing horizontal distance (thumb extends sideways)"""
        return landmarks[tip_idx].x < landmarks[pip_idx].x
    
    # Check if fingers are extended
    index_extended = is_finger_extended(8, 6)
    middle_extended = is_finger_extended(12, 10)
    ring_extended = is_finger_extended(16, 14)
    pinky_extended = is_finger_extended(20, 18)
    
    # Count extended fingers (excluding thumb)
    extended_count = sum([index_extended, middle_extended, ring_extended, pinky_extended])
    
    # Determine if hand is open or closed
    if extended_count >= 3:
        posture = "Open"
        thumb_pointing = False
        index_pointing = False
    else:
        posture = "Closed"
        # Only check pointing when hand is closed
        thumb_extended = is_thumb_extended(4, 3)
        thumb_pointing = thumb_extended
        index_pointing = index_extended and extended_count <= 1  # Only if index is isolated
    
    return posture, thumb_pointing, index_pointing

def get_hand_tilt_angle(landmarks):
    """
    Calculate hand tilt angle in degrees
    Uses the vector from wrist (0) to middle finger tip (12)
    Returns angle in degrees (-180 to 180)
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
    
    # Convert to -90 to 90 range (0 = vertical, positive = tilted right)
    if angle_deg > 90:
        angle_deg = angle_deg - 180
    elif angle_deg < -90:
        angle_deg = angle_deg + 180
    
    return angle_deg

# --- DRAWING HELPER ---
def draw_landmarks(image, landmarks):
    """Draw hand landmarks on image"""
    h, w, _ = image.shape
    # Connection indices for hand
    connections = [
        (0, 1), (1, 2), (2, 3), (3, 4),  # Thumb
        (0, 5), (5, 6), (6, 7), (7, 8),  # Index
        (0, 9), (9, 10), (10, 11), (11, 12),  # Middle
        (0, 13), (13, 14), (14, 15), (15, 16),  # Ring
        (0, 17), (17, 18), (18, 19), (19, 20)  # Pinky
    ]
    
    # Draw connections
    for start, end in connections:
        x1, y1 = int(landmarks[start].x * w), int(landmarks[start].y * h)
        x2, y2 = int(landmarks[end].x * w), int(landmarks[end].y * h)
        cv2.line(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
    
    # Draw landmarks
    for landmark in landmarks:
        x = int(landmark.x * w)
        y = int(landmark.y * h)
        cv2.circle(image, (x, y), 4, (255, 0, 0), -1)

# --- MAIN LOOP ---
cap = cv2.VideoCapture(0)

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        break
    
    # Flip image
    frame = cv2.flip(frame, 1)
    
    # Convert to RGB for MediaPipe
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
    
    # Detect hand landmarks
    results = hand_landmarker.detect(mp_image)
    
    # Get image dimensions
    h, w, _ = frame.shape
    
    # Process detected hands
    if results.hand_landmarks and results.handedness:
        for hand_landmarks, handedness in zip(results.hand_landmarks, results.handedness):
            # Only process right hand (camera mirror means API returns "Left" for actual right hand)
            if handedness[0].category_name != "Left":
                continue
            
            # Classify posture
            posture, thumb_pointing, index_pointing = classify_hand_posture(hand_landmarks)
            tilt_angle = get_hand_tilt_angle(hand_landmarks)
            
            # Get hand position for text placement
            hand_center_x = int(hand_landmarks[9].x * w)
            hand_center_y = int(hand_landmarks[9].y * h)
            
            # Draw hand landmarks
            draw_landmarks(frame, hand_landmarks)
            
            # Build label with hand info
            pointing_info = ""
            if thumb_pointing:
                pointing_info += "Thumb "
            if index_pointing:
                pointing_info += "Index"
            if pointing_info:
                pointing_info = f" ({pointing_info.strip()})"
            
            # Display posture label
            label = f"Right: {posture}{pointing_info}"
            cv2.putText(frame, label, (hand_center_x - 60, hand_center_y - 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            
            # Display tilt angle
            tilt_label = f"Tilt: {tilt_angle:.1f}°"
            cv2.putText(frame, tilt_label, (hand_center_x - 60, hand_center_y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
    
    # Display instructions
    cv2.putText(frame, "Press 'q' to quit", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    # Show image
    cv2.imshow('Hand Posture Caption', frame)
    
    # Exit on 'q'
    if cv2.waitKey(5) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()