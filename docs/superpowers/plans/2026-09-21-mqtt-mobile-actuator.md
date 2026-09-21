# MQTT Mobile Actuator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add MQTT temperature publishing and mobile actuator control while keeping the existing serial controller, database storage, and Flask dashboard working.

**Architecture:** Add a focused `mobilefrost.mqtt_io` adapter that owns topic names, payload serialization, connection setup, command validation, publishing, and subscription callbacks. The existing `Controller` receives this adapter as an optional dependency, publishes readings/cooling state, and lets validated MQTT actuator commands write through the existing serial actuator. Compose adds Mosquitto and Node-RED as adjacent services rather than moving control logic out of Python.

**Tech Stack:** Python 3.9+, `unittest`, `paho-mqtt`, PostgreSQL, Flask, Gunicorn, Podman Compose, Eclipse Mosquitto, Node-RED.

## Global Constraints

- MQTT is the primary interface for mobile apps such as MQTT Dash or MQTT Explorer.
- The existing controller, PostgreSQL storage, and Flask dashboard remain available.
- MQTT failures must not stop serial sensor reads, LCD updates, automatic cooling, or database writes.
- Temperature topics use retained JSON messages on `mobilefrost/temperatures/<sensor_id>`.
- Cooling state uses retained JSON on `mobilefrost/status/cooling`.
- Fan commands use `mobilefrost/actuators/fan/set` with integer payloads from `0` to `255`.
- Flap commands use `mobilefrost/actuators/flap/set` with integer payloads from `0` to `90`.
- Accepted commands are forwarded to the actuator Arduino as `F:<value>` and `S:<value>`.
- Invalid topics, malformed payloads, and out-of-range values are ignored and logged.
- Broker exposure should stay limited to the trusted lab network or Tailscale; no public internet exposure is required.
- Do not create git commits during execution unless the user explicitly requests commits.

---

## File Structure

- Create `src/mobilefrost/mqtt_io.py`: MQTT configuration, topic constants, JSON serialization, command validation, optional Paho client wrapper, and no-op fallback client.
- Modify `src/mobilefrost/controller.py`: accept an optional MQTT adapter, publish temperature and cooling updates, and expose validated command handling through callbacks.
- Modify `src/mobilefrost/__main__.py`: construct the MQTT adapter from environment variables and pass it into `Controller`.
- Modify `src/mobilefrost/config.py`: add MQTT defaults and environment variable names used by `__main__.py`.
- Modify `pyproject.toml`: add `paho-mqtt` runtime dependency.
- Modify `compose.yml`: add `mosquitto` and `nodered` services plus controller MQTT environment variables.
- Modify `README.md`: document MQTT startup, mobile app topics, Node-RED usage, and trusted-network exposure.
- Modify `tests/test_app.py`: add unit tests for MQTT contracts, controller integration, dependency declaration, and Compose service wiring.

---

### Task 1: MQTT Adapter Contracts

**Files:**
- Create: `src/mobilefrost/mqtt_io.py`
- Modify: `tests/test_app.py`
- Modify: `pyproject.toml`

**Interfaces:**
- Produces: `format_temperature_payload(sensor_id: str, value: float, timestamp: datetime.datetime) -> str`
- Produces: `format_cooling_payload(enabled: bool, source: str = "automatic") -> str`
- Produces: `parse_actuator_command(topic: str, payload: bytes | str) -> tuple[str, int] | None`
- Produces: constants `TEMPERATURE_TOPIC_PREFIX`, `COOLING_STATUS_TOPIC`, `FAN_SET_TOPIC`, `FLAP_SET_TOPIC`
- Consumes: Python standard `json` and `datetime`; no controller dependency.

- [ ] **Step 1: Write failing payload serialization tests**

Add imports near the other module imports in `tests/test_app.py`:

```python
from datetime import datetime, timezone
```

Add this module import after `display = importlib.import_module("mobilefrost.display")`:

```python
mqtt_io = importlib.import_module("mobilefrost.mqtt_io")
```

