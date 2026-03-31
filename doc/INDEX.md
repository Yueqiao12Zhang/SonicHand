# Project Navigation Guide

## 📍 Start Here

**New to the project?** → Read [QUICKSTART.md](QUICKSTART.md) (5 minutes)

**Want the full picture?** → Read [README.md](README.md) (20 minutes)

**Need to troubleshoot?** → Use [test_system.py](test_system.py) then [CONFIGURATION.md](CONFIGURATION.md)

---

## 📚 Documentation Files

### Quick References
| File | Purpose | Read Time | Best For |
|------|---------|-----------|----------|
| **QUICKSTART.md** | 5-minute setup guide | 5 min | Getting started immediately |
| **README.md** | Complete system overview | 20 min | Understanding the full system |
| **COMPLETION_SUMMARY.md** | What was built and why | 10 min | Project overview |

### Detailed Guides
| File | Purpose | Read Time | Best For |
|------|---------|-----------|----------|
| **CONFIGURATION.md** | Setup, tuning, troubleshooting | 30 min | Configuration & debugging |
| **ARCHITECTURE.md** | Data flow, latency, performance | 20 min | Technical understanding |
| **OSC_PROTOCOL.md** | OSC message specification | 25 min | PlugData integration |

### Checklists
| File | Purpose | Use When |
|------|---------|----------|
| **REQUIREMENTS_FULFILLMENT.md** | Requirements vs implementation | Verifying completeness |

---

## 🔧 Executable Files

### Main Application
```bash
python main.py
```
**Runs:** Complete gesture-to-OSC controller
**Output:** Real-time video with gesture classification & OSC sending
**Exit:** Press 'q' or Ctrl+C

### Diagnostics
```bash
python test_system.py
```
**Tests:** All system components
**Output:** ✓/✗ status for each component
**Use:** Before running main.py to verify setup

---

## 📁 File Organization

```
Project Root
├── Code (Production)
│   ├── main.py                    ← RUN THIS
│   ├── requirements.txt           ← Python dependencies
│   │
│   ├── utils/ (Modules)
│   │   ├── gesture_classifier.py  ← 5-mode classification
│   │   ├── arduino_handler.py     ← Serial I/O
│   │   ├── osc_manager.py         ← OSC sending
│   │   └── webcam_capture.py      ← Legacy (optional)
│   │
│   ├── arduino_handshake/ (Hardware)
│   │   └── arduino_handshake.ino  ← Arduino firmware
│   │
│   └── synth/ (Synthesis)
│       └── synth1.pd              ← PlugData patch
│
└── Documentation
    ├── README.md                  ← START HERE
    ├── QUICKSTART.md              ← 5-minute setup
    ├── CONFIGURATION.md           ← Advanced tuning
    ├── OSC_PROTOCOL.md            ← OSC specification
    ├── COMPLETION_SUMMARY.md      ← Project summary
    ├── REQUIREMENTS_FULFILLMENT.md← Checklist
    └── INDEX.md                   ← This file
```

---

## 🚀 Quick Command Reference

### Setup
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Download MediaPipe model
python download_model.py

# 3. Verify system
python test_system.py
```

### Run
```bash
# Start the controller
python main.py

