# OSC Protocol Documentation

## Overview

This system uses **Open Sound Control (OSC)** to communicate between the Python gesture controller and PlugData/Pure Data synthesis engine via UDP.

- **Protocol:** OSC 1.0 over UDP
- **Target:** 127.0.0.1 (localhost)
- **Port:** 9999
- **Update Rate:** ~30Hz (33ms per frame)

---

## OSC Message Format

### General Structure
```
/synth/{parameter} {value}
└─────────────────────────┘
   OSC Address   OSC Argument
```

### Message Types

| # | Address | Type | Range | Function | Source |
|----|---------|------|-------|----------|--------|
| 1 | `/synth/pitch` | float | 0.0–1.0 | Fundamental frequency control | Arduino distance sensor |
| 2 | `/synth/mode` | int | 0–5 | Synthesis mode (discrete state) | Hand gesture classification |
| 3 | `/synth/vibrato` | float | 0.0–1.0 | LFO/vibrato depth | Hand roll (tilt) |
| 4 | `/synth/expression` | float | 0.0–1.0 | Amplitude/filter modulation | Hand pitch (tilt) |
| 5 | `/synth/volume` | float | 0.0–1.0 | Master volume level | Safety gate / hand detection |
| 6 | `/synth/panic` | int | 0 or 1 | Emergency stop signal | Shutdown sequence |

---

## Detailed Message Documentation

### 1. `/synth/pitch` — Fundamental Pitch Control

**Type:** `float`  
**Range:** `0.0` to `1.0`  
**Update Rate:** ~30Hz continuous  
**Source:** Arduino HC-SR04 distance sensor  

**Mapping:**
```
Arduino Distance (cm)  →  Normalized Value
─────────────────────      ────────────────
5 cm (closest)         →   1.0 (highest pitch)
27.5 cm (mid-point)    →   0.5 (middle pitch)
50 cm (farthest)       →   0.0 (lowest pitch)
```

**Example Messages:**
```
/synth/pitch 0.0  # Low pitch (far away)
/synth/pitch 0.5  # Mid pitch (arm's length)
/synth/pitch 1.0  # High pitch (close)
```

**PlugData Implementation:**
```pd
[netreceive -u]
    |
[oscparse]
    |
[route /synth/pitch]
    |
[* 220]  # Scale 0-1 to 220Hz (can be 0-4kHz)
    |
[osc~]
```

**Notes:**
- **Smoothing:** Moving average filter (5 samples) reduces jitter
- **Clamping:** Values outside 5–50cm range are clipped to [0.0, 1.0]
- **Frequency Map:** Typically maps to 0–4kHz or 0–8kHz depending on PlugData patch design

---

### 2. `/synth/mode` — Synthesis Mode Selection

**Type:** `int`  
**Range:** `0` to `5` (6 modes total)  
**Update Rate:** Only sent on change (event-driven)  
**Source:** MediaPipe hand gesture classification  

**Mode Map:**

| Mode | Gesture | Description | Recommended Audio Effect |
|------|---------|-------------|--------------------------|
| **0** | Open Hand | All fingers extended | Complex modulation / Full harmonics / All partials active |
| **1** | Closed Fist | No fingers extended | Simple sine or square wave / Single carrier |
| **2** | Fist + Thumb | Thumb extended | Basic + sub-octave color (add -12 semitones) |
| **3** | Fist + Index | Index finger extended | Basic + fifth/overtones (add +7 semitones or harmonics) |
| **4** | Fist + Thumb + Index | Both pointing | Basic + both color effects (sub + overtones combined) |
| **5** | Peace Sign | Index & middle extended | Special FX mode (reverb, delay, freeze, granular) |

**Example Messages:**
```
/synth/mode 1  # Closed fist: basic sine wave
/synth/mode 0  # Open hand: full harmonics
/synth/mode 5  # Peace sign: activate effects
```

**PlugData Implementation:**
```pd
[route /synth/mode]
    |
[sel 0 1 2 3 4 5]  # Route to 6 different signal chains
    |
    +--→ [osc~ with 16 partials]  # mode 0
    +--→ [osc~]                    # mode 1
    +--→ [osc~ + sub oscillator]   # mode 2
    +--→ [osc~ + harmonics]        # mode 3
    +--→ [combined effects]        # mode 4
    +--→ [reverb/delay chain]      # mode 5
```

**Notes:**
- **No redundant messages:** Mode only sent when changing (reduces OSC traffic)
- **Priority:** Highest in gesture hierarchy (always sent before continuous parameters)
- **Safety:** Defaults to mode 1 (simple sine wave) if detection fails