Add this test class before `ArduinoIntegrationTests`:

```python
class MqttIoTests(unittest.TestCase):
    def test_formats_temperature_payload_as_json(self):
        timestamp = datetime(2026, 9, 21, 12, 34, 56, tzinfo=timezone.utc)

        payload = mqtt_io.format_temperature_payload(
            "arduino_sensor_marten",
            22.5,
            timestamp,
        )

        self.assertEqual(
            payload,
            '{"sensor_id":"arduino_sensor_marten","value":22.5,"timestamp":"2026-09-21T12:34:56+00:00"}',
        )

    def test_formats_cooling_payload_as_json(self):
        payload = mqtt_io.format_cooling_payload(True)

        self.assertEqual(payload, '{"enabled":true,"source":"automatic"}')
```

- [ ] **Step 2: Run tests to verify failure**

Run: `python -m unittest tests.test_app.MqttIoTests -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'mobilefrost.mqtt_io'`.

- [ ] **Step 3: Implement minimal payload helpers**

Create `src/mobilefrost/mqtt_io.py`:

```python
import json


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
```

- [ ] **Step 4: Run payload tests to verify pass**

Run: `python -m unittest tests.test_app.MqttIoTests -v`

Expected: PASS for both payload tests.

- [ ] **Step 5: Write failing command validation tests**

Append these methods to `MqttIoTests`:

```python
    def test_parses_valid_actuator_commands(self):
        self.assertEqual(
            mqtt_io.parse_actuator_command(mqtt_io.FAN_SET_TOPIC, b"128"),
            ("fan", 128),
        )
        self.assertEqual(
            mqtt_io.parse_actuator_command(mqtt_io.FLAP_SET_TOPIC, "90"),
            ("flap", 90),
        )

    def test_ignores_invalid_actuator_commands(self):
        invalid_commands = [
            (mqtt_io.FAN_SET_TOPIC, b"256"),
            (mqtt_io.FAN_SET_TOPIC, b"-1"),
            (mqtt_io.FLAP_SET_TOPIC, b"91"),
            (mqtt_io.FLAP_SET_TOPIC, b"open"),
            ("mobilefrost/actuators/unknown/set", b"1"),
        ]

        for topic, payload in invalid_commands:
            with self.subTest(topic=topic, payload=payload):
                self.assertIsNone(mqtt_io.parse_actuator_command(topic, payload))
```

- [ ] **Step 6: Run tests to verify failure**

Run: `python -m unittest tests.test_app.MqttIoTests -v`

Expected: FAIL with `AttributeError: module 'mobilefrost.mqtt_io' has no attribute 'parse_actuator_command'`.

- [ ] **Step 7: Implement command validation**

Append to `src/mobilefrost/mqtt_io.py`:

```python
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
```

- [ ] **Step 8: Add dependency declaration test and implementation**

Add this test to `ArduinoIntegrationTests`:

```python
    def test_pyproject_declares_mqtt_dependency(self):
        pyproject = (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")

        self.assertIn('"paho-mqtt>=2.0,<3",', pyproject)
```

Run: `python -m unittest tests.test_app.ArduinoIntegrationTests.test_pyproject_declares_mqtt_dependency -v`

Expected: FAIL because the dependency is missing.

Modify `pyproject.toml` dependencies:

```toml
dependencies = [
    "Flask>=3.0,<4",
    "gunicorn>=22,<24",
    "paho-mqtt>=2.0,<3",
    "psycopg2-binary>=2.9,<3",
    "pyserial>=3.5,<4",
]
```

- [ ] **Step 9: Run Task 1 tests**

Run: `python -m unittest tests.test_app.MqttIoTests tests.test_app.ArduinoIntegrationTests.test_pyproject_declares_mqtt_dependency -v`

Expected: PASS.

---

### Task 2: Controller MQTT Integration

**Files:**
- Modify: `src/mobilefrost/controller.py`
- Modify: `src/mobilefrost/mqtt_io.py`
- Modify: `tests/test_app.py`

