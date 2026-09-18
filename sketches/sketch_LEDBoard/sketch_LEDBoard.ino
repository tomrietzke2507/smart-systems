const int TEMP_PIN = A0;
const int LED_R = 9;
const int LED_G = 10;
const int LED_B = 11;

void setup() {
  Serial.begin(9600);
  pinMode(LED_R, OUTPUT);
  pinMode(LED_G, OUTPUT);
  pinMode(LED_B, OUTPUT);
}

void loop() {
  float currentTemp = readTemperature();
  updateLED(currentTemp);

  // Diese Zeile wird später vom Python-Skript gelesen
  Serial.print("Aktuelle Temperatur: ");
  Serial.println(currentTemp);
  
  delay(2000); // Alle 2 Sekunden messen reicht völlig
}

float readTemperature() {
  int analogVal = analogRead(TEMP_PIN);
  if (analogVal == 0 || analogVal == 1023) return 0.0; 
  // Formel für die Schaltung: 5V -> Thermistor -> A0 -> 10k -> GND
  float r = 10000.0 * (1023.0 / analogVal - 1.0); 
  float tempK = 1.0 / (1.0 / 298.15 + (1.0 / 3950.0) * log(r / 10000.0));
  return tempK - 273.15;
}

void updateLED(float temp) {
  if (temp > 26.0) {
    setColor(255, 0, 0);   // Rot
  } else if (temp >= 24.0) {
    setColor(0, 255, 0);   // Grün
  } else {
    setColor(0, 0, 255);   // Blau
  }
}

void setColor(int r, int g, int b) {
  analogWrite(LED_R, r);
  analogWrite(LED_G, g);
  analogWrite(LED_B, b);
}