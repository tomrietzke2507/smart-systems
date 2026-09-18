# smart-systems

Mobilefrost controller for the Smart Systems course.

## Project structure

```text
src/mobilefrost/   Python controller package
tests/             Automated tests
sketches/          Arduino sketches, each in its own folder
docs/              Design and implementation notes
compose.yml        Controller and PostgreSQL services
Dockerfile         Controller image
pyproject.toml     Python package and dependencies
```

Run the tests locally with:

```text
python -m unittest discover -s tests -v
```

## Raspberry Pi / Podman

The controller container expects these stable device names:

- `/dev/arduino_sensor_marten`
- `/dev/arduino_sensor_andor`
- `/dev/arduino_sensor_luis`
- `/dev/arduino_aktor`

All sensors use the same temperature output format:

```text
Aktuelle Temperatur: 22.50
```

Each reading is written to the `temperatures` table with the matching `sensor_id`.
The Luis sensor additionally reports `Aktuelle Luftfeuchtigkeit: <value>`.
The actuator Arduino receives all latest temperatures as `D:<marten>;<andor>;<luis>`, for example `D:21.7;22.4;23.9`. On the 16x2 LCD, Marten is shown in the first row on the left, Andor on the right, and Luis in the second row on the right. The fan status remains in the second row on the left.

Luis has a configured temperature correction of `-1.0 °C`. Every incoming
temperature updates the LCD immediately; the DHT11 supplies a new measurement about
every two seconds. Database writes are limited independently to one value per sensor
every ten seconds.

The controller starts with any number of connected sensors. Missing sensors are
shown as `--.-` and retried every five seconds. A sensor that is connected later
is detected without restarting the container. The actuator remains required; if
it is missing, Docker restarts the controller until it becomes available.

The Arduino sketches are stored below `sketches/`. Flash them onto the boards
before starting Docker; Arduino code does not run inside the controller container.
For `sketch_humidity`, install the Arduino libraries `DHT sensor library` and
`Adafruit Unified Sensor` in the Arduino IDE.

Start the services on the Linux host that exposes the four device paths:

```text
podman compose up -d --build
```

The Compose configuration mounts Linux `/dev` so hot-plugged serial devices become
visible inside the running container. `group_add: keep-groups` preserves the host
user's supplementary groups for serial access with rootless Podman.

## Temperature dashboard over Tailscale

The `dashboard` service reads the existing PostgreSQL measurements and is published
only on Raspberry Pi loopback port `8080`. It shows current values and the last hour,
24 hours, or seven days, refreshing every ten seconds.

After starting the Compose stack, verify the local service on the Pi:

```text
curl http://127.0.0.1:8080
podman compose logs --tail=100 dashboard
```

Enable **MagicDNS** in the Tailscale admin console under **DNS** if it is not already
enabled. Then configure a persistent, tailnet-only HTTPS proxy on the Pi:

```text
sudo tailscale serve --bg http://127.0.0.1:8080
tailscale serve status
```

The first command prints the HTTPS URL, normally similar to
`https://raspberrypi.<tailnet>.ts.net`. Open that URL on the laptop while Tailscale is
connected. The first Serve setup can print an admin-console link for enabling HTTPS;
open it once and approve the feature.

The default Tailscale policy allows devices in the same tailnet to connect, so no ACL
change is required. If the tailnet uses a custom deny-by-default policy, grant the
laptop user or device access to TCP port `443` on the Raspberry Pi. Do not enable
Tailscale Funnel, because Funnel would expose the dashboard publicly.

Inspect or disable the proxy with:

```text
tailscale serve status
sudo tailscale serve --https=443 off
```

## Windows bridge

For local Windows testing, adjust the COM ports in `windows_serial_bridge.py`. The bridge writes both sensors to the same PostgreSQL table using the sensor IDs `arduino_sensor_marten` and `arduino_sensor_andor`.
