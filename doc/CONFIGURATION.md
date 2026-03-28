# Configuration & Setup Guide

## Quick Start Checklist

- [ ] Arduino programmed with `arduino_handshake.ino`
- [ ] Arduino connected to computer (find serial port)
- [ ] Python environment with `requirements.txt` installed
- [ ] `hand_landmarker.task` downloaded
- [ ] Serial port configured in `main.py`
- [ ] PlugData installed and synth patch ready
- [ ] Good lighting for hand detection

---

## Step-by-Step Setup

### 1. Arduino Setup

#### Wiring Diagram (HC-SR04 Ultrasonic Sensor)
```
HC-SR04        Arduino
------         -------
VCC     →      5V
GND     →      GND
TRIG    →      Pin 9
ECHO    →      Pin 10
```

#### Arduino Serial Configuration
```cpp
Serial.begin(9600);  // Baud rate must match main.py
```

#### Test Arduino Output
```bash
# macOS: Use screen or miniterm to verify data
screen /dev/cu.usbserial-1130 9600
# You should see distance values like: 15, 16, 14, 15...
# Press Ctrl+A then Ctrl+Q to exit
```

---

### 2. Finding Arduino Serial Port

#### macOS
```bash
ls /dev/tty.*
# Look for: /dev/tty.usbserial-XXXXXX
# Common patterns: /dev/cu.usbserial-1130, /dev/cu.usbserial-14140
```

#### Linux
```bash
ls /dev/ttyUSB* /dev/ttyACM*
# Common: /dev/ttyUSB0, /dev/ttyACM0
```

#### Windows
```cmd
wmic logicaldisk where name="COM3" list
# Or use Device Manager → Ports (COM & LPT)
```

---

### 3. Python Environment Configuration

#### Install Requirements
```bash
pip install opencv-python python-osc mediapipe pyserial numpy
# Or use requirements.txt:
pip install -r requirements.txt
```

#### Download MediaPipe Model
```bash
python download_model.py
# Creates: hand_landmarker.task (~200MB)
```

#### Verify Installation
```bash
python -c "import mediapipe as mp; print(mp.__version__)"
python -c "from pythonosc import udp_client; print('OSC OK')"
python -c "import serial; print('PySerial OK')"
```

---

### 4. Configure main.py

Update these lines if using non-standard configuration:

```python
# Line 25: Arduino serial port
arduino = ArduinoHandler(
    port='/dev/cu.usbserial-1130',  # ← YOUR SERIAL PORT HERE
    baudrate=9600,                  # Must match Arduino
    smooth_window=5                 # Smoothing filter size
)

# Line 28: OSC target
osc = OSCManager(
    ip='127.0.0.1',                 # localhost (or remote IP)
    port=9999,                      # PlugData listening port
    tilt_smooth_window=5            # Tilt angle smoothing
)
```

---

### 5. PlugData Configuration

