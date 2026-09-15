#include <LiquidCrystal.h>

// LCD Verkabelung: RS(12), EN(11), D4(5), D5(4), D6(3), D7(2)
LiquidCrystal lcd(12, 11, 5, 4, 3, 2);

const int FAN_PIN = 6; 

void setup() {
  Serial.begin(9600);
  pinMode(FAN_PIN, OUTPUT);
  
  lcd.begin(8, 2); 
  lcd.setCursor(0, 0);
  lcd.print("MobileFr"); 
  lcd.setCursor(0, 1);
  lcd.print("Warte...");
}

void loop() {
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim(); 

    if (command.startsWith("T:")) {
      String tempVal = command.substring(2); 
      lcd.clear();
      lcd.setCursor(0, 0);
      lcd.print(tempVal + "C"); 
    }
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
  }
}