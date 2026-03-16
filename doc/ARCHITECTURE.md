# System Architecture & Data Flow

## Complete Data Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          INPUT ACQUISITION LAYER                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────────┐         ┌──────────────────┐         ┌──────────────────┐
│   WEBCAM (USB)   │         │   ARDUINO (TTL)  │         │   MEDIAPIPE      │
│                  │         │                  │         │   (GPU/CPU)      │
│  • 30 FPS video  │         │ • HC-SR04 sensor │         │                  │
│  • 1280x720 RGB  │         │ • 9600 baud UART │         │ • Hand tracking  │
│  • OpenCV cap    │         │ • Distance: 5-50cm          │ • 21 landmarks  │
└────────┬─────────┘         └────────┬─────────┘         └────────┬─────────┘
         │                            │                            │
         ├──────────────┬─────────────┴────────────┬────────────────┤
         │              │                          │                │
         v              v                          v                v

┌─────────────────────────────────────────────────────────────────────────────┐
│                       PROCESSING & CLASSIFICATION LAYER                      │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌─────────────────────────┐
    │  GESTURE CLASSIFIER     │
    │  (gesture_classifier.py)│
    ├─────────────────────────┤
    │ Input: Hand landmarks   │
    │ • Finger extension check│
    │ • Thumb detection       │
    │ • Peace sign detection  │
    │                         │
    │ Output: Gesture State   │
    │ • Mode: 0-5 (discrete)  │
    │ • Roll angle (degrees)  │
    │ • Pitch angle (degrees) │
    └────────────┬────────────┘
                 │
      ┌──────────┴──────────┐
      │                     │
      v                     v
   MODE (0-5)        TILT ANGLES
   DISCRETE          Continuous
     STATE           (° degrees)

    ┌─────────────────────────┐
    │  ARDUINO HANDLER        │
    │  (arduino_handler.py)   │
    ├─────────────────────────┤
    │ Input: Serial distance  │
    │ • Read UART buffer      │
    │ • Parse distance value  │
    │ • Smoothing filter (MA) │
    │                         │
    │ Output: Normalized      │
    │ • Raw: cm (5-50)        │
    │ • Smoothed: cm          │
    │ • Normalized: 0.0-1.0   │
    └────────────┬────────────┘
                 │
                 v
            PITCH VALUE
            (0.0-1.0)

┌─────────────────────────────────────────────────────────────────────────────┐
│                          CONVERSION & SMOOTHING                              │
└─────────────────────────────────────────────────────────────────────────────┘

    MODE 0-5                    TILT ROLL              TILT PITCH
    (unchanged)                 (angle → 0-1)         (angle → 0-1)
        │                            │                     │
        │                    ┌───────┴────────┐            │
        │                    │                │            │
        │                  [+90]°  [-90]°    │            │
        │                    │                │            │
        │                    v                v            v
        │                  ÷180              ÷180
        │                    │                │
        │    Moving Average Filter           │
        │    (5 samples)                      │
        │                    │                │
        │                    v                v
        │              0.0-1.0            0.0-1.0
        │                    │                │
        │              VIBRATO          EXPRESSION
        │              CONTROL          CONTROL

┌─────────────────────────────────────────────────────────────────────────────┐
│                        OSC MESSAGE TRANSMISSION LAYER                        │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌──────────────────────────┐
    │   OSC MANAGER            │
    │   (osc_manager.py)       │
    ├──────────────────────────┤
    │ Input: All 5 parameters  │
    │ • Pitch (float)          │
    │ • Mode (int)             │
    │ • Vibrato (float)        │
    │ • Expression (float)     │
    │ • Volume (float)         │
    │                          │
    │ Protocol: OSC 1.0        │
    │ Transport: UDP           │
    │ Target: 127.0.0.1:9999   │
    │ Rate: 30 Hz + events     │
    └────────────┬─────────────┘
                 │
    ┌────────────┴──────────────────┬─────────────┬────────────┬──────────┐
    │                               │             │            │          │
    v                               v             v            v          v

/synth/pitch               /synth/mode          /synth/vibrato
{0.0-1.0}                 {0-5}               {0.0-1.0}
Every frame               On change           Every frame

    + 

/synth/expression        /synth/volume
{0.0-1.0}               {0.0-1.0}
Every frame             On change + safety

