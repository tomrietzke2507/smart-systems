# smart-systems

Mobilefrost controller for the Smart Systems course.

## Raspberry Pi / Podman

The controller container expects these stable device names:

- `/dev/arduino_sensor_marten`
- `/dev/arduino_sensor_andor`
- `/dev/arduino_sensor_luis`
- `/dev/arduino_aktor`

All sensors use the same temperature output format:

```text
Aktuelle Temperatur: 22.50
```

Each reading is written to the `temperatures` table with the matching `sensor_id`.
The Luis sensor additionally reports `Aktuelle Luftfeuchtigkeit: <value>`.
The actuator Arduino receives all latest temperatures as `D:<marten>;<andor>;<luis>`, for example `D:21.7;22.4;23.9`. On the 16x2 LCD, Marten is shown in the first row on the left, Andor on the right, and Luis in the second row on the right. The fan status remains in the second row on the left.

The Arduino sketches are stored below `sketches/`. Flash them onto the boards
before starting Docker; Arduino code does not run inside the controller container.
For `sketch_humidity`, install the Arduino libraries `DHT sensor library` and
`Adafruit Unified Sensor` in the Arduino IDE.

Start the services on the Linux host that exposes the four device paths:

```text
docker compose up --build
```

## Windows bridge

For local Windows testing, adjust the COM ports in `windows_serial_bridge.py`. The bridge writes both sensors to the same PostgreSQL table using the sensor IDs `arduino_sensor_marten` and `arduino_sensor_andor`.