#### Install PlugData
- Download from [plugdata.org](https://plugdata.org)
- Or use Pure Data with `netreceive`

#### Create PlugData Patch (or use provided synth1.pd)
```
[netreceive -u -l 9999]
    |
[oscparse]
    |
[route /synth/pitch /synth/mode /synth/vibrato /synth/volume /synth/panic]
    |
    +--→ [print pitch]
    +--→ [print mode]
    +--→ [print vibrato]
    +--→ [print volume]
    +--→ [print panic]
```

#### Test PlugData Connectivity
1. Start PlugData
2. Put patch in edit mode
3. Right-click `netreceive` → Open Inspector
4. Verify port = 9999
5. Check "Active" checkbox
6. Send test message from Python:
   ```bash
   python -c "
   from pythonosc import udp_client
   client = udp_client.SimpleUDPClient('127.0.0.1', 9999)
   client.send_message('/synth/pitch', 0.5)
   print('Test message sent!')
   "
   ```

---

## Advanced Configuration

### Gesture Threshold Tuning

#### File: `utils/gesture_classifier.py`

Adjust finger extension detection:
```python
self.extended_threshold = 0.05  # Increase for more strict detection
```

**Effect:**
- Lower values (0.02-0.05): Easily triggered, may misclassify
- Higher values (0.08-0.15): Strict, requires clear extension

### Distance Sensor Range Mapping

#### File: `utils/arduino_handler.py`

```python
self.min_distance = 5.0    # Closest distance (cm) = 1.0 pitch
self.max_distance = 50.0   # Farthest distance (cm) = 0.0 pitch
```

**To customize for your space:**
1. Position hand at closest comfortable distance → record value
2. Position hand at farthest comfortable distance → record value
3. Update `min_distance` and `max_distance`

### Smoothing Filter Windows

Larger windows = smoother but more lag
Smaller windows = responsive but jittery

```python
# In main.py:
arduino = ArduinoHandler(smooth_window=10)    # 10 samples = smoother
osc = OSCManager(tilt_smooth_window=10)       # 10 samples = smoother

# Typical: 5-10 for smooth response with minimal latency
```

### Camera Resolution & Frame Rate

Edit `main.py`:
```python
cap = cv2.VideoCapture(0)
# Set resolution:
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
# Set FPS:
cap.set(cv2.CAP_PROP_FPS, 30)
```

### MediaPipe Confidence Threshold

```python
options = vision.HandLandmarkerOptions(
    base_options=base_options,
    num_hands=1,
    min_hand_detection_confidence=0.7  # 0.5 (loose) to 0.9 (strict)
)
```

---

## Performance Optimization

### Reduce CPU Usage
- Lower webcam resolution
- Reduce frame rate: `cv2.waitKey(10)` instead of `cv2.waitKey(5)`
- Increase smoothing window (fewer OSC updates)
- Disable visualization in production

### Reduce Latency
- Increase frame rate: `cv2.waitKey(1)`
- Decrease smoothing window (fewer averaged samples)
- Use direct OSC without additional processing

---

## Troubleshooting

### Issue: "No module named 'mediapipe'"
**Solution:**
```bash
pip install --upgrade mediapipe
# If issues persist:
pip install --force-reinstall mediapipe
```

### Issue: Arduino not responding
**Diagnosis:**
1. Check serial port: `ls /dev/tty.*`
2. Test with terminal: `screen /dev/cu.usbserial-XXXX 9600`
3. Verify Arduino IDE sees device
4. Try different USB cable

**Solution:**
- Update serial port in `main.py`
- Reboot Arduino: unplug/replug USB
- Check for other programs using serial port

### Issue: Poor gesture recognition
**Solutions:**
- Improve lighting (use desk lamp)
- Keep hand fully in frame
- Remove reflective objects (jewelry)
- Calibrate hand size with the model:
  ```python
  # Increase confidence threshold:
  min_hand_detection_confidence=0.85
  ```

### Issue: PlugData not receiving OSC
**Diagnosis:**
1. Start PlugData with debugging: `pd -verbose`
2. Monitor OSC messages:
   ```bash
   python main.py | grep "sending"
   ```
3. Check firewall isn't blocking UDP 9999

**Solution:**
```bash
# Test OSC directly:
python -c "
from pythonosc import udp_client
c = udp_client.SimpleUDPClient('127.0.0.1', 9999)
c.send_message('/synth/pitch', 0.5)
"
# In PlugData, use [print] to verify reception
```

### Issue: Jittery/noisy control values
**Solutions:**
- Increase smoothing window size
- Improve hand position stability
- Use better lighting
- Add additional smoothing in PlugData patch

### Issue: High CPU usage (>30%)
**Solutions:**
- Reduce webcam resolution
- Lower frame rate: `cv2.waitKey(10)` or `cv2.waitKey(20)`
- Turn off landmark visualization
- Close other applications

---

## Testing Checklist

### Hardware Test
- [ ] Arduino reports distance values via serial
- [ ] Distance values range 5-50cm
- [ ] Distance updates ~30 times per second
- [ ] Webcam displays hand properly

### Software Test
- [ ] `python main.py` starts without errors
- [ ] "✓ Hand Detected" appears on screen
- [ ] "✓ Arduino" connection shows
- [ ] Gesture mode changes when moving fingers

### PlugData Test
- [ ] PlugData receives `/synth/pitch` messages
- [ ] PlugData receives `/synth/mode` changes
- [ ] PlugData receives `/synth/vibrato` values
- [ ] Audio updates with hand movements

### Integration Test
- [ ] Move hand closer → pitch increases
- [ ] Change hand posture (thumb/index variations) → mode 0-4 switches correctly
- [ ] Tilt hand left/right → vibrato changes
- [ ] Remove hand → volume goes to 0 (safety)
- [ ] Press 'q' → graceful shutdown, panic sent

---

## Production Deployment

### Before Performance
1. **Test in actual venue:**
   - Verify lighting conditions
   - Test wireless stability if applicable
   - Check floor space for safe hand movement

2. **Optimize for stability:**
   ```python
   smooth_window=8-10        # More stable
   min_confidence=0.8        # Higher threshold
   cv2.waitKey(10)           # Slightly lower frame rate
   ```

3. **Create failsafe:**
   - Keep keyboard nearby for 'q' exit
   - Test `Ctrl+C` interrupt handling
   - Monitor on-screen status indicators

4. **Document setup:**
   - Camera position (height, distance, angle)
   - Arduino port name (changes between systems!)
   - PlugData patch file location
   - Keyboard mapping for emergencies

---

## Resetting to Defaults

```python
# Gesture classification defaults
gesture_classifier = GestureClassifier()
# extended_threshold = 0.05

# Arduino defaults
arduino = ArduinoHandler(
    port='/dev/cu.usbserial-1130',
    baudrate=9600,
    smooth_window=5,
    min_distance=5.0,
    max_distance=50.0
)

# OSC defaults
osc = OSCManager(
    ip='127.0.0.1',
    port=9999,
    tilt_smooth_window=5
)

# MediaPipe defaults
min_hand_detection_confidence=0.7
num_hands=1
```

---

## Need Help?

1. Check **README.md** for overview
2. Review code **comments** in each module
3. Test each component **independently**
4. Check **on-screen diagnostics** (status indicators)
5. Monitor **print statements** for debugging

---

**Last Updated:** 2026-03-15
