import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import math
import numpy as np
from utils.webcam_capture import classify_hand_posture, get_hand_tilt_angle, draw_landmarks, distance

# --- INITIALIZE MEDIAPIPE ---
base_options = python.BaseOptions(model_asset_path='hand_landmarker.task')
options = vision.HandLandmarkerOptions(
    base_options=base_options,
    num_hands=1,
    min_hand_detection_confidence=0.7
)
hand_landmarker = vision.HandLandmarker.create_from_options(options)

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