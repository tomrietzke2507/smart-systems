# Resilient Controller Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split the controller into logical modules and keep it running while any subset of sensors is available.

**Architecture:** Configuration, serial sensor lifecycle, PostgreSQL persistence, and orchestration are separate modules. A `SensorManager` opens and retries each sensor independently; `Controller` consumes its available connections and never lets one sensor or database write stop the others.

**Tech Stack:** Python 3.9, pyserial, psycopg2, unittest, Docker Compose

## Global Constraints

- Preserve sensor IDs and serial paths.
- Preserve the LCD command `D:<marten>;<andor>;<luis>`.
- Keep the actuator mandatory and sensors optional.
- Do not require Arduino compilation inside Docker.

---

### Task 1: Extract Pure Configuration And Formatting

**Files:**
- Create: `config.py`
- Create: `display.py`
- Modify: `test_app.py`

**Interfaces:**
- `SENSORS: tuple[dict[str, str], ...]`, `PORT_ACTUATOR: str`, `BAUD_RATE: int`
- `parse_temperature(line: str) -> float | None`
- `format_display_command(temperatures: dict[str, float]) -> str`

- [ ] Move tests to direct module imports and verify they fail before modules exist.
- [ ] Implement constants, parser, display formatting, and initial display write.
- [ ] Run `python -m unittest -v` and require all focused tests to pass.

### Task 2: Extract Database Persistence

**Files:**
- Create: `database.py`
- Modify: `test_app.py`

**Interfaces:**
- `connect_db() -> connection`
- `init_db(connection) -> None`
- `store_temperature(cursor, connection, sensor_id: str, temperature: float) -> bool`

- [ ] Change transaction tests to import `database` and verify failure before extraction.
- [ ] Move connection, schema initialization, commit, and rollback behavior unchanged.
- [ ] Run the database-focused tests and require pass.

### Task 3: Add Independent Sensor Lifecycle

**Files:**
- Create: `sensor_io.py`
- Modify: `test_app.py`

**Interfaces:**
- `SensorManager(serial_factory, clock)`
- `connect_available() -> None`
- `retry_missing() -> None`
- `readings() -> iterable[tuple[str, float]]`

- [ ] Add tests proving partial connection, delayed reconnection, and isolated read failure.
- [ ] Run tests and verify expected missing-symbol failures.
- [ ] Implement independent connection state and retry timestamps.
- [ ] Run sensor manager tests and require pass.

### Task 4: Extract Controller And Entry Point

**Files:**
- Create: `controller.py`
- Modify: `app.py`
- Modify: `test_app.py`

**Interfaces:**
- `Controller.run_once() -> None`
- `Controller.run() -> None`
- `app.main() -> None`

- [ ] Add a controller test proving one available reading updates display and database while other sensors are absent.
- [ ] Verify the new test fails before extraction.
- [ ] Implement orchestration and reduce `app.py` to construction plus `main()`.
- [ ] Run all unit tests and require pass.

### Task 5: Package And Validate

**Files:**
- Modify: `Dockerfile`
- Modify: `README.md`

- [ ] Change Docker build input from only `app.py` to all runtime Python modules.
- [ ] Document optional sensors and automatic reconnection.
- [ ] Run `python -m unittest -v` and `python -m py_compile app.py config.py display.py database.py sensor_io.py controller.py`.
- [ ] Run `docker compose config` and `docker compose build controller` when the container engine is available.