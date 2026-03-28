# Quick Start Guide

## 5-Minute Setup

### Prerequisites Checklist
- ✓ Python 3.8+
- ✓ Arduino with HC-SR04 sensor connected
- ✓ Webcam
- ✓ PlugData installed
- ✓ Good lighting

---

## Installation (2 min)

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Download MediaPipe model
python download_model.py

# 3. Find your Arduino serial port
# macOS:
ls /dev/cu.usbserial*
# Linux:
ls /dev/ttyUSB* /dev/ttyACM*
# Windows: Check Device Manager
```

---

## Configuration (1 min)

Edit `main.py` line 25:
```python
arduino = ArduinoHandler(port='/dev/cu.usbserial-1130')  # ← YOUR PORT HERE
```

---

## Run (2 min)

### Terminal 1: Start PlugData
```bash
# Open synth/synth1.pd in PlugData
# Click "start audio" toggle
```

### Terminal 2: Run Python Controller
```bash
python main.py
```

**You should see:**
- ✓ Hand Detected
- ✓ Arduino connected
- Real-time gesture recognition on screen

### Control the Synth
- **Move hand closer/farther** → Pitch changes
- **Change finger pose** → Mode changes
- **Tilt hand** → Vibrato changes
- **Leave frame** → Auto mutes (safety)

---

## Done! 🎉

Press `q` to quit gracefully.

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Arduino not found" | Check port in main.py (run `ls /dev/cu.*`) |
| "No hand detected" | Improve lighting, keep hand in frame |
| "PlugData not receiving" | Verify `netreceive -l 9999` is active |
| Jittery values | Increase smooth_window to 8-10 |

---

## Full Documentation

- **README.md** — System overview & architecture
- **CONFIGURATION.md** — Advanced tuning & troubleshooting
- **OSC_PROTOCOL.md** — Detailed OSC message specification
- **utils/gesture_classifier.py** — Gesture detection code
- **utils/arduino_handler.py** — Serial communication code
- **utils/osc_manager.py** — OSC transmission code

---

## Key Files

```
main.py                 ← Run this
synth/synth1.pd         ← Open in PlugData
utils/gesture_classifier.py
utils/arduino_handler.py
utils/osc_manager.py
hand_landmarker.task    ← Download with download_model.py
```

---

## Support

Check the documentation files for detailed configuration, troubleshooting, and customization options.

**Happy gesturing! 🤚**