---

### 3. `/synth/vibrato` — Roll/LFO Modulation

**Type:** `float`  
**Range:** `0.0` to `1.0`  
**Update Rate:** ~30Hz continuous  
**Source:** Hand roll angle (side-to-side tilt)  

**Mapping:**
```
Hand Orientation    →  Normalized Value
────────────────        ────────────────
Tilted far left     →   1.0 (max LFO depth)
Vertical/straight   →   0.5 (mid LFO depth)
Tilted far right    →   0.0 (min LFO depth)
```

**Tilt Angle Calculation:**
```
Vector: wrist (landmark 0) → middle finger tip (landmark 12)
Angle in degrees: -90° (full left) to +90° (full right)
Normalized: (angle + 90) / 180 → 0.0 to 1.0
```

**Example Messages:**
```
/synth/vibrato 0.0  # Right tilt: vibrato off
/synth/vibrato 0.5  # Vertical: moderate vibrato
/synth/vibrato 1.0  # Left tilt: strong vibrato
```

**PlugData Implementation:**
```pd
[route /synth/vibrato]
    |
[* 5]  # Scale 0-1 to 0-5 Hz LFO rate
    |
[osc~]  # LFO generator
    |
[* 500]  # LFO depth control (scale to filter/pitch range)
    |
[+~ 440]  # Modulate pitch around 440Hz
```

**Notes:**
- **Smoothing:** 5-sample moving average reduces hand shake artifacts
- **Natural Range:** Humans typically tilt ±45°, maps to full 0-1 range
- **Audio Use:** LFO depth, vibrato amount, filter modulation, pan control

---

### 4. `/synth/expression` — Pitch/Envelope Control

**Type:** `float`  
**Range:** `0.0` to `1.0`  
**Update Rate:** ~30Hz continuous  
**Source:** Hand pitch angle (forward/backward tilt)  

**Mapping:**
```
Hand Orientation        →  Normalized Value
────────────────            ────────────────
Tilted backward         →   0.0 (closed/min)
Neutral/horizontal      →   0.5 (mid position)
Tilted forward          →   1.0 (open/max)
```

**Pitch Angle Calculation:**
```
Metric: Middle MCP depth relative to wrist
Angle in degrees: -90° (far) to +90° (near)
Normalized: (angle + 90) / 180 → 0.0 to 1.0
```

**Example Messages:**
```
/synth/expression 0.0  # Hand back: envelope closed
/synth/expression 0.5  # Hand neutral: mid envelope
/synth/expression 1.0  # Hand forward: envelope open
```

**PlugData Implementation:**
```pd
[route /synth/expression]
    |
[* 32767]  # Scale to ADSR envelope
    |
[line~]  # Smooth envelope generator
    |
[*~]  # Multiply with oscillator
```

**Notes:**
- **Natural Interaction:** Forward gesture naturally feels like "opening" the sound
- **Smoothing:** 5-sample moving average for stable envelope control
- **Use Cases:** 
  - Filter cutoff frequency
  - Amplitude envelope
  - Harmonic distribution control
  - Reverb wet/dry mix

---

### 5. `/synth/volume` — Safety Master Volume Gate

**Type:** `float`  
**Range:** `0.0` to `1.0`  
**Update Rate:** ~0.5Hz (only on significant changes)  
**Source:** Hand detection status  

**Values:**
```
Hand Status     →  Volume Value
───────────────    ──────────────
Hand detected   →  1.0 (full volume)
Hand missing    →  0.0 (mute/safety)
```

**Example Messages:**
```
/synth/volume 1.0  # Hand in frame: unmute
/synth/volume 0.0  # Hand lost: safety mute
```

**PlugData Implementation:**
```pd
[route /synth/volume]
    |
[*~]  # Multiply with all audio signals
    |
[dac~]  # Send to output
```

**Notes:**
- **Safety Feature:** Prevents "stuck notes" if performer leaves frame
- **Hysteresis:** Only sends when change > 0.1 (hysteresis) to reduce traffic
- **Latency:** ~66ms (2 frame) detection lag for responsiveness

---

### 6. `/synth/panic` — Emergency Stop Signal

**Type:** `int`  
**Values:** `0` (normal) or `1` (stop)  
**Update Rate:** Once on shutdown  
**Source:** Program termination / safety shutdown  

**Example Messages:**
```
/synth/panic 0  # Normal operation
/synth/panic 1  # EMERGENCY STOP: Release all notes, silence output
```

