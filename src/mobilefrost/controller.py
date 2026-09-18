import time

from .database import store_temperature
from .display import format_display_command


class Controller:
    def __init__(
        self,
        actuator,
        sensor_manager,
        cursor,
        database_connection,
        sleep_func=time.sleep,
    ):
        self.actuator = actuator
        self.sensor_manager = sensor_manager
        self.cursor = cursor
        self.database_connection = database_connection
        self.sleep = sleep_func
        self.last_temperatures = {}

    def run_once(self):
        self.sensor_manager.retry_missing()
        reading_count = 0

        for sensor_id, temperature in self.sensor_manager.readings():
            reading_count += 1
            self.last_temperatures[sensor_id] = temperature
            print(f"Gemessen ({sensor_id}): {temperature}°C")

            command = format_display_command(self.last_temperatures)
            print(f"LCD-Kommando: {command.strip()}")
            self.actuator.write(command.encode("utf-8"))
            self.sleep(0.2)

            self._update_cooling()
            store_temperature(
                self.cursor,
                self.database_connection,
                sensor_id,
                temperature,
            )

        return reading_count

    def run(self):
        while True:
            try:
                reading_count = self.run_once()
                if reading_count == 0:
                    self.sleep(1)
            except Exception as error:
                print(f"Fehler: {error}")
                self.sleep(1)

    def _update_cooling(self):
        if max(self.last_temperatures.values()) > 26.0:
            print("Zu warm! Lüfter AN & Klappe AUF.")
            self.actuator.write(b"F:255\n")
            self.sleep(0.5)
            self.actuator.write(b"S:90\n")
        else:
            print("Temperatur OK. Lüfter AUS & Klappe ZU.")
            self.actuator.write(b"F:0\n")
            self.sleep(0.5)
            self.actuator.write(b"S:0\n")