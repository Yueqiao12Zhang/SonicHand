#define TRIG_PIN 12
#define ECHO_PIN 11

void setup() {
  Serial.begin(115200);
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
}

void loop() {
  long duration, distance;
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  
  // Cap timeout so missed echoes do not block the loop for 1 second.
  duration = pulseIn(ECHO_PIN, HIGH, 30000);
  distance = (duration / 2) / 29.1; // Convert to cm

  if (distance > 0 && distance < 100) {
    Serial.println(distance);
  }
  
  delay(30); // Keep it fast for low latency
}