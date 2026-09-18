import importlib
from pathlib import Path
import sys
import types
import unittest


sys.modules.setdefault("serial", types.SimpleNamespace(Serial=object))

fake_psycopg2 = types.ModuleType("psycopg2")
fake_psycopg2.OperationalError = Exception
fake_psycopg2.connect = lambda **kwargs: None
sys.modules.setdefault("psycopg2", fake_psycopg2)

app = importlib.import_module("app")
PROJECT_ROOT = Path(__file__).parent


class TemperatureSensorTests(unittest.TestCase):
    def test_parses_temperature_line(self):
        self.assertEqual(app.parse_temperature("Aktuelle Temperatur: 21.75"), 21.75)
        self.assertIsNone(app.parse_temperature("Bereit"))
        self.assertIsNone(app.parse_temperature("Aktuelle Temperatur: nan?"))

    def test_configures_all_named_sensors(self):
        sensor_ids = [sensor["id"] for sensor in app.SENSORS]

        self.assertEqual(
            sensor_ids,
            [
                "arduino_sensor_marten",
                "arduino_sensor_andor",
                "arduino_sensor_luis",
            ],
        )

    def test_formats_display_command_for_all_sensors(self):
        last_temperatures = {
            "arduino_sensor_marten": 21.74,
            "arduino_sensor_andor": 22.35,
            "arduino_sensor_luis": 23.86,
        }

        command = app.format_display_command(last_temperatures)

        self.assertEqual(command, "D:21.7;22.4;23.9\n")

    def test_stores_temperature_and_commits(self):
        cursor = RecordingCursor()
        connection = RecordingConnection()

        self.assertTrue(
            app.store_temperature(
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
            app.store_temperature(
                cursor, connection, "arduino_sensor_luis", 23.5
            )
        )
        self.assertEqual(connection.commits, 0)
        self.assertEqual(connection.rollbacks, 1)

    def test_initial_display_command_contains_placeholders(self):
        self.assertEqual(app.format_display_command({}), "D:--.-;--.-;--.-\n")

    def test_initializes_display_after_serial_connection(self):
        serial_connection = RecordingSerial()

        app.initialize_display(serial_connection)

        self.assertEqual(serial_connection.writes, [b"D:--.-;--.-;--.-\n"])

    def test_connects_available_sensors_when_one_is_unavailable(self):
        def serial_factory(port, _baud_rate, timeout):
            self.assertEqual(timeout, 2)
            if port.endswith("luis"):
                raise OSError("device missing")
            return RecordingSerial()

        connections = app.open_sensor_connections(serial_factory)

        self.assertEqual(
            [sensor["id"] for sensor in connections],
            ["arduino_sensor_marten", "arduino_sensor_andor"],
        )


class RecordingCursor:
    def __init__(self, error=None):
        self.error = error
        self.parameters = None

    def execute(self, _query, parameters):
        if self.error:
            raise self.error
        self.parameters = parameters


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


class ArduinoIntegrationTests(unittest.TestCase):
    def test_compose_maps_luis_sensor(self):
        compose = (PROJECT_ROOT / "compose.yml").read_text(encoding="utf-8")

        self.assertIn(
            '"/dev/arduino_sensor_luis:/dev/arduino_sensor_luis"', compose
        )
        self.assertNotIn("keep-groups", compose)

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
        self.assertIn("lcd.setCursor(8, 1);", sketch)


if __name__ == "__main__":
    unittest.main()