#include "BluetoothSerial.h"
#include <ESP32Servo.h>

// Check if Bluetooth is enabled in the ESP32 board configuration
#if !defined(CONFIG_BT_ENABLED) || !defined(CONFIG_BLUEDROID_ENABLED)
#error Bluetooth is not enabled! Please run `make menuconfig` to and enable it
#endif

// Create Bluetooth Serial object
BluetoothSerial SerialBT;

// Pin definitions
const int thumbPin = 13;
const int indexPin = 14;
const int middlePin = 15;
const int ringPin = 26;
const int pinkyPin = 27;

// Servo objects
Servo thumbServo;
Servo indexServo;
Servo middleServo;
Servo ringServo;
Servo pinkyServo;

// Angles for open and closed states
const int OPEN_ANGLE = 0;
const int OPEN_ANGLE_2 = 15;
const int CLOSED_ANGLE = 180;
const int CLOSED_ANGLE_2 = 160;

// Variables to track current state 
// (true = 180/closed, false = 0/open)
bool thumbState = true;   // Starts at 180
bool indexState = false;  // Starts at 0
bool middleState = false; // Starts at 0
bool ringState = true;    // Starts at 180
bool pinkyState = true;   // Starts at 180

void setup() {
  Serial.begin(115200);

  // Allocate standard ESP32 PWM timers for the servos
  ESP32PWM::allocateTimer(0);
  ESP32PWM::allocateTimer(1);
  ESP32PWM::allocateTimer(2);
  ESP32PWM::allocateTimer(3);

  // Set standard servo frequencies
  thumbServo.setPeriodHertz(50);
  indexServo.setPeriodHertz(50);
  middleServo.setPeriodHertz(50);
  ringServo.setPeriodHertz(50);
  pinkyServo.setPeriodHertz(50);

  // Attach servos to pins
  thumbServo.attach(thumbPin, 500, 2400);
  indexServo.attach(indexPin, 500, 2400);
  middleServo.attach(middlePin, 500, 2400);
  ringServo.attach(ringPin, 500, 2400);
  pinkyServo.attach(pinkyPin, 500, 2400);

  // Set the exact starting positions you requested
  thumbServo.write(180);
  indexServo.write(0);
  middleServo.write(0);
  ringServo.write(180);
  pinkyServo.write(175);

  // Start Bluetooth device
  SerialBT.begin("AnimatronicHand"); 
  Serial.println("Bluetooth started! Ready to pair as 'AnimatronicHand'.");
}

void loop() {
  // Check if we received anything over Bluetooth
  if (SerialBT.available()) {
    char incomingChar = SerialBT.read();
    
    // Ignore newline or carriage return characters
    if (incomingChar == '\n' || incomingChar == '\r') {
      return; 
    }

    Serial.print("Received command: ");
    Serial.println(incomingChar);

    // Toggle fingers based on the character received
    switch (incomingChar) {
      case '1':
      case 't': 
        thumbState = !thumbState;
        thumbServo.write(thumbState ? CLOSED_ANGLE : 30);
        SerialBT.println("Thumb toggled");
        break;
      
      case '2':
      case 'i': 
        indexState = !indexState;
        indexServo.write(indexState ? CLOSED_ANGLE_2 : OPEN_ANGLE);
        SerialBT.println("Index toggled");
        break;
      
      case '3':
      case 'm': 
        middleState = !middleState;
        middleServo.write(middleState ? CLOSED_ANGLE : OPEN_ANGLE);
        SerialBT.println("Middle toggled");
        break;
      
      case '4':
      case 'r': 
        ringState = !ringState;
        ringServo.write(ringState ? CLOSED_ANGLE : OPEN_ANGLE);
        SerialBT.println("Ring toggled");
        break;
      
      case '5':
      case 'p': 
        pinkyState = !pinkyState;
        pinkyServo.write(pinkyState ? CLOSED_ANGLE : OPEN_ANGLE_2);
        SerialBT.println("Pinky toggled");
        break;

      default:
        SerialBT.println("Invalid command. Send t, i, m, r, or p.");
        break;
    }
  }
}