**Interfaces:**
- Consumes: `mqtt_io.format_temperature_payload`, `mqtt_io.format_cooling_payload`, and topic constants from Task 1.
- Produces: `MqttAdapter.publish_temperature(sensor_id: str, value: float, timestamp: datetime.datetime) -> None`
- Produces: `MqttAdapter.publish_cooling_state(enabled: bool, source: str = "automatic") -> None`
- Produces: `MqttAdapter.start(on_command: Callable[[str, int], None]) -> None`
- Produces: `Controller.handle_actuator_command(kind: str, value: int) -> None`

- [ ] **Step 1: Write failing adapter publish tests**

Append to `MqttIoTests`:

```python
    def test_adapter_publishes_temperature_to_sensor_topic(self):
        client = RecordingMqttClient()
        adapter = mqtt_io.MqttAdapter(client=client)
        timestamp = datetime(2026, 9, 21, 12, 34, 56, tzinfo=timezone.utc)

        adapter.publish_temperature("arduino_sensor_marten", 22.5, timestamp)

        self.assertEqual(
            client.published,
            [
                (
                    "mobilefrost/temperatures/arduino_sensor_marten",
                    '{"sensor_id":"arduino_sensor_marten","value":22.5,"timestamp":"2026-09-21T12:34:56+00:00"}',
                    True,
                )
            ],
        )

    def test_adapter_publishes_cooling_state(self):
        client = RecordingMqttClient()
        adapter = mqtt_io.MqttAdapter(client=client)

        adapter.publish_cooling_state(False)

        self.assertEqual(
            client.published,
            [("mobilefrost/status/cooling", '{"enabled":false,"source":"automatic"}', True)],
        )

    def test_adapter_ignores_publish_errors(self):
        adapter = mqtt_io.MqttAdapter(client=FailingMqttClient())
        timestamp = datetime(2026, 9, 21, 12, 34, 56, tzinfo=timezone.utc)

        adapter.publish_temperature("arduino_sensor_marten", 22.5, timestamp)
        adapter.publish_cooling_state(True)
```

Add this helper near the other recording helper classes:

```python
class RecordingMqttClient:
    def __init__(self):
        self.published = []

    def publish(self, topic, payload, retain=False):
        self.published.append((topic, payload, retain))


class FailingMqttClient:
    def publish(self, _topic, _payload, retain=False):
        raise RuntimeError("broker unavailable")
```

- [ ] **Step 2: Run tests to verify failure**

Run: `python -m unittest tests.test_app.MqttIoTests -v`

Expected: FAIL with `AttributeError: module 'mobilefrost.mqtt_io' has no attribute 'MqttAdapter'`.

- [ ] **Step 3: Implement minimal adapter publishing**

Append to `src/mobilefrost/mqtt_io.py`:

```python
class MqttAdapter:
    def __init__(self, client=None):
        self.client = client

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
```

- [ ] **Step 4: Write failing controller publish and command tests**

Add these tests to `TemperatureSensorTests`:

