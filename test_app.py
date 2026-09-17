import importlib
import sys
import types
import unittest


sys.modules.setdefault("serial", types.SimpleNamespace(Serial=object))

fake_psycopg2 = types.ModuleType("psycopg2")
fake_psycopg2.OperationalError = Exception
fake_psycopg2.connect = lambda **kwargs: None
sys.modules.setdefault("psycopg2", fake_psycopg2)

app = importlib.import_module("app")


class TemperatureSensorTests(unittest.TestCase):
    def test_parses_temperature_line(self):
        self.assertEqual(app.parse_temperature("Aktuelle Temperatur: 21.75"), 21.75)
        self.assertIsNone(app.parse_temperature("Bereit"))

    def test_configures_both_named_sensors(self):
        sensor_ids = [sensor["id"] for sensor in app.SENSORS]

        self.assertEqual(sensor_ids, ["arduino_sensor_marten", "arduino_sensor_andor"])

    def test_formats_display_command_for_both_sensors(self):
        last_temperatures = {
            "arduino_sensor_marten": 21.74,
            "arduino_sensor_andor": 22.35,
        }

        command = app.format_display_command(last_temperatures)

        self.assertEqual(command, "D:21.7;22.4\n")


if __name__ == "__main__":
    unittest.main()