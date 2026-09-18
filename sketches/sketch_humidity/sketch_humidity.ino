#include <DHT.h>

const int LED_R = 9;
const int LED_G = 10;
const int LED_B = 11;

DHT dht(A0, DHT11);

void setup() {
	Serial.begin(9600);
	dht.begin();

	pinMode(LED_R, OUTPUT);
	pinMode(LED_G, OUTPUT);
	pinMode(LED_B, OUTPUT);
}

void loop() {
	float humidity = dht.readHumidity();
	float temperature = dht.readTemperature();

	if (isnan(humidity) || isnan(temperature)) {
		Serial.println("Fehler beim Lesen des DHT11");
		setColor(255, 0, 255);
		delay(2000);
		return;
	}

	updateLED(temperature);

	Serial.print("Aktuelle Temperatur: ");
	Serial.println(temperature);
	Serial.print("Aktuelle Luftfeuchtigkeit: ");
	Serial.println(humidity);

	delay(2000);
}

void updateLED(float temperature) {
	if (temperature > 26.0) {
		setColor(255, 0, 0);
	} else if (temperature >= 24.0) {
		setColor(0, 255, 0);
	} else {
		setColor(0, 0, 255);
	}
}

void setColor(int red, int green, int blue) {
	analogWrite(LED_R, red);
	analogWrite(LED_G, green);
	analogWrite(LED_B, blue);
}