```python
    def test_controller_publishes_temperature_reading_to_mqtt(self):
        mqtt_adapter = RecordingMqttAdapter()
        service = controller.Controller(
            RecordingSerial(),
            RecordingSensorManager([("arduino_sensor_luis", 23.5)]),
            RecordingCursor(),
            RecordingConnection(),
            clock=lambda: 42.0,
            wall_clock=lambda: datetime(2026, 9, 21, 12, 34, 56, tzinfo=timezone.utc),
            mqtt_adapter=mqtt_adapter,
            sleep_func=lambda _seconds: None,
        )

        service.run_once()

        self.assertEqual(
            mqtt_adapter.temperatures,
            [("arduino_sensor_luis", 23.5, datetime(2026, 9, 21, 12, 34, 56, tzinfo=timezone.utc))],
        )

    def test_controller_publishes_cooling_state_changes_to_mqtt(self):
        mqtt_adapter = RecordingMqttAdapter()
        service = controller.Controller(
            RecordingSerial(),
            RecordingSensorManager([("arduino_sensor_luis", 27.0)]),
            RecordingCursor(),
            RecordingConnection(),
            mqtt_adapter=mqtt_adapter,
            sleep_func=lambda _seconds: None,
        )

        service.run_once()

        self.assertEqual(mqtt_adapter.cooling_states, [(True, "automatic")])

    def test_controller_handles_mqtt_actuator_commands(self):
        actuator = RecordingSerial()
        service = controller.Controller(
            actuator,
            RecordingSensorManager([]),
            RecordingCursor(),
            RecordingConnection(),
            sleep_func=lambda _seconds: None,
        )

        service.handle_actuator_command("fan", 128)
        service.handle_actuator_command("flap", 45)

        self.assertEqual(actuator.writes, [b"F:128\n", b"S:45\n"])
```

Add this helper near other recording helpers:

```python
class RecordingMqttAdapter:
    def __init__(self):
        self.started_with = None
        self.temperatures = []
        self.cooling_states = []

    def start(self, on_command):
        self.started_with = on_command

    def publish_temperature(self, sensor_id, value, timestamp):
        self.temperatures.append((sensor_id, value, timestamp))

    def publish_cooling_state(self, enabled, source="automatic"):
        self.cooling_states.append((enabled, source))
```

- [ ] **Step 5: Run tests to verify failure**

Run: `python -m unittest tests.test_app.TemperatureSensorTests.test_controller_publishes_temperature_reading_to_mqtt tests.test_app.TemperatureSensorTests.test_controller_publishes_cooling_state_changes_to_mqtt tests.test_app.TemperatureSensorTests.test_controller_handles_mqtt_actuator_commands -v`

Expected: FAIL because `Controller.__init__` has no `wall_clock` or `mqtt_adapter` arguments and no `handle_actuator_command` method.

- [ ] **Step 6: Implement controller integration**

Modify `src/mobilefrost/controller.py` imports:

```python
from datetime import datetime, timezone
import time
```

Extend `Controller.__init__` parameters and fields:

```python
        wall_clock=lambda: datetime.now(timezone.utc),
        mqtt_adapter=None,
```

```python
        self.wall_clock = wall_clock
        self.mqtt_adapter = mqtt_adapter
        if self.mqtt_adapter is not None:
            self.mqtt_adapter.start(self.handle_actuator_command)
```

In `run_once`, after the actuator LCD write and before `_update_cooling()`, add:

```python
            if self.mqtt_adapter is not None:
                self.mqtt_adapter.publish_temperature(
                    sensor_id,
                    temperature,
                    self.wall_clock(),
                )
```

In `_update_cooling`, after setting `self.cooling_enabled`, publish state:

```python
        if self.mqtt_adapter is not None:
            self.mqtt_adapter.publish_cooling_state(cooling_enabled)
```

Add a public method to `Controller`:

```python
    def handle_actuator_command(self, kind, value):
        if kind == "fan":
            self.actuator.write(f"F:{value}\n".encode("utf-8"))
        elif kind == "flap":
            self.actuator.write(f"S:{value}\n".encode("utf-8"))
```

- [ ] **Step 7: Run Task 2 tests**

Run: `python -m unittest tests.test_app.MqttIoTests tests.test_app.TemperatureSensorTests -v`

Expected: PASS.

---

### Task 3: Runtime MQTT Client Construction

**Files:**
- Modify: `src/mobilefrost/mqtt_io.py`
- Modify: `src/mobilefrost/config.py`
- Modify: `src/mobilefrost/__main__.py`
- Modify: `tests/test_app.py`

**Interfaces:**
- Consumes: `MqttAdapter.start(on_command)` from Task 2.
- Produces: `build_mqtt_adapter() -> MqttAdapter | None`
- Produces: environment variables `MQTT_HOST`, `MQTT_PORT`, `MQTT_USERNAME`, `MQTT_PASSWORD`.

