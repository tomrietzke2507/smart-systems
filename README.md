# smart-systems

Mobilefrost controller for the Smart Systems course.

## Raspberry Pi / Podman

The controller container expects these stable device names:

- `/dev/arduino_sensor_marten`
- `/dev/arduino_sensor_andor`
- `/dev/arduino_aktor`

Both sensors use the same Arduino sketch output format:

```text
Aktuelle Temperatur: 22.50
```

Each reading is written to the `temperatures` table with the matching `sensor_id`.
The actuator Arduino receives both latest temperatures as `D:<marten>;<andor>`, for example `D:21.7;22.4`. On the 8x2 LCD, Marten is shown in the first row on the left and Andor on the right.

## Windows bridge

For local Windows testing, adjust the COM ports in `windows_serial_bridge.py`. The bridge writes both sensors to the same PostgreSQL table using the sensor IDs `arduino_sensor_marten` and `arduino_sensor_andor`.
