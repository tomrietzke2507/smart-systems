import importlib
from pathlib import Path
import sys
import types
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

sys.modules.setdefault("serial", types.SimpleNamespace(Serial=object))

fake_psycopg2 = types.ModuleType("psycopg2")
fake_psycopg2.OperationalError = Exception
fake_psycopg2.connect = lambda **kwargs: None
sys.modules.setdefault("psycopg2", fake_psycopg2)

app = importlib.import_module("mobilefrost.__main__")
config = importlib.import_module("mobilefrost.config")
controller = importlib.import_module("mobilefrost.controller")
database = importlib.import_module("mobilefrost.database")
display = importlib.import_module("mobilefrost.display")
sensor_io = importlib.import_module("mobilefrost.sensor_io")


class TemperatureSensorTests(unittest.TestCase):
    def test_parses_temperature_line(self):
        self.assertEqual(sensor_io.parse_temperature("Aktuelle Temperatur: 21.75"), 21.75)
        self.assertIsNone(sensor_io.parse_temperature("Bereit"))
        self.assertIsNone(sensor_io.parse_temperature("Aktuelle Temperatur: nan?"))

    def test_configures_all_named_sensors(self):
        sensor_ids = [sensor["id"] for sensor in config.SENSORS]

        self.assertEqual(
            sensor_ids,
            [
                "arduino_sensor_marten",
                "arduino_sensor_andor",
                "arduino_sensor_luis",
            ],
        )
        self.assertEqual(config.SENSORS[2]["temperature_offset"], -1.0)
        self.assertEqual(config.DATABASE_WRITE_INTERVAL, 10.0)

    def test_applies_configured_temperature_offset(self):
        sensor = {
            "id": "arduino_sensor_luis",
            "port": "/dev/arduino_sensor_luis",
            "temperature_offset": -1.0,
        }
        manager = sensor_io.SensorManager(
            serial_factory=lambda _port, _baud_rate, timeout: ReadingSerial(
                b"Aktuelle Temperatur: 24.0\n"
            ),
            clock=lambda: 0.0,
            sensors=(sensor,),
        )
        manager.connect_available()

        self.assertEqual(
            list(manager.readings()),
            [("arduino_sensor_luis", 23.0)],
        )

    def test_formats_display_command_for_all_sensors(self):
        last_temperatures = {
            "arduino_sensor_marten": 21.74,
            "arduino_sensor_andor": 22.35,
            "arduino_sensor_luis": 23.86,
        }

        command = display.format_display_command(last_temperatures)

        self.assertEqual(command, "D:21.7;22.4;23.9\n")

    def test_stores_temperature_and_commits(self):
        cursor = RecordingCursor()
        connection = RecordingConnection()

        self.assertTrue(
            database.store_temperature(
                cursor, connection, "arduino_sensor_luis", 23.5
            )
        )
        self.assertEqual(
            cursor.parameters, ("arduino_sensor_luis", 23.5)
        )
        self.assertEqual(connection.commits, 1)
        self.assertEqual(connection.rollbacks, 0)

    def test_database_error_rolls_back_without_raising(self):
        cursor = RecordingCursor(error=RuntimeError("database unavailable"))
        connection = RecordingConnection()

        self.assertFalse(
            database.store_temperature(
                cursor, connection, "arduino_sensor_luis", 23.5
            )
        )
        self.assertEqual(connection.commits, 0)
        self.assertEqual(connection.rollbacks, 1)

    def test_initial_display_command_contains_placeholders(self):
        self.assertEqual(display.format_display_command({}), "D:--.-;--.-;--.-\n")

    def test_initializes_display_after_serial_connection(self):
        serial_connection = RecordingSerial()

        display.initialize_display(serial_connection)

        self.assertEqual(serial_connection.writes, [b"D:--.-;--.-;--.-\n"])

    def test_connects_available_sensors_when_one_is_unavailable(self):
        def serial_factory(port, _baud_rate, timeout):
            self.assertEqual(timeout, 2)
            if port.endswith("luis"):
                raise OSError("device missing")
            return RecordingSerial()

        manager = sensor_io.SensorManager(serial_factory=serial_factory)
        manager.connect_available()

        self.assertEqual(
            list(manager.connections),
            ["arduino_sensor_marten", "arduino_sensor_andor"],
        )

    def test_reconnects_sensor_after_retry_interval(self):
        now = [0.0]
        luis_available = [False]

        def serial_factory(port, _baud_rate, timeout):
            self.assertEqual(timeout, 2)
            if port.endswith("luis") and not luis_available[0]:
                raise OSError("device missing")
            return RecordingSerial()

        manager = sensor_io.SensorManager(
            serial_factory=serial_factory,
            clock=lambda: now[0],
            retry_interval=5.0,
        )
        manager.connect_available()
        self.assertNotIn("arduino_sensor_luis", manager.connections)

        luis_available[0] = True
        now[0] = 5.0
        manager.retry_missing()

        self.assertIn("arduino_sensor_luis", manager.connections)

    def test_read_error_disconnects_only_failed_sensor(self):
        serial_connections = {
            "/dev/arduino_sensor_marten": ReadingSerial(error=OSError("disconnected")),
            "/dev/arduino_sensor_andor": ReadingSerial(b"Aktuelle Temperatur: 22.0\n"),
            "/dev/arduino_sensor_luis": ReadingSerial(b"Aktuelle Temperatur: 23.0\n"),
        }
        manager = sensor_io.SensorManager(
            serial_factory=lambda port, _baud_rate, timeout: serial_connections[port],
            clock=lambda: 0.0,
        )
        manager.connect_available()

        self.assertEqual(
            list(manager.readings()),
            [
                ("arduino_sensor_andor", 22.0),
                ("arduino_sensor_luis", 22.0),
            ],
        )
        self.assertNotIn("arduino_sensor_marten", manager.connections)
        self.assertIn("arduino_sensor_andor", manager.connections)
        self.assertTrue(serial_connections["/dev/arduino_sensor_marten"].closed)

    def test_controller_processes_available_sensor(self):
        actuator = RecordingSerial()
        manager = RecordingSensorManager([
            ("arduino_sensor_luis", 23.5),
        ])
        cursor = RecordingCursor()
        connection = RecordingConnection()
        service = controller.Controller(
            actuator,
            manager,
            cursor,
            connection,
            sleep_func=lambda _seconds: None,
        )

        self.assertEqual(service.run_once(), 1)

        self.assertEqual(actuator.writes[0], b"D:--.-;--.-;23.5\n")
        self.assertEqual(cursor.parameters, ("arduino_sensor_luis", 23.5))
        self.assertEqual(manager.retry_calls, 1)

    def test_controller_displays_every_reading_and_stores_every_ten_seconds(self):
        now = [0.0]
        sleeps = []
        actuator = RecordingSerial()
        manager = RecordingSensorManager([("arduino_sensor_luis", 23.5)])
        cursor = RecordingCursor()
        connection = RecordingConnection()
        service = controller.Controller(
            actuator,
            manager,
            cursor,
            connection,
            clock=lambda: now[0],
            sleep_func=sleeps.append,
        )

        service.run_once()
        now[0] = 5.0
        service.run_once()
        now[0] = 10.0
        service.run_once()

        self.assertEqual(
            actuator.writes,
            [
                b"D:--.-;--.-;23.5\n",
                b"F:0\n",
                b"S:0\n",
                b"D:--.-;--.-;23.5\n",
                b"D:--.-;--.-;23.5\n",
            ],
        )
        self.assertEqual(len(cursor.executions), 2)
        self.assertEqual(sleeps, [])

    def test_controller_retries_database_write_after_failure(self):
        now = [0.0]
        cursor = RecordingCursor(error=RuntimeError("database unavailable"))
        connection = RecordingConnection()
        service = controller.Controller(
            RecordingSerial(),
            RecordingSensorManager([("arduino_sensor_luis", 23.5)]),
            cursor,
            connection,
            clock=lambda: now[0],
            sleep_func=lambda _seconds: None,
        )

        service.run_once()
        cursor.error = None
        now[0] = 1.0
        service.run_once()

        self.assertEqual(connection.rollbacks, 1)
        self.assertEqual(connection.commits, 1)


