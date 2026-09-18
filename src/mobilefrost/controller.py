import time

from .config import DATABASE_WRITE_INTERVAL
from .database import store_temperature
from .display import format_display_command


class Controller:
    def __init__(
        self,
        actuator,
        sensor_manager,
        cursor,
        database_connection,
        clock=time.monotonic,
        database_write_interval=DATABASE_WRITE_INTERVAL,
        sleep_func=time.sleep,
    ):
        self.actuator = actuator
        self.sensor_manager = sensor_manager
        self.cursor = cursor
        self.database_connection = database_connection
        self.clock = clock
        self.database_write_interval = database_write_interval
        self.sleep = sleep_func
        self.last_temperatures = {}
        self.last_database_writes = {}
        self.cooling_enabled = None

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

            self._update_cooling()
            self._store_if_due(sensor_id, temperature)

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
        cooling_enabled = max(self.last_temperatures.values()) > 26.0
        if cooling_enabled == self.cooling_enabled:
            return

        self.cooling_enabled = cooling_enabled
        if cooling_enabled:
            print("Zu warm! Lüfter AN & Klappe AUF.")
            self.actuator.write(b"F:255\n")
            self.actuator.write(b"S:90\n")
        else:
            print("Temperatur OK. Lüfter AUS & Klappe ZU.")
            self.actuator.write(b"F:0\n")
            self.actuator.write(b"S:0\n")

    def _store_if_due(self, sensor_id, temperature):
        now = self.clock()
        last_write = self.last_database_writes.get(sensor_id)
        if (
            last_write is not None
            and now - last_write < self.database_write_interval
        ):
            return

        if store_temperature(
            self.cursor,
            self.database_connection,
            sensor_id,
            temperature,
        ):
            self.last_database_writes[sensor_id] = now