**PlugData Implementation:**
```pd
[route /synth/panic]
    |
[sel 1]  # Trigger on 1
    |
[; pd dsp 0]  # Disable audio
[; *1 0]      # Send 0 to all controls
```

**Notes:**
- **Use Cases:**
  - Graceful shutdown
  - Safety emergency stop
  - Stuck note recovery
- **Should:**
  - Stop all audio generation
  - Release all ADSR envelopes
  - Zero all filter/modulation parameters
  - Reset to safe defaults

---

## Message Timing & Synchronization

### Frame Timing
```
Time (ms)  Event
─────────  ──────────────────────────────────────
0          MediaPipe detects hand + Arduino reads distance
~3         Calculate gestures, classify posture, compute angles
~5         Send OSC batch
~10        PlugData receives and processes
~33        (Next frame)
```

### Typical OSC Message Sequence (per frame)
```
1. /synth/pitch {float}         # Always sent (continuous)
2. /synth/mode {int}            # Only if changed
3. /synth/vibrato {float}       # Always sent (continuous)
4. /synth/expression {float}    # Always sent (continuous)
5. /synth/volume {float}        # Only if significantly changed
```

### Total OSC Traffic
- **Typical:** 3–4 messages per frame × 30 fps = 90–120 messages/sec
- **Bandwidth:** ~5–10 KB/sec (negligible for local UDP)
- **Latency:** <5ms round-trip for localhost

---

## Common PlugData Patterns

### Basic Receiver Setup
```pd
[netreceive -u -l 9999]
    |
[oscparse]
    |
[route /synth/pitch /synth/mode /synth/vibrato /synth/expression /synth/volume /synth/panic]
```

### Frequency Mapping (0-1 to Hz)
```pd
# Map 0.0→100Hz, 0.5→440Hz, 1.0→4000Hz
[route /synth/pitch]
    |
[* 3900]  # Scale to 0-3900 Hz
    |
[+ 100]   # Offset by 100 Hz
    |
[osc~]
```

### Mode-based Signal Router
```pd
[route /synth/mode]
    |
[sel 0 1 2 3 4 5]
    |
    +--→ [part0~]  # mode 0: all partials
    +--→ [osc~]    # mode 1: sine
    +--→ [sub~]    # mode 2: sub
    +--→ [harm~]   # mode 3: harmonics
    etc...
```

### LFO from Vibrato Control
```pd
[route /synth/vibrato]
    |
[* 8]      # Scale 0-1 to 0-8 Hz
    |
[osc~]     # LFO generator
    |
[* 1000]   # LFO depth (for pitch mod)
    |
[+~]       # Add to oscillator pitch
```

---

## Testing & Debugging

### Verify OSC Reception in PlugData
```pd
[netreceive -u -l 9999]
    |
[oscparse]
    |
[print OSC]  # Print all incoming messages
```

### Test from Command Line
```bash
# Send test message to PlugData
python3 -c "
from pythonosc import udp_client
client = udp_client.SimpleUDPClient('127.0.0.1', 9999)
client.send_message('/synth/pitch', 0.75)
print('Sent: /synth/pitch 0.75')
"
```

### Monitor OSC Traffic (macOS/Linux)
```bash
# Using tcpdump to capture UDP packets on port 9999
sudo tcpdump -i lo -A 'udp port 9999'
```

### Enable OSC Debugging in Python
```python
# In main.py, add after OSC initialization:
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## OSC Specifications Reference

- **OSC 1.0 Standard:** http://opensoundcontrol.org/spec-1_0
- **Python OSC Library:** `python-osc` package
- **Pure Data:** `netreceive`, `oscparse`, `route`
- **PlugData:** Native OSC support via objects

---

## Troubleshooting OSC Issues

### Messages Not Received
1. Verify PlugData `netreceive -u -l 9999` is active
2. Check port 9999 is not blocked by firewall
3. Test with simple print receivers
4. Monitor with tcpdump

### Garbled/Invalid Messages
1. Ensure correct OSC address format (starts with `/`)
2. Verify correct data type (int vs float)
3. Check network MTU (usually not an issue for localhost)

### High Latency
1. Use localhost (127.0.0.1) instead of network IP
2. Reduce filter smoothing window
3. Lower frame rate if not needed
4. Check CPU usage on PlugData

### Stuck Notes
1. Ensure `/synth/volume` gate is working
2. Check for unhandled `/synth/panic` messages
3. Verify ADSR envelopes in PlugData have proper release

---

**Last Updated:** 2026-03-15
