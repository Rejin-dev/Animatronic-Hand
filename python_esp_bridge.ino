#include <ESP32Servo.h>

// Create 5 servo objects
Servo thumbServo;
Servo indexServo;
Servo middleServo;
Servo ringServo;
Servo pinkyServo;

// Define safe ESP32 PWM pins
const int thumbPin = 13;
const int indexPin = 14;
const int middlePin = 15;
const int ringPin = 26;
const int pinkyPin = 27;

void setup() {
  // Must match the 115200 in the Python script!
  Serial.begin(115200); 
  
  // ESP32 requires timers to be allocated for servos
  ESP32PWM::allocateTimer(0);
  ESP32PWM::allocateTimer(1);
  ESP32PWM::allocateTimer(2);
  ESP32PWM::allocateTimer(3);

  // Standard servos operate at 50Hz
  thumbServo.setPeriodHertz(50);
  indexServo.setPeriodHertz(50);
  middleServo.setPeriodHertz(50);
  ringServo.setPeriodHertz(50);
  pinkyServo.setPeriodHertz(50);
  
  // Attach servos to the pins
  thumbServo.attach(thumbPin);
  indexServo.attach(indexPin);
  middleServo.attach(middlePin);
  ringServo.attach(ringPin);
  pinkyServo.attach(pinkyPin);
  
  // Start all servos in the "Open" position (0 degrees)
  thumbServo.write(0);
  indexServo.write(0);
  middleServo.write(0);
  ringServo.write(0);
  pinkyServo.write(0);
}

void loop() {
  // If data is coming in from Python
  if (Serial.available() > 0) {
    
    // Parse the 5 numbers separated by commas
    int t = Serial.parseInt(); // Thumb
    int i = Serial.parseInt(); // Index
    int m = Serial.parseInt(); // Middle
    int r = Serial.parseInt(); // Ring
    int p = Serial.parseInt(); // Pinky
    
    // Look for the newline character to finish the read
    if (Serial.read() == '\n') {
      
      // Write the angles to the motors safely clamped between 0-180
      thumbServo.write(constrain(t, 0, 180));
      indexServo.write(constrain(i, 0, 180));
      middleServo.write(constrain(m, 0, 180));
      ringServo.write(constrain(r, 0, 180));
      pinkyServo.write(constrain(p, 0, 180));
    }
  }
}