- [ ] **Step 1: Write failing config and main wiring tests**

Add to `TemperatureSensorTests`:

```python
    def test_config_declares_mqtt_defaults(self):
        self.assertEqual(config.MQTT_HOST, "mosquitto")
        self.assertEqual(config.MQTT_PORT, 1883)
```

Add to `ArduinoIntegrationTests`:

```python
    def test_main_passes_mqtt_adapter_to_controller(self):
        main_file = (PROJECT_ROOT / "src" / "mobilefrost" / "__main__.py").read_text(encoding="utf-8")

        self.assertIn("from .mqtt_io import build_mqtt_adapter", main_file)
        self.assertIn("mqtt_adapter=build_mqtt_adapter()", main_file)
```

- [ ] **Step 2: Run tests to verify failure**

Run: `python -m unittest tests.test_app.TemperatureSensorTests.test_config_declares_mqtt_defaults tests.test_app.ArduinoIntegrationTests.test_main_passes_mqtt_adapter_to_controller -v`

Expected: FAIL because config and main wiring are missing.

- [ ] **Step 3: Add MQTT config defaults**

Append to `src/mobilefrost/config.py`:

```python
MQTT_HOST = "mosquitto"
MQTT_PORT = 1883
```

- [ ] **Step 4: Implement Paho client factory**

Extend `src/mobilefrost/mqtt_io.py` with environment-aware construction:

```python
import os

from .config import MQTT_HOST, MQTT_PORT


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

    adapter = MqttAdapter(client=client, host=host, port=port)
    return adapter
```

Update `MqttAdapter.__init__` to accept connection details:

```python
    def __init__(self, client=None, host=None, port=None):
        self.client = client
        self.host = host
        self.port = port
```

Add `start` to `MqttAdapter`:

```python
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
```

- [ ] **Step 5: Wire main**

Modify `src/mobilefrost/__main__.py` imports:

```python
from .mqtt_io import build_mqtt_adapter
```

Modify `Controller(...)` construction:

```python
    Controller(
        actuator,
        sensor_manager,
        cursor,
        database_connection,
        mqtt_adapter=build_mqtt_adapter(),
    ).run()
```

- [ ] **Step 6: Run Task 3 tests**

Run: `python -m unittest tests.test_app.TemperatureSensorTests.test_config_declares_mqtt_defaults tests.test_app.ArduinoIntegrationTests.test_main_passes_mqtt_adapter_to_controller tests.test_app.MqttIoTests -v`

Expected: PASS.

---

### Task 4: Compose And Documentation

**Files:**
- Modify: `compose.yml`
- Modify: `README.md`
- Modify: `tests/test_app.py`

**Interfaces:**
- Consumes: controller environment variables from Task 3.
- Produces: runnable Compose services `mosquitto` and `nodered`.

- [ ] **Step 1: Write failing Compose tests**

Add to `ArduinoIntegrationTests`:

```python
    def test_compose_adds_mqtt_and_nodered_services(self):
        compose = (PROJECT_ROOT / "compose.yml").read_text(encoding="utf-8")

        self.assertIn("mosquitto:", compose)
        self.assertIn("image: eclipse-mosquitto:2", compose)
        self.assertIn('"1883:1883"', compose)
        self.assertIn("nodered:", compose)
        self.assertIn("image: nodered/node-red:latest", compose)
        self.assertIn('"127.0.0.1:1880:1880"', compose)

    def test_controller_receives_mqtt_environment(self):
        compose = (PROJECT_ROOT / "compose.yml").read_text(encoding="utf-8")

        self.assertIn("- MQTT_HOST=mosquitto", compose)
        self.assertIn("- MQTT_PORT=1883", compose)
```

- [ ] **Step 2: Run tests to verify failure**

Run: `python -m unittest tests.test_app.ArduinoIntegrationTests.test_compose_adds_mqtt_and_nodered_services tests.test_app.ArduinoIntegrationTests.test_controller_receives_mqtt_environment -v`

