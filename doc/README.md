# Gesture-to-OSC Controller
## Hand Gesture + Arduino Distance Sensor → PlugData Virtual Instrument

A real-time gesture recognition and distance sensing system that maps hand postures and movements to Open Sound Control (OSC) messages for controlling a synthesizer in PlugData/Pure Data.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     GESTURE-TO-OSC CONTROLLER                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │  WEBCAM      │  │  ARDUINO     │  │  MEDIAPIPE   │           │
│  │  (Video)     │  │  (Distance)  │  │  (Hand Track)│           │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘           │
│         │                 │                 │                    │
│         └─────────────────┼─────────────────┘                    │
│                           │                                      │
│                    ┌──────▼─────────┐                            │
│                    │   MAIN.PY      │                            │
│                    │  - Classify    │                            │
│                    │  - Smooth      │                            │
│                    │  - Map OSC     │                            │
│                    └──────┬─────────┘                            │
│                           │                                      │
│                    ┌──────▼─────────┐                            │
│                    │  OSC CLIENT    │                            │
│                    │  UDP 127.0.0.1 │                            │
│                    │      :9999     │                            │
│                    └──────┬─────────┘                            │
│                           │                                      │
│                    ┌──────▼─────────┐                            │
│                    │  PLUGDATA      │                            │
│                    │  Synthesizer   │                            │
│                    │  (synth1.pd)   │                            │
│                    └────────────────┘                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## Components

### 1. **Gesture Classifier** (`utils/gesture_classifier.py`)
Analyzes MediaPipe hand landmarks to determine:

#### Gesture Modes (0-5):
| Mode | Posture | OSC Mapping | Audio Effect |
|------|---------|-------------|--------------|
| **0** | Open Hand (all fingers extended) | `/synth/mode 0` | Complex modulation / Full harmonics |
| **1** | Closed Fist (no fingers extended) | `/synth/mode 1` | Basic sine/square wave |
| **2** | Fist + Thumb Out | `/synth/mode 2` | Basic + Sub-octave color |
| **3** | Fist + Index Out | `/synth/mode 3` | Basic + Fifth/Overtones |
| **4** | Fist + Thumb + Index Out | `/synth/mode 4` | Basic + Both colors |
| **5** | Peace Sign (Index & Middle) | `/synth/mode 5` | Special FX (Reverb/Delay) |

#### Continuous Parameters:
- **Roll (Side-to-side)**: Maps to `/synth/vibrato` (0.0-1.0)
- **Pitch (Forward/backward)**: Maps to `/synth/expression` (0.0-1.0)

### 2. **Arduino Handler** (`utils/arduino_handler.py`)
Manages serial communication with ultrasonic distance sensor:

- **Serial Interface**: Reads distance values from Arduino (9600 baud)
- **Smoothing**: Moving average filter (default: 5-sample window)
- **Range Mapping**: 5cm–50cm → 0.0–1.0 (OSC `/synth/pitch`)
- **Safety**: Validates data within physical range

### 3. **OSC Manager** (`utils/osc_manager.py`)
Handles UDP OSC message transmission to PlugData:

**OSC Addresses:**
| Address | Type | Range | Function |
|---------|------|-------|----------|
| `/synth/pitch` | float | 0.0–1.0 | Distance-based pitch control |
| `/synth/mode` | int | 0–5 | Gesture mode (discrete state) |
| `/synth/vibrato` | float | 0.0–1.0 | Hand roll (side-to-side tilt) |
| `/synth/expression` | float | 0.0–1.0 | Hand pitch (forward/backward tilt) |
| `/synth/volume` | float | 0.0–1.0 | Safety volume control (0 = mute) |
| `/synth/panic` | int | 0 or 1 | Emergency stop (1 = stop) |

---

## Installation

### Prerequisites
- Python 3.8+
- MacOS/Linux/Windows
- Arduino with ultrasonic distance sensor
- PlugData or Pure Data with `netreceive` listening on port 9999

### Setup Steps

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

   **requirements.txt** should contain:
   ```
   opencv-python
   python-osc
   mediapipe
   pyserial
   numpy
   ```