┌─────────────────────────────────────────────────────────────────────────────┐
│                          NETWORK & UDP TRANSPORT                             │
└─────────────────────────────────────────────────────────────────────────────┘

    Python Controller (127.0.0.1:random)
    UDP Client
            │
            │ OSC over UDP
            │ Localhost socket
            │ ~5-10 KB/sec
            │ <5ms latency
            │
            v
    PlugData/PD (127.0.0.1:9999)
    UDP Server
    netreceive -u -l 9999

┌─────────────────────────────────────────────────────────────────────────────┐
│                    PLUGDATA RECEPTION & SYNTHESIS LAYER                     │
└─────────────────────────────────────────────────────────────────────────────┘

    [netreceive -u]
            │
    [oscparse]
            │
    [route /synth/pitch /synth/mode /synth/vibrato /synth/expression /synth/volume]
            │
            ├──────────────┬────────────┬────────────┬────────────┬──────────┐
            │              │            │            │            │          │
            v              v            v            v            v          v
        [*220]        [sel 0 1 2]  [*8Hz]      [*envelope]   [*~volume]  [print]
        [osc~]        ...mode...  [osc~LFO] [line~ADSR]    [dac~]
                                  [pitch+]   [filter]       Audio Out
        Carrier
        Oscillator
            │
            └────────────────────┬────────────────────────────┐
                                 │                            │
                            [*~EXPRESSION]               [*~VIBRATO]
                                 │                            │
                                 └────────────┬───────────────┘
                                              │
                                              v
                                        [*~volume]
                                              │
                                              v
                                         [dac~]
                                              │
                                              v
                                         SPEAKERS
```

---

## Detailed Component Interactions

### 1. Input Acquisition (0-5ms)

**Webcam → MediaPipe**
```
Frame capture (30 FPS, 33ms)
    ↓
Convert BGR → RGB
    ↓
Create mp.Image object
    ↓
hand_landmarker.detect()
    ↓
Returns: hand_landmarks, handedness
    ↓
Filter: Right hand only (camera mirror)
```

**Arduino → Distance Value**
```
Trigger pulse (10 µs)
    ↓
Measure echo time (~380 µs @ 50cm)
    ↓
Calculate: distance = (duration/2)/29
    ↓
Validate: 5cm < distance < 50cm
    ↓
Send via Serial UART
    ↓
Python reads from buffer
```

### 2. Gesture Classification (5-10ms)

**Classify Posture (0-5)**
```
For each finger: check if extended
    ↓
Count extended fingers (0-4)
    ↓
Detect thumb orientation
    ↓
Apply classification rules
    ↓
Return discrete mode 0-5
```

**Calculate Roll Angle**
```
Vector: wrist (0) → middle tip (12)
    ↓
dx = x_tip - x_wrist
dy = y_tip - y_wrist
    ↓
angle = atan2(dy, dx) - 90°
    ↓
Normalize to -90° to +90°
    ↓
Return degrees
```

**Calculate Pitch Angle**
```
Y-distance: wrist (0) → middle MCP (9)
    ↓
Map forward/backward to -90° to +90°
    ↓
Return degrees
```

### 3. Smoothing & Normalization (3-5ms)

**Distance Smoothing**
```
Raw distance value
    ↓
Add to 5-sample buffer
    ↓
Average: sum(buffer) / len(buffer)
    ↓
Normalize: (value - 5) / (50 - 5)
    ↓
Clamp: max(0.0, min(1.0, result))
```

**Angle Smoothing**
```
Raw angle (degrees)
    ↓
Add to 5-sample buffer
    ↓
Average: sum(buffer) / len(buffer)
    ↓
Map to 0-1: (angle + 90) / 180
    ↓
Clamp: max(0.0, min(1.0, result))
```

### 4. OSC Message Construction (2-3ms)

**Build Message Batch**
```
Prepare OSC packet:
    /synth/pitch {float 0.0-1.0}
    /synth/mode {int 0-5}
    /synth/vibrato {float 0.0-1.0}
    /synth/expression {float 0.0-1.0}
    /synth/volume {float 0.0-1.0}
    
Encode as OSC binary format
Send via UDP to 127.0.0.1:9999
```

### 5. PlugData Reception (~1-3ms network)

**OSC Parse & Route**
```
[netreceive] captures UDP packet
    ↓
[oscparse] decodes OSC binary
    ↓
[route] splits into 5 streams
    ↓
Each stream goes to corresponding control
```

**Audio Generation (~10ms processing)**
```
Pitch input → [osc~] frequency
Mode input → signal chain selector
Vibrato → LFO generator
Expression → ADSR envelope
Volume → output multiplier
    ↓
Output audio to [dac~]
    ↓
