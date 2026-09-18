#include <LiquidCrystal.h>
#include <Servo.h>  // Neue Servo-Bibliothek

// LCD Verkabelung: RS(12), EN(11), D4(5), D5(4), D6(3), D7(2)
LiquidCrystal lcd(12, 11, 5, 4, 3, 2);

const int FAN_PIN = 6; 
const int SERVO_PIN = 9;

Servo klappenServo; // Erstellt das Servo-Objekt

void setup() {
  Serial.begin(9600);
  pinMode(FAN_PIN, OUTPUT);
  
  // Servo an Pin 9 binden und Startposition (0 Grad = zu) setzen
  klappenServo.attach(SERVO_PIN);
  klappenServo.write(0);
  
  lcd.begin(16, 2);
  lcd.setCursor(0, 0);
  lcd.print("MobileFrost");
  lcd.setCursor(0, 1);
  lcd.print("Warte...");
}

void loop() {
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim(); 

    // BEFEHL 1: Temperaturen (z.B. "D:21.7;22.4;23.9")
    if (command.startsWith("D:")) {
      int separatorIndex = command.indexOf(';');
      int secondSeparatorIndex = command.indexOf(';', separatorIndex + 1);
      if (separatorIndex > 2 && secondSeparatorIndex > separatorIndex) {
        String tempLeft = command.substring(2, separatorIndex);
        String tempRight = command.substring(separatorIndex + 1, secondSeparatorIndex);
        String tempLuis = command.substring(secondSeparatorIndex + 1);

        lcd.setCursor(0, 0);
        lcd.print("        ");
        lcd.setCursor(0, 0);
        lcd.print(tempLeft.substring(0, 4) + "C");

        lcd.setCursor(8, 0);
        lcd.print("        ");
        lcd.setCursor(8, 0);
        lcd.print(tempRight.substring(0, 4) + "C");

        lcd.setCursor(8, 1);
        lcd.print("        ");
        lcd.setCursor(8, 1);
        lcd.print(tempLuis.substring(0, 4) + "C");
      }
    }
    else if (command.startsWith("T:")) {
      String tempVal = command.substring(2);
      lcd.setCursor(0, 0);
      lcd.print("                ");
      lcd.setCursor(0, 0);
      lcd.print(tempVal.substring(0, 4) + "C");
    }
    
    // BEFEHL 2: Lüfter (z.B. "F:255")
    else if (command.startsWith("F:")) {
      String pwmVal = command.substring(2);
      int speed = pwmVal.toInt(); 
      if (speed < 0) speed = 0;
      if (speed > 255) speed = 255;
      
      analogWrite(FAN_PIN, speed);
      
      lcd.setCursor(0, 1);
      if (speed == 0) {
        lcd.print("FAN: AUS");
      } else {
        lcd.print("FAN: AN ");
      }
    }
    
    // BEFEHL 3: Servo / Klappe (z.B. "S:90")
    else if (command.startsWith("S:")) {
      String winkelVal = command.substring(2);
      int winkel = winkelVal.toInt();
      
      if (winkel < 0) winkel = 0;
      if (winkel > 180) winkel = 180;
      
      klappenServo.write(winkel); // Bewegt den Motor
    }
  }
}