// Independent Motor Control with Serial Commands for Arduino Uno
// Command formats:
//   Two-token: "forward,10" or "backward,5" (defaults to both sides)
//   Three-token: "forward,right,10", "backward,left,5", "forward,both,3"
// Additional command: "stop" to immediately stop motors

#define DEFAULT_DUTY 128  // PWM duty (50% of 255)

// --- Left Motor Driver Pins ---
const int FL_ENA = 5;   // PWM pin for front left enable
const int FL_IN1 = 8;   // Direction control pin
const int FL_IN2 = 7;   // Direction control pin
const int RL_ENA = 3;   // PWM pin for rear left enable
const int RL_IN3 = 4;   // Direction control pin
const int RL_IN4 = 2;   // Direction control pin

// --- Right Motor Driver Pins ---
const int FR_ENA = 6;   // PWM pin for front right enable
const int FR_IN3 = A0;  // Direction control pin
const int FR_IN4 = 12;  // Direction control pin
const int RR_ENA = 10;  // PWM pin for rear right enable
const int RR_IN1 = 11;  // Direction control pin (using analog pin as digital)
const int RR_IN2 = 9;  // Direction control pin (using analog pin as digital)

String inputString = "";      // a String to hold incoming data
bool stringComplete = false;  // whether the string is complete

// Set all motor control pins as outputs.
void setupPins() {
  int motorPins[] = {FL_ENA, FL_IN1, FL_IN2, RL_ENA, RL_IN3, RL_IN4,
                     FR_ENA, FR_IN3, FR_IN4, RR_ENA, RR_IN1, RR_IN2};
  for (int i = 0; i < 12; i++) {
    pinMode(motorPins[i], OUTPUT);
  }
}

// Functions to drive the left motors.
void driveLeftMotors(bool forward) {
  if (forward) {
    digitalWrite(FL_IN1, HIGH);
    digitalWrite(FL_IN2, LOW);
    digitalWrite(RL_IN3, HIGH);
    digitalWrite(RL_IN4, LOW);
  } else {
    digitalWrite(FL_IN1, LOW);
    digitalWrite(FL_IN2, HIGH);
    digitalWrite(RL_IN3, LOW);
    digitalWrite(RL_IN4, HIGH);
  }
  analogWrite(FL_ENA, DEFAULT_DUTY);
  analogWrite(RL_ENA, DEFAULT_DUTY);
}

// Functions to drive the right motors.
void driveRightMotors(bool forward) {
  if (forward) {
    digitalWrite(FR_IN3, HIGH);
    digitalWrite(FR_IN4, LOW);
    digitalWrite(RR_IN1, HIGH);
    digitalWrite(RR_IN2, LOW);
  } else {
    digitalWrite(FR_IN3, LOW);
    digitalWrite(FR_IN4, HIGH);
    digitalWrite(RR_IN1, LOW);
    digitalWrite(RR_IN2, HIGH);
  }
  analogWrite(FR_ENA, DEFAULT_DUTY);
  analogWrite(RR_ENA, DEFAULT_DUTY);
}

// Combined drive for both sides.
void driveMotors(bool forward) {
  driveLeftMotors(forward);
  driveRightMotors(forward);
}

// Stop functions for each side.
void stopLeftMotors() {
  analogWrite(FL_ENA, 0);
  analogWrite(RL_ENA, 0);
}

void stopRightMotors() {
  analogWrite(FR_ENA, 0);
  analogWrite(RR_ENA, 0);
}

// Stop all motors.
void stopMotors() {
  stopLeftMotors();
  stopRightMotors();
}

// Run left motors for a specified duration.
void runLeftMotorsForSeconds(bool forward, unsigned long seconds) {
  driveLeftMotors(forward);
  delay(seconds * 1000UL);
  stopLeftMotors();
}

// Run right motors for a specified duration.
void runRightMotorsForSeconds(bool forward, unsigned long seconds) {
  driveRightMotors(forward);
  delay(seconds * 1000UL);
  stopRightMotors();
}

// Run both motors for a specified duration.
void runMotorsForSeconds(bool forward, unsigned long seconds) {
  driveMotors(forward);
  delay(seconds * 1000UL);
  stopMotors();
}

void setup() {
  Serial.begin(9600);
  setupPins();
  stopMotors();  // Ensure motors are off at startup
  Serial.println("Motor controller ready.");
  Serial.println("Commands:");
  Serial.println("  forward,10               -> Run both motors forward for 10 seconds");
  Serial.println("  backward,5               -> Run both motors backward for 5 seconds");
  Serial.println("  forward,left,10          -> Run left motors forward for 10 seconds");
  Serial.println("  backward,right,5         -> Run right motors backward for 5 seconds");
  Serial.println("  forward,both,3           -> Run both motors forward for 3 seconds");
  Serial.println("  stop                     -> Stop motors immediately");
}

void loop() {
  if (stringComplete) {
    Serial.print("Received command: ");
    Serial.println(inputString);
    inputString.trim();  // Remove extra whitespace
    inputString.toLowerCase();

    if (inputString.length() > 0) {
      // Split the input string by commas.
      int firstComma = inputString.indexOf(',');
      int secondComma = inputString.indexOf(',', firstComma + 1);

      String direction;
      String side;
      String timeString;
      unsigned long duration = 0;
      bool valid = true;

      // If two commas are found, we have three tokens.
      if (secondComma != -1) {
        direction = inputString.substring(0, firstComma);
        side = inputString.substring(firstComma + 1, secondComma);
        timeString = inputString.substring(secondComma + 1);
      }
      // If only one comma, default to "both" motors.
      else if (firstComma != -1) {
        direction = inputString.substring(0, firstComma);
        side = "both";
        timeString = inputString.substring(firstComma + 1);
      }
      else {
        // If no comma, check for "stop" command.
        if (inputString.equals("stop")) {
          Serial.println("Stopping motors immediately.");
          stopMotors();
          valid = false;
        }
        else {
          Serial.println("Invalid command format.");
          valid = false;
        }
      }

      if (valid) {
        duration = timeString.toInt();
        if (duration == 0) {
          Serial.println("Invalid duration.");
          valid = false;
        }
      }

      if (valid) {
        bool forward = (direction.equals("forward"));

        if (side.equals("left")) {
          Serial.print("Running left motors ");
          Serial.print(direction);
          Serial.print(" for ");
          Serial.print(duration);
          Serial.println(" seconds.");
          runLeftMotorsForSeconds(forward, duration);
        }
        else if (side.equals("right")) {
          Serial.print("Running right motors ");
          Serial.print(direction);
          Serial.print(" for ");
          Serial.print(duration);
          Serial.println(" seconds.");
          runRightMotorsForSeconds(forward, duration);
        }
        else if (side.equals("both")) {
          Serial.print("Running both motors ");
          Serial.print(direction);
          Serial.print(" for ");
          Serial.print(duration);
          Serial.println(" seconds.");
          runMotorsForSeconds(forward, duration);
        }
        else {
          Serial.println("Unknown side. Use left, right, or both.");
        }
      }
    }
    // Clear input buffer and reset flag.
    inputString = "";
    stringComplete = false;
    Serial.println("Awaiting command:");
  }
}

// This function is automatically called when new Serial data arrives.
void serialEvent() {
  while (Serial.available()) {
    char inChar = (char)Serial.read();
    if (inChar == '\n' || inChar == '\r') {
      if (inputString.length() > 0) {
        stringComplete = true;
      }
    } else {
      inputString += inChar;
    }
  }
}
