# Requirements Fulfillment Checklist

## Scope
Python-based gesture-to-OSC controller with MediaPipe hand tracking and Arduino distance sensing.

Updated: 2026-03-27

---

## 1) Inputs

### 1.1 Arduino distance input
- Status: Met
- Evidence:
  - `utils/arduino_handler.py` reads serial distance values.
  - Distance is smoothed and normalized to 0.0-1.0.
  - Mapping sent to `/synth/pitch`.

### 1.2 MediaPipe hand tracking (right hand)
- Status: Met
- Evidence:
  - `main.py` uses handedness filtering and processes right-hand stream.
  - Hand landmarks drive posture classification and roll extraction.

---

## 2) Discrete Gesture Mapping

### Gesture state output
- Status: Met (current implementation uses 5 states)
- Current mode range: 0-4
- Evidence:
  - `utils/gesture_classifier.py::classify_posture`
  - `utils/osc_manager.py::send_mode`

Current state map:
- 0: Open hand
- 1: Closed fist
- 2: Thumb-only
- 3: Thumb + index
- 4: Thumb + index + middle

---

## 3) Continuous Modulation

### 3.1 Roll to vibrato
- Status: Met
- Evidence:
  - Roll extracted via `get_tilt_roll(...)`
  - Smoothed in `OSCManager`
  - Sent as `/synth/vibrato`

### 3.2 Pitch to expression
- Status: Present in utility code, currently disabled in runtime path
- Evidence:
  - `get_tilt_pitch(...)` exists
  - `main.py` and `OSCManager` currently do not emit `/synth/expression`

---

## 4) OSC Output

- Status: Met
- Target: `127.0.0.1:9999`
- Active messages:
  - `/synth/pitch`
  - `/synth/mode`
  - `/synth/vibrato`
  - `/synth/volume`
  - `/synth/panic`

Note:
- `/synth/expression` is intentionally inactive in current runtime behavior.

---

## 5) Smoothing and Safety

### Smoothing
- Status: Met
- Evidence:
  - Distance smoothing buffer in `ArduinoHandler`
  - Roll smoothing buffer in `OSCManager`

### Safety
- Status: Met
- Evidence:
  - Hand loss sends `/synth/volume 0.0`
  - Shutdown sends `/synth/panic 1`

---

## 6) Deliverable Structure

- Status: Met
- Core files:
  - `main.py`
  - `utils/gesture_classifier.py`
  - `utils/arduino_handler.py`
  - `utils/osc_manager.py`
  - `arduino_handshake/arduino_handshake.ino`
  - `synth/synth1.pd`

---

## Verification

```bash
python test_system.py
python main.py
```

Expected:
- Components initialize, OSC values stream correctly, and safety mute/panic paths work.