2. **Download MediaPipe hand model:**
   ```bash
   python download_model.py
   ```
   This creates `hand_landmarker.task` file.

3. **Configure Arduino:**
   - Flash `arduino_handshake/arduino_handshake.ino` to your Arduino board
   - **Pins:**
     - TRIG_PIN = 9 (ultrasonic trigger)
     - ECHO_PIN = 10 (ultrasonic echo)
   - **Baud rate:** 9600

4. **Find Arduino Serial Port:**
   - **macOS**: `/dev/cu.usbserial-*` (e.g., `/dev/cu.usbserial-1130`)
   - **Linux**: `/dev/ttyUSB0` or `/dev/ttyACM0`
   - **Windows**: `COM3`, `COM4`, etc.

5. **Update `main.py`:**
   - Line 25: Set correct Arduino port if needed
   ```python
   arduino = ArduinoHandler(port='/dev/cu.usbserial-1130', smooth_window=5)
   ```

6. **Setup PlugData receiver:**
   - Open `synth/synth1.pd` in PlugData
   - Ensure `netreceive -u -l 9999` is active and the patch is running
   - OSC messages will be automatically received

---

## Running the System

1. **Start PlugData:**
   ```bash
   # Open synth/synth1.pd in PlugData
   # Click "start audio" in PlugData
   ```

2. **Run the controller:**
   ```bash
   python main.py
   ```

3. **On-screen display shows:**
   - ✓/✗ Hand detection status
   - ✓/✗ Arduino connection status
   - Current gesture mode and name
   - Distance reading (cm and normalized 0.0-1.0)
   - Hand roll and pitch angles (degrees)

4. **Control synthesis:**
   - **Move hand closer/farther** → Control pitch
   - **Change finger configuration** → Switch synthesis mode
   - **Tilt hand side-to-side** → Modulate vibrato
   - **Tilt hand forward/backward** → Modulate expression
   - **Remove hand from view** → Automatic volume mute (safety)

5. **Exit:**
   - Press **'q'** to quit cleanly
   - System sends `/synth/volume 0` and `/synth/panic 1` to PlugData

---

## Data Flow & Smoothing

### Arduino Distance → Pitch
```
Raw Distance (cm)
    ↓
[Moving Average Filter: 5-sample window]
    ↓
Normalized: (distance - 5) / (50 - 5) → 0.0–1.0
    ↓
/synth/pitch ← UDP OSC
```

### Hand Tilt Angles → Vibrato/Expression
```
Raw Tilt (degrees)
    ↓
[Moving Average Filter: 5-sample window]
    ↓
Roll: (-90 to 90°) → (0.0 to 1.0)
Pitch: (-90 to 90°) → (0.0 to 1.0)
    ↓
/synth/vibrato, /synth/expression ← UDP OSC
```

### Gesture Mode (Discrete)
```
Hand Landmarks
    ↓
Classify Posture (finger detection)
    ↓
Gesture State: 0–5 (discrete)
    ↓
/synth/mode ← UDP OSC (only on change)
```

---

## Safety Features

1. **No Hand Detection:**
   - Automatically mutes audio (`/synth/volume 0`)
   - Prevents "stuck" notes if user steps away

2. **Distance Clamping:**
   - Values outside 5–50cm are clamped to 0.0–1.0 range
   - Prevents unexpected jumps

3. **Hysteresis:**
   - Volume changes only sent if significant change detected
   - Reduces OSC traffic

4. **Panic Mode:**
   - On exit: sends `/synth/panic 1` and `/synth/volume 0`
   - Emergency stop if anything goes wrong

---

## Configuration & Tuning

### Adjust Smoothing (Filter Window Size)
In `main.py`:
```python
arduino = ArduinoHandler(port='...', smooth_window=5)  # 5 samples
osc = OSCManager(ip='127.0.0.1', port=9999, tilt_smooth_window=5)
```
- Larger window = smoother but more latency
- Smaller window = more responsive but jittery