Expected: FAIL because the services and environment variables are missing.

- [ ] **Step 3: Modify Compose**

Add `mosquitto` under `services`:

```yaml
  mosquitto:
    image: eclipse-mosquitto:2
    restart: unless-stopped
    ports:
      - "1883:1883"
    command: mosquitto -c /mosquitto-no-auth.conf
```

Add MQTT dependency and environment to `controller`:

```yaml
    depends_on:
      - db
      - mosquitto
```

```yaml
      - MQTT_HOST=mosquitto
      - MQTT_PORT=1883
```

Add `nodered` under `services`:

```yaml
  nodered:
    image: nodered/node-red:latest
    restart: unless-stopped
    depends_on:
      - mosquitto
    ports:
      - "127.0.0.1:1880:1880"
    volumes:
      - nodered_data:/data
```

Add `nodered_data:` under `volumes`.

- [ ] **Step 4: Update README**

Add a section after the dashboard/Tailscale section:

````markdown
## MQTT mobile control and Node-RED

The Compose stack includes an Eclipse Mosquitto broker and Node-RED. The controller
publishes retained temperature updates to MQTT and accepts simple actuator commands
from mobile MQTT apps.

Start the stack:

```text
podman compose up -d --build
```

MQTT topics for MQTT Dash or MQTT Explorer:

- `mobilefrost/temperatures/arduino_sensor_marten`
- `mobilefrost/temperatures/arduino_sensor_andor`
- `mobilefrost/temperatures/arduino_sensor_luis`
- `mobilefrost/status/cooling`
- publish `0` to `255` to `mobilefrost/actuators/fan/set`
- publish `0` to `90` to `mobilefrost/actuators/flap/set`

The bundled broker listens on port `1883`. Expose it only on the trusted lab network
or through Tailscale. Node-RED is published on Raspberry Pi loopback port `1880`; use
Tailscale Serve or an SSH tunnel when editing flows remotely. In Node-RED, connect MQTT
nodes to broker host `mosquitto` and port `1883`.

Manual actuator commands are prototype controls. The automatic cooling rule remains
active and can overwrite manual fan or flap values on the next temperature update.
````

- [ ] **Step 5: Run Task 4 tests**

Run: `python -m unittest tests.test_app.ArduinoIntegrationTests.test_compose_adds_mqtt_and_nodered_services tests.test_app.ArduinoIntegrationTests.test_controller_receives_mqtt_environment -v`

Expected: PASS.

---

### Task 5: Full Verification

**Files:**
- Verify: all modified files

**Interfaces:**
- Consumes: all previous tasks.
- Produces: final validation evidence for the MQTT mobile actuator feature.

- [ ] **Step 1: Run full unit test suite**

Run: `python -m unittest discover -s tests -v`

Expected: PASS.

- [ ] **Step 2: Inspect working tree changes**

Run: `git --no-pager diff -- docs/superpowers/specs/2026-09-21-mqtt-mobile-actuator-design.md docs/superpowers/plans/2026-09-21-mqtt-mobile-actuator.md src/mobilefrost/mqtt_io.py src/mobilefrost/controller.py src/mobilefrost/__main__.py src/mobilefrost/config.py pyproject.toml compose.yml README.md tests/test_app.py`

Expected: Diff only contains MQTT/mobile actuator work and the approved design/plan documents.

- [ ] **Step 3: Optional Raspberry Pi smoke test with hardware**

Run on the Pi with Arduino devices attached:

```text
podman compose up -d --build
podman compose logs --tail=100 controller
```

Expected: controller starts, sensor readings continue, MQTT connection does not block serial/database behavior.

Connect MQTT Explorer to the Pi broker on port `1883` and verify retained messages under `mobilefrost/temperatures/#`. Publish `128` to `mobilefrost/actuators/fan/set` and `45` to `mobilefrost/actuators/flap/set`; the actuator Arduino should receive the matching serial commands.