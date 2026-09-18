from .config import SENSORS


def format_display_value(temperature):
    if temperature is None:
        return "--.-"
    return f"{temperature:.1f}"[-4:]


def format_display_command(last_temperatures):
    values = [
        format_display_value(last_temperatures.get(sensor["id"]))
        for sensor in SENSORS
    ]
    return f"D:{';'.join(values)}\n"


def initialize_display(serial_connection):
    serial_connection.write(format_display_command({}).encode("utf-8"))