### Adjust Distance Range
In `utils/arduino_handler.py`:
```python
self.min_distance = 5.0   # cm (closest detection)
self.max_distance = 50.0  # cm (farthest detection)
```

### Adjust Gesture Detection Thresholds
In `utils/gesture_classifier.py`:
```python
self.extended_threshold = 0.05  # Distance ratio for finger extension
```

### Adjust OSC IP/Port
In `main.py`:
```python
osc = OSCManager(ip='127.0.0.1', port=9999)
```

---

## Troubleshooting

### "Failed to connect to Arduino"
- Check serial port in `main.py` (find with `ls /dev/ttyUSB*` or `ls /dev/cu.*`)
- Verify Arduino is programmed and connected
- Check USB cable and drivers

### "No hand landmarks detected"
- Ensure good lighting
- Keep hand in camera view
- Increase `min_hand_detection_confidence` in `main.py` if needed

### "PlugData not receiving OSC"
- Verify PlugData has `netreceive -u -l 9999` active
- Check IP/port in `main.py`
- Ensure PlugData audio is running
- Test with `python -m pythonosc.udp_client 127.0.0.1 9999 /test 1.0`

### Gesture misclassification
- Adjust `extended_threshold` in `gesture_classifier.py`
- Improve hand position/lighting
- Retrain if needed based on your hand size

### Jittery audio/OSC values
- Increase smoothing window size in `ArduinoHandler` and `OSCManager`
- Reduce frame rate: change `cv2.waitKey(5)` to `cv2.waitKey(10)` or higher

---

## PlugData Patch (synth1.pd) Integration

The included `synth/synth1.pd` patch expects:
- **OSC Input:** UDP netreceive on port 9999
- **Messages:**
  - `/pitch` → osc~ frequency
  - `/mode` → route/select synthesis mode
  - `/vibrato` → modulation depth
  - `/expression` → amplitude envelope
  - `/volume` → master volume multiplier
  - `/panic` → stop all notes

Extend the patch to:
1. Add mode-specific synthesis chains (sine, square, suboctave, overtones)
2. Implement reverb/delay effect for mode 5
3. Map vibrato/expression to appropriate parameters
4. Add safety cutoff for `/panic` messages

---

## File Structure

```
├── main.py                          # Main control loop
├── hand_landmarker.task             # MediaPipe model (download required)
├── requirements.txt                 # Python dependencies
├── utils/
│   ├── gesture_classifier.py        # Gesture classification logic
│   ├── arduino_handler.py           # Arduino serial interface
│   ├── osc_manager.py               # OSC message sender
│   └── webcam_capture.py            # [Legacy - can be removed]
├── arduino_handshake/
│   └── arduino_handshake.ino        # Arduino ultrasonic firmware
└── synth/
    └── synth1.pd                    # PlugData synthesizer patch
```

---

## Performance Notes

- **Latency:** ~50-100ms (webcam capture + processing + network OSC)
- **CPU Usage:** ~15-25% (single core) for real-time gesture detection
- **Network:** UDP OSC to localhost is reliable and low-latency
- **Arduino Update Rate:** 30Hz (distance sensor sampling)
- **MediaPipe Update Rate:** 30Hz (webcam frame rate)

---

## Future Enhancements

1. **Multi-hand support:** Track left hand for separate control
2. **Pressure sensitivity:** Use hand pose landmarks to estimate pressure
3. **Finger isolation:** Individual finger-to-note mapping
4. **Machine learning:** Train custom gesture classifier
5. **Recording/playback:** Log gesture sequences
6. **Network OSC:** Send to remote PlugData instances
7. **Gesture velocity:** Track hand speed for dynamics
8. **Calibration UI:** Per-user hand size calibration

---

## License & Credits

- **MediaPipe:** Google's hand tracking library
- **python-osc:** Open Sound Control client
- **OpenCV:** Computer vision
- **Arduino:** Ultrasonic distance sensing

---

## Contact & Support

For issues or improvements, refer to the inline code comments or create an issue.

**Version:** 1.0  
**Last Updated:** 2026-03-15
