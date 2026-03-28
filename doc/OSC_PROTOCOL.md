# OSC Protocol Documentation

## Overview

This project sends OSC over UDP from Python to PlugData/Pure Data.

- Protocol: OSC 1.0 over UDP
- Target: 127.0.0.1
- Port: 9999
- Runtime update loop: about 30 Hz

---

## Active OSC Messages

| Address | Type | Range | Sent When | Source |
|---|---|---|---|---|
| /synth/pitch | float | 0.0-1.0 | Continuous (valid distance) | Arduino distance sensor |
| /synth/mode | int | 0-4 | On change only | Hand posture classifier |
| /synth/vibrato | float | 0.0-1.0 | Continuous | Hand roll angle |
| /synth/volume | float | 0.0-1.0 | On significant change | Hand presence safety gate |
| /synth/panic | int | 0 or 1 | Shutdown or emergency | Controller safety logic |

Notes:
- /synth/expression is currently not emitted by main.py or osc_manager.py.
- mode is normalized in code with int(mode) % 6, but current classifier outputs 0-4.

---

## Mode Map (Current Classifier)

| Mode | Gesture Pattern | Description |
|---|---|---|
| 0 | Open hand | All non-thumb fingers extended (tilt-aware relaxation supported) |
| 1 | Closed fist | No extended fingers |
| 2 | Thumb only | Fist + thumb extension |
| 3 | Thumb + index | Two-feature gesture |
| 4 | Thumb + index + middle | Three-feature gesture |

---

## Value Mapping

### /synth/pitch

- Input: smoothed distance in cm
- Valid sensing range in code: 5 to 50 cm
- Output: normalized float in [0.0, 1.0]

Reference mapping:
- Near (about 5 cm) -> 1.0
- Mid (about 27.5 cm) -> about 0.5
- Far (about 50 cm) -> 0.0

### /synth/vibrato

- Input: hand roll angle in degrees
- Smoothing: moving average (tilt_smooth_window, default 5)
- Mapping in code: abs(smoothed_roll) / 60, clamped to [0.0, 1.0]

### /synth/volume

- Hand detected -> typically 1.0
- Hand lost after being present -> send 0.0
- Sent only when change is significant (>= 0.01)

### /synth/panic

- Sent in shutdown path
- Typical sequence:
  - /synth/volume 0.0
  - /synth/panic 1

---

## Example Sequence

Tracking frame:

```text
/synth/pitch 0.63
/synth/mode 3
/synth/vibrato 0.41
/synth/volume 1.0
```

Hand lost:

```text
/synth/volume 0.0
```

Graceful shutdown:

```text
/synth/volume 0.0
/synth/panic 1
```

---

## PlugData Routing Example

```pd
[netreceive -u -b 9999]
|
[oscparse]
|
[list trim]
|
[route synth]
|
[route pitch mode vibrato volume panic]
```

This matches synth/synth1.pd.

---

## Integration Checklist

- Receiver listens on UDP 9999.
- Incoming addresses are /synth/* (or route synth then pitch/mode/vibrato/volume/panic).
- Do not rely on /synth/expression unless you re-enable it in Python code.
- Handle mode range 0-4 in current build.
- Treat /synth/panic 1 as hard mute or reset.

---

Updated: 2026-03-27
