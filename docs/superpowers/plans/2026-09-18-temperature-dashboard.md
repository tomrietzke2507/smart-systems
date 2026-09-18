# Temperature Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a tailnet-only web dashboard for current and historical temperatures.

**Architecture:** A Flask application in the Mobilefrost package queries PostgreSQL through a small repository boundary and serves an HTML dashboard plus JSON API. Compose runs it as a separate service on Raspberry Pi loopback; Tailscale Serve provides HTTPS to authorized tailnet clients.

**Tech Stack:** Python 3.9, Flask, PostgreSQL, Chart.js, HTML/CSS/JavaScript, Podman Compose, Tailscale Serve

## Global Constraints

- Default range is 24 hours; allowed ranges are 1, 24, and 168 hours.
- Browser data refresh is every 10 seconds.
- Dashboard binds only to `127.0.0.1:8080` on the host.
- No Tailscale Funnel or public exposure.
- Controller operation remains independent from dashboard availability.

---

### Task 1: Dashboard Repository And API

**Files:**
- Create: `src/mobilefrost/dashboard.py`
- Modify: `src/mobilefrost/database.py`
- Modify: `pyproject.toml`
- Test: `tests/test_dashboard.py`

- [ ] Add failing tests for default/allowed ranges, invalid range, serialized readings, and database HTTP 503.
- [ ] Add one-shot database connection and read queries.
- [ ] Implement the Flask app factory and JSON endpoint.
- [ ] Run dashboard API tests and require pass.

### Task 2: Monitoring Interface

**Files:**
- Create: `src/mobilefrost/templates/dashboard.html`
- Create: `src/mobilefrost/static/dashboard.css`
- Create: `src/mobilefrost/static/dashboard.js`
- Modify: `pyproject.toml`
- Test: `tests/test_dashboard.py`

- [ ] Add a failing test for page controls and asset references.
- [ ] Implement current values, segmented range selector, shared chart, refresh status, and loading/empty/error states.
- [ ] Include package data and run tests.
- [ ] Verify desktop and mobile rendering in a browser.

### Task 3: Compose And Tailscale Operation

**Files:**
- Modify: `compose.yml`
- Modify: `README.md`
- Modify: `tests/test_app.py`

- [ ] Add failing tests for dashboard command and loopback-only port binding.
- [ ] Add the independent dashboard service.
- [ ] Document Podman start, Tailscale Serve, MagicDNS, ACL requirements, status, and disable commands.
- [ ] Run all tests, syntax checks, Compose validation, image build, and browser smoke checks.