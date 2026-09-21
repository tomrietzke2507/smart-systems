import time

import serial

from .config import BAUD_RATE, PORT_ACTUATOR, SERIAL_TIMEOUT
from .controller import Controller
from .database import connect_db, init_db
from .display import initialize_display
from .mqtt_io import build_mqtt_adapter
from .sensor_io import SensorManager

def main():
    print("Starte Mobilefrost Zentrale (Sensor & Aktor)...")

    try:
        actuator = serial.Serial(
            PORT_ACTUATOR, BAUD_RATE, timeout=SERIAL_TIMEOUT
        )
        time.sleep(2)
        initialize_display(actuator)
        print("Aktor verbunden!")
    except Exception as error:
        print(f"Aktor nicht erreichbar: {error}")
        return 1

    sensor_manager = SensorManager()
    sensor_manager.connect_available()
    if not sensor_manager.connections:
        print("Keine Sensoren erreichbar. Wiederverbindung läuft.")

    database_connection = connect_db()
    init_db(database_connection)
    cursor = database_connection.cursor()
    Controller(
        actuator,
        sensor_manager,
        cursor,
        database_connection,
        mqtt_adapter=build_mqtt_adapter(),
    ).run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())