/**
 * HC-SR04 Ultrasonic Distance Sensor
 * Gesture-to-OSC Controller: Arduino Component
 * 
 * Purpose: Read distance values from HC-SR04 ultrasonic sensor
 *          and send via Serial (9600 baud) to Python controller
 * 
 * Hardware:
 *   - HC-SR04 Ultrasonic Sensor
 *   - Arduino (UNO, Nano, Mega, etc.)
 * 
 * Connections:
 *   HC-SR04 VCC   → Arduino 5V
 *   HC-SR04 GND   → Arduino GND
 *   HC-SR04 TRIG  → Arduino Pin 9
 *   HC-SR04 ECHO  → Arduino Pin 10
 * 
 * Output: Distance in centimeters (5-50cm range)
 * Update Rate: ~30Hz (33ms delay between readings)
 * Serial Baud: 9600
 */

// Pin definitions
#define TRIG_PIN 9    // Trigger pin (output)
#define ECHO_PIN 10   // Echo pin (input)

// Distance sensor parameters
#define MIN_DISTANCE 5     // Minimum detectable distance (cm)
#define MAX_DISTANCE 100   // Maximum detectable distance (cm)
#define SPEED_OF_SOUND 343  // Speed of sound in air (m/s at 20°C)
#define SENSOR_UPDATE_RATE 30  // Hz

void setup() {
  // Initialize serial communication
  Serial.begin(9600);
  
  // Configure pins
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  
  // Initialization message
  delay(1000);
  Serial.println("# HC-SR04 Ultrasonic Distance Sensor Ready");
  Serial.println("# Format: [distance_cm]");
}

void loop() {
  // --- TRIGGER MEASUREMENT ---
  // Send 10 microsecond pulse to trigger pin
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  
  digitalWrite(TRIG_PIN, LOW);
  
  // --- MEASURE ECHO TIME ---
  // Measure duration of ECHO pulse
  // The sensor keeps ECHO pin high for a duration proportional to distance
  long duration = pulseIn(ECHO_PIN, HIGH, 30000);  // 30ms timeout
  
  // --- CALCULATE DISTANCE ---
  // distance = (duration / 2) / 29.1
  // Derivation:
  //   - Sound travels at ~343 m/s (29.1 microseconds per cm)
  //   - Distance = (speed × time) / 2
  //   - Divide by 2 because sound travels to object and back
  long distance = (duration / 2) / 29;  // Use 29 for HC-SR04
  
  // --- VALIDATE AND SEND DATA ---
  if (distance >= MIN_DISTANCE && distance <= MAX_DISTANCE) {
    // Valid reading: send to Python
    Serial.println(distance);
  }
  // If out of range, skip sending (no invalid data)
  
  // --- UPDATE RATE CONTROL ---
  // Maintain ~30Hz update rate
  // 33ms per reading = ~30 readings per second
  delay(33);
}

/**
 * DEBUG: Uncomment below to add diagnostic output
 * 
 * Diagnostic mode prints:
 *   - Raw duration (microseconds)
 *   - Calculated distance
 *   - Validation status
 */

/*
void debug_loop() {
  long duration, distance;
  
  // Trigger measurement
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  
  // Measure echo
  duration = pulseIn(ECHO_PIN, HIGH, 30000);
  distance = (duration / 2) / 29;
  
  // Print debug info
  Serial.print("Duration: ");
  Serial.print(duration);
  Serial.print(" µs | Distance: ");
  Serial.print(distance);
  Serial.print(" cm | Valid: ");
  Serial.println((distance >= MIN_DISTANCE && distance <= MAX_DISTANCE) ? "YES" : "NO");
  
  delay(100);  // Slower for readability
}
*/