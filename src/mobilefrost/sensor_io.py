import math
import time

import serial

from .config import BAUD_RATE, SENSORS, SENSOR_RETRY_INTERVAL, SERIAL_TIMEOUT


def parse_temperature(line):
    if not line or "Aktuelle Temperatur:" not in line:
        return None

    try:
        temperature = float(line.split(":", 1)[1].strip())
    except (ValueError, IndexError):
        return None
    return temperature if math.isfinite(temperature) else None


class SensorManager:
    def __init__(
        self,
        serial_factory=serial.Serial,
        clock=time.monotonic,
        retry_interval=SENSOR_RETRY_INTERVAL,
        sensors=SENSORS,
    ):
        self.serial_factory = serial_factory
        self.clock = clock
        self.retry_interval = retry_interval
        self.sensors = sensors
        self.connections = {}
        self.next_retry = {sensor["id"]: 0.0 for sensor in sensors}

    def connect_available(self):
        now = self.clock()
        for sensor in self.sensors:
            sensor_id = sensor["id"]
            if sensor_id in self.connections or now < self.next_retry[sensor_id]:
                continue

            try:
                self.connections[sensor_id] = self.serial_factory(
                    sensor["port"], BAUD_RATE, timeout=SERIAL_TIMEOUT
                )
                print(f"Sensor verbunden: {sensor_id}")
            except Exception as error:
                self.next_retry[sensor_id] = now + self.retry_interval
                print(f"Sensor nicht erreichbar ({sensor_id}): {error}")

    def retry_missing(self):
        self.connect_available()

    def readings(self):
        for sensor in self.sensors:
            sensor_id = sensor["id"]
            connection = self.connections.get(sensor_id)
            if connection is None:
                continue

            try:
                line = connection.readline().decode(
                    "utf-8", errors="ignore"
                ).strip()
            except Exception as error:
                self._disconnect(sensor_id, connection, error)
                continue

            temperature = parse_temperature(line)
            if temperature is not None:
                yield sensor_id, temperature

    def _disconnect(self, sensor_id, connection, error):
        try:
            connection.close()
        except Exception:
            pass
        self.connections.pop(sensor_id, None)
        self.next_retry[sensor_id] = self.clock() + self.retry_interval
        print(f"Sensorverbindung verloren ({sensor_id}): {error}")