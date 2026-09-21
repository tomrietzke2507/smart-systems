import os
import json

from .config import MQTT_HOST, MQTT_PORT


TEMPERATURE_TOPIC_PREFIX = "mobilefrost/temperatures"
COOLING_STATUS_TOPIC = "mobilefrost/status/cooling"
FAN_SET_TOPIC = "mobilefrost/actuators/fan/set"
FLAP_SET_TOPIC = "mobilefrost/actuators/flap/set"


def format_temperature_payload(sensor_id, value, timestamp):
    return json.dumps(
        {
            "sensor_id": sensor_id,
            "value": float(value),
            "timestamp": timestamp.isoformat(),
        },
        separators=(",", ":"),
    )


def format_cooling_payload(enabled, source="automatic"):
    return json.dumps(
        {"enabled": bool(enabled), "source": source},
        separators=(",", ":"),
    )


def parse_actuator_command(topic, payload):
    if isinstance(payload, bytes):
        payload = payload.decode("utf-8", errors="replace")

    try:
        value = int(str(payload).strip())
    except ValueError:
        return None

    if topic == FAN_SET_TOPIC and 0 <= value <= 255:
        return ("fan", value)
    if topic == FLAP_SET_TOPIC and 0 <= value <= 90:
        return ("flap", value)
    return None


class MqttAdapter:
    def __init__(self, client=None, host=None, port=None):
        self.client = client
        self.host = host
        self.port = port

    def start(self, on_command):
        if self.client is None or self.host is None or self.port is None:
            return

        def handle_message(_client, _userdata, message):
            command = parse_actuator_command(message.topic, message.payload)
            if command is None:
                print(f"Ungültiges MQTT-Kommando: {message.topic} {message.payload!r}")
                return
            on_command(*command)

        self.client.on_message = handle_message
        try:
            self.client.connect_async(self.host, self.port)
            self.client.subscribe(FAN_SET_TOPIC)
            self.client.subscribe(FLAP_SET_TOPIC)
            self.client.loop_start()
        except Exception as error:
            print(f"MQTT nicht erreichbar: {error}")

    def publish_temperature(self, sensor_id, value, timestamp):
        if self.client is None:
            return

        topic = f"{TEMPERATURE_TOPIC_PREFIX}/{sensor_id}"
        try:
            self.client.publish(
                topic,
                format_temperature_payload(sensor_id, value, timestamp),
                retain=True,
            )
        except Exception as error:
            print(f"MQTT Publish fehlgeschlagen: {error}")

    def publish_cooling_state(self, enabled, source="automatic"):
        if self.client is None:
            return

        try:
            self.client.publish(
                COOLING_STATUS_TOPIC,
                format_cooling_payload(enabled, source),
                retain=True,
            )
        except Exception as error:
            print(f"MQTT Publish fehlgeschlagen: {error}")


def build_mqtt_adapter():
    host = os.environ.get("MQTT_HOST", MQTT_HOST)
    port = int(os.environ.get("MQTT_PORT", str(MQTT_PORT)))
    username = os.environ.get("MQTT_USERNAME")
    password = os.environ.get("MQTT_PASSWORD")

    try:
        import paho.mqtt.client as mqtt
    except Exception as error:
        print(f"MQTT deaktiviert: {error}")
        return None

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    if username:
        client.username_pw_set(username, password)

    return MqttAdapter(client=client, host=host, port=port)