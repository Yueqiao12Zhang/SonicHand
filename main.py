import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np
import time
from utils.gesture_classifier import GestureClassifier
from utils.arduino_handler import ArduinoHandler
from utils.osc_manager import OSCManager

# --- INITIALIZE MEDIAPIPE ---
base_options = python.BaseOptions(model_asset_path='hand_landmarker.task')
options = vision.HandLandmarkerOptions(
    base_options=base_options,
    num_hands=1,
    min_hand_detection_confidence=0.7
)
hand_landmarker = vision.HandLandmarker.create_from_options(options)

# --- INITIALIZE GESTURE CLASSIFIER ---
gesture_classifier = GestureClassifier()

# --- INITIALIZE ARDUINO HANDLER ---
arduino = ArduinoHandler(port='/dev/cu.usbserial-1110', smooth_window=5)
arduino.connect()

# --- INITIALIZE OSC MANAGER ---
osc = OSCManager(ip='127.0.0.1', port=9999, tilt_smooth_window=5)

# --- GESTURE MODE DESCRIPTIONS ---
GESTURE_MODES = {
    0: "Open Hand (Chord)",
    1: "Closed Fist (Off)",
    2: "Fist + Thumb (Bass)",
    3: "Fist + Index (Saw Pad)",
    4: "Fist + Thumb + Index (Arpeggio)",
}

# --- HELPER FUNCTION: Draw hand landmarks ---
def draw_landmarks(image, landmarks):
    """Draw hand landmarks on image."""
    h, w, _ = image.shape
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
hand_detected_last_frame = False

try:
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break
        
        # Flip image horizontally
        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape
        
        # Convert to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        
        # Detect hand landmarks
        results = hand_landmarker.detect(mp_image)
        
        # --- READ ARDUINO DISTANCE DATA ---
        raw_distance, smoothed_distance, normalized_pitch = arduino.read_distance()
        
        # Default values
        hand_detected = False
        gesture_mode = 1
        tilt_roll = 0
        tilt_pitch = 0
        
        # --- PROCESS HAND DATA ---
        if results.hand_landmarks and results.handedness:
            for hand_landmarks, handedness in zip(results.hand_landmarks, results.handedness):
                # Only process right hand (camera mirror: API returns "Left" for actual right hand)
                if handedness[0].category_name != "Left":
                    continue
                
                hand_detected = True
                
                # Classify gesture
                gesture_mode = gesture_classifier.classify_posture(hand_landmarks)
                
                # Get tilt angles
                tilt_roll = gesture_classifier.get_tilt_roll(hand_landmarks)
                # tilt_pitch = gesture_classifier.get_tilt_pitch(hand_landmarks)
                thumb_metrics = gesture_classifier.get_thumb_extension_metrics(hand_landmarks)
                
                # Get hand position for visualization
                hand_center_x = int(hand_landmarks[9].x * w)
                hand_center_y = int(hand_landmarks[9].y * h)
                
                # Draw landmarks
                draw_landmarks(frame, hand_landmarks)
                
                # --- SEND OSC MESSAGES ---
                if normalized_pitch is not None:
                    osc.send_all(
                        pitch=normalized_pitch,
                        mode=gesture_mode,
                        tilt_roll=tilt_roll,
                        # tilt_pitch=tilt_pitch,
                        volume=1.0  # Hand detected, full volume
                    )
                
                # --- DISPLAY ON-SCREEN INFO ---
                gesture_name = GESTURE_MODES[gesture_mode]
                cv2.putText(frame, f"Mode {gesture_mode}: {gesture_name}", 
                           (hand_center_x - 100, hand_center_y - 60),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                
                if smoothed_distance is not None:
                    cv2.putText(frame, f"Distance: {smoothed_distance:.1f}cm ({normalized_pitch:.2f})", 
                               (hand_center_x - 100, hand_center_y - 35),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 200, 0), 2)
                
                cv2.putText(frame, f"Roll: {tilt_roll:.1f}°", 
                           (hand_center_x - 100, hand_center_y - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 100, 0), 2)

                cv2.putText(frame, f"SegGrowth: {thumb_metrics['segment_growth']:.3f}",
                           (hand_center_x - 100, hand_center_y + 15),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.55, (150, 255, 150), 2)

                cv2.putText(frame, f"RadGain: {thumb_metrics['radial_gain']:.3f}",
                           (hand_center_x - 100, hand_center_y + 38),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.55, (150, 255, 150), 2)
        
        # --- SAFETY: If no hand detected, send volume 0 ---
        if not hand_detected:
            if hand_detected_last_frame:
                # Hand was detected but is now missing - send panic
                osc.send_volume(0.0)
                print("⚠ Hand lost! Sending volume 0 to prevent stuck notes")
        
        hand_detected_last_frame = hand_detected
        
        # --- STATUS DISPLAY ---
        status_color = (0, 255, 0) if hand_detected else (0, 0, 255)
        status_text = "✓ Hand Detected" if hand_detected else "✗ No Hand"
        cv2.putText(frame, status_text, (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
        
        arduino_status = "✓ Arduino" if arduino.is_connected else "✗ Arduino"
        cv2.putText(frame, arduino_status, (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0) if arduino.is_connected else (0, 0, 255), 2)
        
        cv2.putText(frame, "Press 'q' to quit", (10, h - 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Show image
        cv2.imshow('Gesture-to-OSC Controller', frame)
        
        # Exit on 'q'
        if cv2.waitKey(5) & 0xFF == ord('q'):
            break

except KeyboardInterrupt:
    print("\n⚠ Interrupted by user")

finally:
    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    
    # Send panic to PlugData
    osc.send_panic()
    
    # Disconnect from Arduino
    arduino.disconnect()
    
    print("✓ Shutdown complete")