class RecordingCursor:
    def __init__(self, error=None):
        self.error = error
        self.parameters = None
        self.executions = []

    def execute(self, _query, parameters):
        if self.error:
            raise self.error
        self.parameters = parameters
        self.executions.append(parameters)


class RecordingConnection:
    def __init__(self):
        self.commits = 0
        self.rollbacks = 0

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1


class RecordingSerial:
    def __init__(self):
        self.writes = []

    def write(self, value):
        self.writes.append(value)


class ReadingSerial:
    def __init__(self, value=b"", error=None):
        self.value = value
        self.error = error
        self.closed = False

    def readline(self):
        if self.error:
            raise self.error
        return self.value

    def close(self):
        self.closed = True


class RecordingSensorManager:
    def __init__(self, readings):
        self._readings = readings
        self.retry_calls = 0

    def retry_missing(self):
        self.retry_calls += 1

    def readings(self):
        return iter(self._readings)


class ArduinoIntegrationTests(unittest.TestCase):
    def test_dockerfile_installs_and_runs_package(self):
        dockerfile = (PROJECT_ROOT / "Dockerfile").read_text(encoding="utf-8")

        self.assertIn("COPY pyproject.toml ./", dockerfile)
        self.assertIn("COPY src ./src", dockerfile)
        self.assertIn("RUN pip install --no-cache-dir .", dockerfile)
        self.assertIn('CMD ["python", "-u", "-m", "mobilefrost"]', dockerfile)

    def test_compose_allows_missing_and_reconnected_sensors(self):
        compose = (PROJECT_ROOT / "compose.yml").read_text(encoding="utf-8")

        self.assertIn('"/dev:/dev"', compose)
        self.assertNotIn("device_cgroup_rules", compose)
        self.assertNotIn('"/dev/arduino_sensor_luis:/dev/arduino_sensor_luis"', compose)
        self.assertIn("keep-groups", compose)

    def test_compose_exposes_dashboard_on_loopback_only(self):
        compose = (PROJECT_ROOT / "compose.yml").read_text(encoding="utf-8")

        self.assertIn("dashboard:", compose)
        self.assertIn('"127.0.0.1:8080:8080"', compose)
        self.assertIn("mobilefrost.dashboard:create_app()", compose)

    def test_humidity_sketch_uses_requested_hardware(self):
        sketch = (
            PROJECT_ROOT / "sketches" / "sketch_humidity" / "sketch_humidity.ino"
        ).read_text(encoding="utf-8")

        self.assertIn("DHT dht(A0, DHT11);", sketch)
        self.assertIn("const int LED_R = 9;", sketch)
        self.assertIn("const int LED_G = 10;", sketch)
        self.assertIn("const int LED_B = 11;", sketch)
        self.assertIn('Serial.print("Aktuelle Temperatur: ");', sketch)
        self.assertIn('Serial.print("Aktuelle Luftfeuchtigkeit: ");', sketch)

    def test_actuator_displays_third_temperature_bottom_right(self):
        sketch = (
            PROJECT_ROOT / "sketches" / "sketch_fanANDled" / "sketch_fanANDled.ino"
        ).read_text(encoding="utf-8")

        self.assertIn("String tempLuis", sketch)
        self.assertIn("lcd.setCursor(11, 0);", sketch)
        self.assertIn("lcd.setCursor(11, 1);", sketch)


if __name__ == "__main__":
    unittest.main()