# Press 'q' to quit
```

### Debug
```bash
# Test individual components
python test_system.py              # Full system test
python -c "import mediapipe"       # Test MediaPipe
python -c "import cv2"             # Test OpenCV
python -c "from pythonosc import udp_client"  # Test OSC
```

---

## 📖 Reading Order

### For Musicians/Performers
1. [QUICKSTART.md](QUICKSTART.md)
2. [README.md](README.md)
3. Run `python main.py`

### For System Integrators
1. [README.md](README.md)
2. [CONFIGURATION.md](CONFIGURATION.md)
3. [ARCHITECTURE.md](ARCHITECTURE.md)

### For Developers
1. [README.md](README.md)
2. [ARCHITECTURE.md](ARCHITECTURE.md)
3. [OSC_PROTOCOL.md](OSC_PROTOCOL.md)
4. Study: `main.py`, `utils/` modules
5. Reference: [REQUIREMENTS_FULFILLMENT.md](REQUIREMENTS_FULFILLMENT.md)

### For Troubleshooters
1. Run: `python test_system.py`
2. Read: Relevant section in [CONFIGURATION.md](CONFIGURATION.md)
3. Check: Code comments in failing module

---

## 🔍 What Each Documentation File Contains

### README.md
- System architecture diagram
- Component descriptions
- Installation steps
- Running instructions
- Troubleshooting guide
- Performance notes
- File structure
- **Length:** 500+ lines

### QUICKSTART.md
- Prerequisites checklist
- 2-minute installation
- 1-minute configuration
- 2-minute first run
- Quick troubleshooting table
- **Length:** 100 lines

### CONFIGURATION.md
- Detailed setup instructions
- Arduino wiring diagram
- Serial port discovery
- Python environment setup
- Advanced tuning options
- Performance optimization
- Extensive troubleshooting
- **Length:** 400+ lines

### ARCHITECTURE.md
- Complete data pipeline diagram
- Component interactions
- Frame-by-frame timeline
- Latency analysis (20-120ms)
- CPU/memory usage
- Smoothing algorithms
- Performance profiling
- **Length:** 500+ lines

### OSC_PROTOCOL.md
- OSC message format
- 5 active-parameter specification (+ 1 disabled legacy channel)
- Type & range for each message
- Example PlugData code
- Testing procedures
- Common patterns
- **Length:** 400+ lines

### COMPLETION_SUMMARY.md
- What was built
- Features implemented
- File list (created/modified)
- Configuration options
- Performance characteristics
- Documentation index
- Version info
- **Length:** 400+ lines

### REQUIREMENTS_FULFILLMENT.md
- All requirements listed
- Implementation evidence
- Code references
- Verification procedures
- Deliverables checklist
- **Length:** 350+ lines

---

## 💡 Key Information at a Glance

### What It Does
Converts hand gestures + distance sensor → OSC messages for synthesizer

### Main Components
- Webcam + MediaPipe: Hand tracking
- Arduino + HC-SR04: Distance sensing  
- Python logic: Gesture classification
- OSC: Network control protocol

### Five Gesture Modes
```
0: Open Hand        → Full harmonics
1: Closed Fist      → Basic sine/square
2: Fist + Thumb    → Sub-octave
3: Thumb + Index    → Harmonic layer
4: Thumb+Index+Middle → Arpeggio/combined texture
```

### Continuous Controls
- Roll (side-to-side) → Vibrato
- Distance (close/far) → Frequency

### Performance
- **Latency:** 50-80ms typical
- **Frame Rate:** 30 Hz
- **CPU Usage:** 10-15% (GPU), 40-50% (CPU)
- **Bandwidth:** 5-10 KB/sec

---

## 🆘 Finding Help

| I need to... | Go to... |
|--------------|----------|
| Get started quickly | [QUICKSTART.md](QUICKSTART.md) |
| Understand the system | [README.md](README.md) |
| Set up hardware | [CONFIGURATION.md](CONFIGURATION.md) |
| Fix a problem | [CONFIGURATION.md](CONFIGURATION.md) → Troubleshooting |
| Understand data flow | [ARCHITECTURE.md](ARCHITECTURE.md) |
| Learn OSC details | [OSC_PROTOCOL.md](OSC_PROTOCOL.md) |
| Verify requirements | [REQUIREMENTS_FULFILLMENT.md](REQUIREMENTS_FULFILLMENT.md) |
| Run diagnostics | `python test_system.py` |

---

## ✅ Verification Checklist

Before using the system:
- [ ] Read QUICKSTART.md
- [ ] Arduino port configured
- [ ] PlugData patch ready
- [ ] Good lighting available

---

## 🎉 You're All Set!

Everything is ready to use. Choose your learning path above and get started!

**Questions?** Check the relevant documentation file or run `python test_system.py` for diagnostics.

---

**Last Updated:** 2026-03-15  
**Status:** ✅ Complete  
**Version:** 1.0
