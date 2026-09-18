# Resilient Controller Design

## Goal

The controller starts when zero, one, two, or three temperature sensors are
available. Available sensors continue updating the LCD, actuator, and database.
Missing or disconnected sensors are retried automatically without restarting the
container.

## Modules

- `src/mobilefrost/config.py` owns sensor IDs, serial device paths, baud rate, and retry timing.
- `src/mobilefrost/sensor_io.py` parses readings and manages independent serial sensor connections.
- `src/mobilefrost/database.py` connects to PostgreSQL, initializes the schema, and stores readings
  with transaction rollback on errors.
- `src/mobilefrost/controller.py` coordinates measurements, display,
  cooling, persistence, and sensor reconnection.
- `src/mobilefrost/display.py` owns LCD command formatting.
- `src/mobilefrost/__main__.py` constructs dependencies and is started with
  `python -m mobilefrost`.
- `tests/test_app.py` contains unit and integration contract tests.

## Runtime Behavior

The actuator is required because no LCD or cooling control is possible without it.
After connecting, it immediately receives `D:--.-;--.-;--.-`. Each sensor is opened
independently. Failed connections are logged and retried periodically. A read error
disconnects only that sensor and schedules it for reconnection. Missing sensor values
remain `--.-` on the LCD; available values are stored under their existing sensor ID.
Database failures roll back the affected transaction and do not block LCD or actuator
updates.

## Measurement Timing And Calibration

Each sensor profile may define a temperature offset. Luis uses `-1.0` degrees Celsius
to compensate for the observed DHT11 deviation; display, cooling, and stored values all
use the corrected temperature. The controller sends every incoming temperature to the
LCD immediately and does not add artificial delays. The DHT11 remains limited by its
reliable two-second Arduino measurement period.

Database writes are throttled independently per sensor to at most one value every ten
seconds. A failed write is retried on the next reading. Fan and servo commands are sent
only when the cooling state changes, avoiding serial delays and duplicate commands.

## Docker And Tests

`pyproject.toml` defines the installable package and runtime dependencies. The Docker
image installs that package before starting `python -m mobilefrost`. Unit tests cover partial
startup, reconnection, parsing, display formatting, database transactions, and the
existing Arduino/Compose contracts. Hardware behavior remains verifiable only on the
Linux host with the mapped `/dev/arduino_*` devices.