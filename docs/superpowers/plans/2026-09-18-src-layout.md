# Python Src Layout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the controller into an installable `src/mobilefrost` package with tests under `tests`.

**Architecture:** Runtime modules become one package using relative imports. `pyproject.toml` defines Python 3.9 compatibility and runtime dependencies; Docker installs the local package and starts its module entry point.

**Tech Stack:** Python 3.9, setuptools, unittest, Docker Compose

## Global Constraints

- Preserve all runtime behavior and Arduino paths.
- Keep `sketches/`, `docs/`, `compose.yml`, `Dockerfile`, and `README.md` at repository root.
- Keep tests runnable without a prior local package installation.

---

### Task 1: Move Python Sources And Tests

**Files:**
- Move: `app.py` to `src/mobilefrost/__main__.py`
- Move: `config.py`, `controller.py`, `database.py`, `display.py`, `sensor_io.py` to `src/mobilefrost/`
- Create: `src/mobilefrost/__init__.py`
- Move: `test_app.py` to `tests/test_app.py`

- [ ] Move files without changing behavior.
- [ ] Run tests and verify imports fail from the old module paths.
- [ ] Change runtime imports to package-relative imports and test imports to `mobilefrost.*`.
- [ ] Run `python -m unittest discover -s tests -v` and require pass.

### Task 2: Add Packaging And Container Entry Point

**Files:**
- Create: `pyproject.toml`
- Modify: `Dockerfile`
- Modify: `tests/test_app.py`

- [ ] Add a failing Docker contract test for package installation and module startup.
- [ ] Define the package metadata and dependencies in `pyproject.toml`.
- [ ] Copy `pyproject.toml` and `src/`, install the package, and run `python -m mobilefrost` in Docker.
- [ ] Run all tests and require pass.

### Task 3: Clean Repository Metadata And Documentation

**Files:**
- Create: `.gitignore`
- Modify: `README.md`

- [ ] Ignore Python bytecode, virtual environments, and test caches.
- [ ] Document the final directory layout and local test command.
- [ ] Run package compilation, all tests, Compose validation, and editor diagnostics.