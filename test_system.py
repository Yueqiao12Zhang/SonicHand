#!/usr/bin/env python3
"""
System verification and diagnostics script.
Tests all components before running main.py.
Usage: python test_system.py
"""

import sys
import os

def print_header(text):
    """Print a formatted section header."""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)

def print_success(text):
    """Print success message."""
    print(f"✓ {text}")

def print_error(text):
    """Print error message."""
    print(f"✗ {text}")

def print_info(text):
    """Print info message."""
    print(f"ℹ {text}")

def test_python_packages():
    """Test Python package imports."""
    print_header("Testing Python Packages")
    
    packages = [
        ("opencv", "cv2"),
        ("mediapipe", "mediapipe"),
        ("pyserial", "serial"),
        ("python-osc", "pythonosc"),
        ("numpy", "numpy")
    ]
    
    all_ok = True
    for pkg_name, import_name in packages:
        try:
            __import__(import_name)
            print_success(f"'{pkg_name}' installed")
        except ImportError:
            print_error(f"'{pkg_name}' NOT installed")
            print_info(f"  Install with: pip install {pkg_name}")
            all_ok = False
    
    return all_ok

def test_mediapipe_model():
    """Test MediaPipe hand landmarker model file."""
    print_header("Testing MediaPipe Model")
    
    model_path = 'hand_landmarker.task'
    
    if os.path.exists(model_path):
        size_mb = os.path.getsize(model_path) / (1024*1024)
        print_success(f"Model found: '{model_path}' ({size_mb:.1f} MB)")
        return True
    else:
        print_error(f"Model NOT found: '{model_path}'")
        print_info("  Download with: python download_model.py")
        return False

def test_module_imports():
    """Test custom module imports."""
    print_header("Testing Custom Modules")
    
    modules = [
        ("utils.gesture_classifier", "GestureClassifier"),
        ("utils.arduino_handler", "ArduinoHandler"),
        ("utils.osc_manager", "OSCManager")
    ]
    
    all_ok = True
    for module_name, class_name in modules:
        try:
            module = __import__(module_name, fromlist=[class_name])
            getattr(module, class_name)
            print_success(f"Module '{module_name}' loads correctly")
        except (ImportError, AttributeError) as e:
            print_error(f"Module '{module_name}' failed: {e}")
            all_ok = False
    
    return all_ok

def test_arduino_connection():
    """Test Arduino serial connection."""
    print_header("Testing Arduino Connection")
    
    try:
        from utils.arduino_handler import ArduinoHandler
        
        # List potential ports
        potential_ports = [
            '/dev/cu.usbserial-1130',
            '/dev/cu.usbserial-14140',
            '/dev/ttyUSB0',
            '/dev/ttyACM0',
            'COM3',
            'COM4'
        ]
        
        print_info("Scanning for Arduino...")
        for port in potential_ports:
            try:
                arduino = ArduinoHandler(port=port, timeout=0.5)
                if arduino.connect():
                    print_success(f"Arduino found on port: {port}")
                    
                    # Try reading
                    raw, smooth, norm = arduino.read_distance()
                    if raw is not None:
                        print_success(f"  Reading distance: {raw:.1f}cm → normalized {norm:.2f}")
                    
                    arduino.disconnect()
                    return True
            except Exception:
                pass
        
        print_error("Arduino NOT detected on any port")
        print_info("  Available ports (macOS): ls /dev/cu.*")
        print_info("  Available ports (Linux): ls /dev/ttyUSB* /dev/ttyACM*")
        print_info("  Update port in main.py if found")
        return False
        
    except Exception as e:
        print_error(f"Arduino test failed: {e}")
        return False

def test_osc_connection():
    """Test OSC client initialization."""
    print_header("Testing OSC Connection")
    
    try:
        from utils.osc_manager import OSCManager
        
        osc = OSCManager(ip='127.0.0.1', port=9999)
        print_success("OSC Manager initialized for 127.0.0.1:9999")
        
        # Test sending test message
        try:
            osc.send_pitch(0.5)
            print_success("Test OSC message sent (PlugData should receive)")
        except Exception as e:
            print_error(f"Failed to send test message: {e}")
            return False
        
        return True
        
    except Exception as e:
        print_error(f"OSC test failed: {e}")
        return False

def test_gesture_classifier():
    """Test gesture classifier initialization."""
    print_header("Testing Gesture Classifier")
    
    try:
        from utils.gesture_classifier import GestureClassifier
        
        classifier = GestureClassifier()
        print_success("GestureClassifier initialized")
        
        # Verify methods exist
        methods = [
            'classify_posture',
            'get_tilt_roll',
            'get_tilt_pitch',
            'is_finger_extended',
            'is_thumb_extended'
        ]
        
        for method in methods:
            if hasattr(classifier, method):
                print_success(f"  Method '{method}' exists")
            else:
                print_error(f"  Method '{method}' NOT found")
                return False
        
        return True
        
    except Exception as e:
        print_error(f"Gesture classifier test failed: {e}")
        return False

def test_webcam():
    """Test webcam access."""
    print_header("Testing Webcam")
    
    try:
        import cv2
        
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print_error("Webcam NOT accessible")
            print_info("  Ensure webcam is connected and not in use")
            return False
        
        ret, frame = cap.read()
        if not ret:
            print_error("Failed to read from webcam")
            cap.release()
            return False
        
        h, w = frame.shape[:2]
        print_success(f"Webcam connected ({w}x{h})")
        cap.release()
        return True
        
    except Exception as e:
        print_error(f"Webcam test failed: {e}")
        return False

def main():
    """Run all tests and report results."""
    print_header("GESTURE-TO-OSC CONTROLLER - SYSTEM DIAGNOSTICS")
    
    tests = [
        ("Python Packages", test_python_packages),
        ("MediaPipe Model", test_mediapipe_model),
        ("Custom Modules", test_module_imports),
        ("Gesture Classifier", test_gesture_classifier),
        ("Webcam", test_webcam),
        ("Arduino Connection", test_arduino_connection),
        ("OSC Connection", test_osc_connection),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print_error(f"Test '{test_name}' crashed: {e}")
            results[test_name] = False
    
    # Summary
    print_header("TEST SUMMARY")
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:8} - {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print_success("All tests passed! Ready to run main.py")
        return 0
    else:
        print_error(f"{total - passed} test(s) failed. See above for details.")
        print_info("Review CONFIGURATION.md for troubleshooting steps")
        return 1

if __name__ == "__main__":
    sys.exit(main())