SPEAKERS
```

---

## Latency Analysis

```
Component                          Time (ms)
─────────────────────────────────────────────
Webcam capture                     0-16
MediaPipe inference                10-30 (GPU)
Arduino serial read                <1
Gesture classification             2-5
Smoothing & normalization          1-3
OSC message creation               2-3
UDP transmission                   <1 (local)
PlugData OSC parsing               1-2
PlugData audio generation          1-3 (next buffer)
─────────────────────────────────────────────
TOTAL LATENCY (best case):         ~20-30ms
TOTAL LATENCY (typical):           50-80ms
TOTAL LATENCY (worst case):        100-120ms

Notes:
- MediaPipe latency varies: GPU ~10ms, CPU ~30ms
- Buffer size affects PlugData latency
- Network latency minimal for localhost
- Smoothing adds 33ms per filter window
```

---

## Data Types & Conversions

### Hand Landmarks
```
MediaPipe LandmarkList (21 landmarks per hand)
  └─ Landmark (normalized x, y coordinates)
       ├─ x: 0.0-1.0 (left to right)
       ├─ y: 0.0-1.0 (top to bottom)
       └─ z: 0.0-1.0 (depth, camera to hand)
```

### Gesture State
```python
gesture_mode: int
  0: Open Hand
  1: Closed Fist
  2: Fist + Thumb
  3: Fist + Index
  4: Fist + Thumb + Index
  5: Peace Sign
```

### Angles
```
Roll (X-axis rotation):  -90° to +90° (left to right)
Pitch (Y-axis rotation): -90° to +90° (back to forward)

After normalization: 0.0 to 1.0 (linear mapping)
```

### OSC Arguments
```
/synth/pitch           f      float  [0.0, 1.0]
/synth/mode            i      int    [0, 5]
/synth/vibrato         f      float  [0.0, 1.0]
/synth/expression      f      float  [0.0, 1.0]
/synth/volume          f      float  [0.0, 1.0]
/synth/panic           i      int    [0, 1]
```

---

## Frame-by-Frame Timeline

**Frame N (T = 0ms)**
```
00ms: Webcam captures frame
03ms: Convert to RGB, create mp.Image
05ms: MediaPipe hand_landmarker.detect()
25ms: Gesture classification complete
27ms: Arduino read from serial buffer
28ms: Smoothing & normalization complete
30ms: OSC messages created
31ms: UDP packets sent
32ms: PlugData receives & parses
33ms: PlugData generates audio (~20ms in future)
33ms: Frame N+1 begins

Total per frame: 33ms (@ 30 FPS)
```

---

## Safety & Error Handling

### Hand Loss Detection
```
if not hand_detected:
    if hand_was_detected_last_frame:
        send_volume(0.0)  # Mute immediately
        print("Hand lost - muting")
```

### Distance Validation
```
if 5 <= distance <= 50:
    valid = True
else:
    value = clamp(0, 1, normalized)  # Safe default
```

### Serial Timeout
```
if not arduino.is_connected:
    use_default_pitch(0.5)  # Middle value
    retry_connection_next_frame()
```

### OSC Failure
```
try:
    osc.send_message(address, value)
except Exception:
    log_error("OSC send failed")
    continue_without_audio_control()
```

---

## Performance Profiling

### CPU Usage
```
Component                  CPU % (single core)
─────────────────────────────────────────────
MediaPipe (GPU)            5-10%
MediaPipe (CPU)            25-40%
Gesture Classification     1-2%
Arduino Serial I/O         <0.5%
OSC Transmission           <0.5%
OpenCV drawing             2-3%
─────────────────────────────────────────────
TOTAL (GPU):               10-15%
TOTAL (CPU):               30-50%
```

### Memory Usage
```
Component                  Memory
──────────────────────────────────
MediaPipe model            ~250 MB
Video buffer               ~10 MB
Python process             ~150 MB
──────────────────────────────────
TOTAL:                     ~400-500 MB
```

### Network Usage
```
Messages per second:       90-120
Bytes per message:         40-60
Total bandwidth:           5-10 KB/sec
```

---

## Optimization Tips

1. **Reduce latency:**
   - Use GPU (CUDA/Metal) for MediaPipe
   - Reduce smoothing window
   - Use lower video resolution

2. **Reduce CPU:**
   - Lower frame rate (cv2.waitKey(10))
   - Disable landmark visualization
   - Use CPU-efficient preprocessing

3. **Improve stability:**
   - Increase smoothing window
   - Better lighting
   - Higher MediaPipe confidence threshold

---

**Last Updated:** 2026-03-15
