This markdown documents all technical issues and resolutions implemented during project development.

___

# Arduino Connection
- `arduino_handshake/arduino_handshake.ino`
- `utils/arduino_handler.py`

### Reduced Camera Frame Rate

- Initial system integration resulted in degraded webcam frame rate (~0.2 fps). Root cause: excessive loop delay in Arduino firmware logic. Resolution: optimized Arduino timing and interrupt handling to restore acceptable frame rates.

### Sensor Noise Interference

- Hardware constraints introduce consistent noise artifacts in distance sensor readings. Implementation: windowing-buffer algorithm applied to filter outliers and stabilize sensor output.

___

# Gesture Classification
- `utils/gesture_classifier.py`

### Finger Extension Detection Algorithm

- MediaPipe hand landmark model identifies 21 points but exhibits asymmetric behavior between thumb and fingers during extension detection. Solution: developed pose-invariant classification algorithm accounting for morphological differences in finger articulation.

### Hand Orientation Compensation

- MediaPipe provides only positional landmarks without intrinsic orientation data. Implementation: designed robust algorithm to normalize finger extension detection relative to hand tilt angle using quaternion-based rotation matrices.

___

# Audio Synthesis & OSC Protocol
- `synth/*`

### Synth Mode Switching Logic

- Integer mode values transmitted via OSC to Pure Data require debouncing and state validation. Solution: implemented hysteresis-based volume control algorithm in PD for stable mode transitions without audio artifacts.

### Vibrato Modulation

- Vibrato parameter received via OSC is normalized to modulation range and fed to FM synthesizer modulator. Implementation: standardized input scaling with configurable depth range for frequency modulation control.

### Panic & Volume Control

- Panic/volume signals processed through unified volume-control algorithm, reusing mode-switching logic for consistent parameter handling.

___

# Hardware Constraints

### Webcam Illumination

- No integrated light control necessary. Ensure adequate ambient lighting and minimize background contrast to maintain hand detection reliability.

### Ultrasonic Sensor Accuracy

- Reflected signal noise from irregular surfaces induces false readings. Best practice: mount sensor perpendicular to flat reference surfaces to minimize specular reflection noises.