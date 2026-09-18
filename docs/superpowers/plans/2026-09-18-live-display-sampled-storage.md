# Live Display And Sampled Storage Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Update the LCD on every reading while storing corrected sensor values at most every ten seconds per sensor.

**Architecture:** Sensor profiles own calibration offsets, which `SensorManager` applies at ingestion. `Controller` updates the display immediately, tracks independent successful database-write timestamps, and sends cooling commands only on state changes.

**Tech Stack:** Python 3.9, unittest, pyserial, Arduino DHT11

## Global Constraints

- Luis temperature offset is exactly `-1.0` degrees Celsius.
- DHT11 Arduino measurement period remains two seconds.
- Database interval is exactly ten seconds per sensor.
- Failed database writes are retried on the next reading.

---

### Task 1: Calibrate Luis At Ingestion

**Files:**
- Modify: `src/mobilefrost/config.py`
- Modify: `src/mobilefrost/sensor_io.py`
- Test: `tests/test_app.py`

- [ ] Add a failing test proving Luis `24.0` becomes `23.0` while other sensors remain unchanged.
- [ ] Add profile offsets and apply them in `SensorManager.readings()`.
- [ ] Run the focused sensor tests and require pass.

### Task 2: Separate Display And Persistence Timing

**Files:**
- Modify: `src/mobilefrost/config.py`
- Modify: `src/mobilefrost/controller.py`
- Test: `tests/test_app.py`

- [ ] Add failing tests for immediate LCD writes, per-sensor ten-second storage, retry after DB failure, and cooling commands only on state changes.
- [ ] Inject a monotonic clock and implement successful-write timestamps per sensor.
- [ ] Remove artificial actuator sleeps from each reading.
- [ ] Run all tests and package syntax checks.