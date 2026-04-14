# SonicHand: Gesture-to-OSC Controller

Updated: 2026-04-14
- SonicHand is a final project by Yueqiao Zhang for MUMT306 in McGill University.

## What This System Does

This project converts:
- Hand gestures from a webcam (MediaPipe)
- Distance data from Arduino ultrasonic sensor

into real-time OSC messages for PlugData/Pure Data synthesis control.

## Gesture Modes

0 = Open hand
1 = Closed fist
2 = Thumb-only
3 = Thumb + index
4 = Thumb + index + middle

## Quick Run

- Download `hand_landmarker.task` from the link in `hand_landmarker_download`
```
pip install -r requirements.txt
python main.py
```

## Credits

- **[MediaPipe](https://ai.google.dev/edge/mediapipe/solutions/guide)**: Hand gesture detection library by Google
- **[python-osc](https://pypi.org/project/python-osc/)**: OSC protocol implementation
- **[PySerial](https://pypi.org/project/pyserial/)**: Arduino communication
- **[OpenCV](https://opencv.org/)**: Computer vision processing
- Youtube tutorial for synthesizer: 
    - https://www.youtube.com/watch?v=lx_L9dPIa78
    - https://www.youtube.com/watch?v=hkBCYffNMX4
- Generative AI including Github Copilot only used for code, comments, and document refining. NOT used in development.

## Possible Future directions

- Add machine learning model for custom gesture recognition training
- Expand to multi-hand tracking for collaborative musical control
- Optimize latency for real-time performance applications
- Add calibration UI for sensor distance thresholds
- Support multiple Arduino sensors for spatial audio control
- Support multiple musical scales instead of the chromatic scale only for better aesthetic purposes.


> Check `/doc` for detailed project write-up.