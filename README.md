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
