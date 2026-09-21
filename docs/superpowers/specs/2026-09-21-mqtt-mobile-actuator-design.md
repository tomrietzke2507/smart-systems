# MQTT Mobile Actuator Design

## Goal

Extend the MobileFrost prototype so mobile devices can receive temperature
information through MQTT and send actuator commands without entering the cooled
truck area. The existing controller, PostgreSQL storage, and Flask dashboard remain
available. MQTT becomes the primary interface for mobile apps such as MQTT Dash or
MQTT Explorer.

## Architecture

The Compose stack adds a local MQTT broker and a Node-RED service. The broker is
reachable inside the Compose network and, on the Raspberry Pi, can be exposed to the
trusted local network or tailnet for mobile clients. Node-RED connects to the same
broker and is available for low-code flows, demos, and later optimizations without
moving the critical sensor and actuator loop out of Python.

The Python controller gains a small MQTT adapter. It publishes sensor and cooling
state updates after successful readings and subscribes to actuator command topics.
MQTT failures are logged but do not stop serial sensor reads, LCD updates, automatic
cooling, or database writes.

## Topics And Payloads

Temperature readings are published as retained JSON messages on
`mobilefrost/temperatures/<sensor_id>`:

```json
{
  "sensor_id": "arduino_sensor_marten",
  "value": 22.5,
  "timestamp": "2026-09-21T12:34:56Z"
}
```

The cooling state is published as retained JSON on `mobilefrost/status/cooling`:

```json
{
  "enabled": true,
  "source": "automatic"
}
```

Mobile actuator commands use simple payloads so they are easy to enter in MQTT Dash
and MQTT Explorer:

- `mobilefrost/actuators/fan/set`: integer `0` to `255`
- `mobilefrost/actuators/flap/set`: integer `0` to `90`

Invalid topics, malformed payloads, and out-of-range values are ignored and logged.
Accepted commands are forwarded to the existing actuator Arduino protocol as `F:<value>`
and `S:<value>`.

## Runtime Behavior

Automatic cooling remains the safety default. It still switches the fan and flap based
on the latest corrected temperatures. Manual MQTT commands are prototype controls and
may be overwritten by the next automatic cooling state change. This keeps the existing
temperature protection behavior predictable while still demonstrating remote actuator
control from a mobile device.

On startup, the controller attempts to connect to the MQTT broker with configured host,
port, and optional credentials. If the broker is missing, the controller continues in
offline mode and retries in the background. Published messages use the last available
reading time from the controller process; database write throttling remains independent.

## Configuration And Deployment

`compose.yml` adds `mosquitto` and `nodered` services. The controller receives MQTT
configuration through environment variables such as `MQTT_HOST`, `MQTT_PORT`,
`MQTT_USERNAME`, and `MQTT_PASSWORD`. Local development can use the bundled broker
without credentials. A course or company broker can be used by changing environment
values instead of changing code.

The README documents how to start the stack, which topics to use in MQTT Dash or MQTT
Explorer, and how Node-RED connects to the broker. Broker exposure should stay limited
to the trusted lab network or Tailscale; no public internet exposure is required.

## Testing

Unit tests cover MQTT topic names, JSON payload serialization, actuator command
validation, ignored invalid payloads, and controller behavior when MQTT is disabled or
temporarily unavailable. Existing controller and dashboard tests continue to verify the
serial, database, and web paths. A manual smoke test verifies that MQTT Explorer receives
temperature topics and that publishing valid fan or flap values reaches the actuator
Arduino.