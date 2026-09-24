SENSORS = (
    {
        "id": "arduino_sensor_marten",
        "port": "/dev/arduino_sensor_marten",
        "temperature_offset": 0.0,
    },
    {
        "id": "arduino_sensor_andor",
        "port": "/dev/arduino_sensor_andor",
        "temperature_offset": 0.0,
    },
    {
        "id": "arduino_sensor_luis",
        "port": "/dev/arduino_sensor_luis",
        "temperature_offset": -1.0,
    },
)

PORT_ACTUATOR = "/dev/arduino_aktor"
BAUD_RATE = 9600
SERIAL_TIMEOUT = 2
SENSOR_RETRY_INTERVAL = 5.0
DATABASE_WRITE_INTERVAL = 10.0
FAN_ON_TEMPERATURE = 26.0
FLAP_OPEN_TEMPERATURE = 30.0
MQTT_HOST = "mosquitto"
MQTT_PORT = 1883