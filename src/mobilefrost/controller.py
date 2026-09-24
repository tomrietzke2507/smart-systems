from datetime import datetime, timezone
import time

from .config import DATABASE_WRITE_INTERVAL, FAN_ON_TEMPERATURE, FLAP_OPEN_TEMPERATURE
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
        wall_clock=lambda: datetime.now(timezone.utc),
        mqtt_adapter=None,
        database_write_interval=DATABASE_WRITE_INTERVAL,
        sleep_func=time.sleep,
    ):
        self.actuator = actuator
        self.sensor_manager = sensor_manager
        self.cursor = cursor
        self.database_connection = database_connection
        self.clock = clock
        self.wall_clock = wall_clock
        self.mqtt_adapter = mqtt_adapter
        self.database_write_interval = database_write_interval
        self.sleep = sleep_func
        self.last_temperatures = {}
        self.last_database_writes = {}
        self.cooling_enabled = None
        self.flap_open = None
        if self.mqtt_adapter is not None:
            self.mqtt_adapter.start(self.handle_actuator_command)

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

            if self.mqtt_adapter is not None:
                self.mqtt_adapter.publish_temperature(
                    sensor_id,
                    temperature,
                    self.wall_clock(),
                )

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
        maximum_temperature = max(self.last_temperatures.values())
        cooling_enabled = maximum_temperature > FAN_ON_TEMPERATURE
        flap_open = maximum_temperature >= FLAP_OPEN_TEMPERATURE

        if cooling_enabled != self.cooling_enabled:
            self.cooling_enabled = cooling_enabled
            if self.mqtt_adapter is not None:
                self.mqtt_adapter.publish_cooling_state(cooling_enabled)

            if cooling_enabled:
                print("Zu warm! Lüfter AN.")
                self.actuator.write(b"F:255\n")
            else:
                print("Temperatur OK. Lüfter AUS.")
                self.actuator.write(b"F:0\n")

        if flap_open != self.flap_open:
            self.flap_open = flap_open
            if flap_open:
                print("Temperatur mindestens 30 °C. Klappe AUF.")
                self.actuator.write(b"S:90\n")
            else:
                self.actuator.write(b"S:0\n")

    def handle_actuator_command(self, kind, value):
        if kind == "fan":
            self.actuator.write(f"F:{value}\n".encode("utf-8"))
        elif kind == "flap":
            self.actuator.write(f"S:{value}\n".encode("utf-8"))

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