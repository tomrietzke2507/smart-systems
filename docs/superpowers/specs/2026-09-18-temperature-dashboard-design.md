# Temperature Dashboard Design

## Goal

Provide a responsive web dashboard for current temperatures and historical trends.
The dashboard is reachable from the laptop only through the existing Tailscale
tailnet and does not expose a public internet endpoint.

## Architecture

A separate `dashboard` service runs from the existing Mobilefrost image. It uses
Flask and read-only queries against the existing PostgreSQL `temperatures` table.
The controller remains independent, so dashboard failures cannot interrupt sensor
collection or actuator control.

Compose publishes the dashboard only on Raspberry Pi loopback as
`127.0.0.1:8080:8080`. Tailscale Serve terminates HTTPS on the Pi and proxies tailnet
requests to `http://127.0.0.1:8080`. Tailscale Funnel is not used.

## API And Data

`GET /api/temperatures?hours=<value>` accepts only `1`, `24`, or `168`, with `24`
as the default. It returns ordered timestamp/value points grouped by the three known
sensor IDs and the latest reading for each sensor. Values are serialized as numbers
and timestamps as ISO 8601 strings. Database failures return HTTP 503 JSON without
leaking credentials or query internals.

## User Interface

The first viewport is the monitoring workspace, not a landing page. It contains a
compact header with connection and last-refresh status, three current-value panels,
a segmented 1h/24h/7d selector, and one shared temperature chart with a distinct
color per sensor. The browser refreshes data every ten seconds without reloading the
page. Loading, empty, stale, and error states remain visible and do not shift the
layout. The layout supports laptop and mobile widths.

## Tailscale Operation

On the Raspberry Pi, `tailscale serve --bg http://127.0.0.1:8080` creates a persistent
tailnet-only HTTPS endpoint. MagicDNS must be enabled in the Tailscale DNS settings.
With the default allow-all tailnet policy no access-rule change is required. A custom
deny-by-default policy must grant the laptop user or device access to TCP port 443 on
the Pi. The resulting URL and current proxy state are shown by `tailscale serve status`.

## Testing

Unit tests cover accepted and rejected time windows, query result serialization,
database failure responses, HTML delivery, Compose loopback binding, and the dashboard
container command. Browser verification checks desktop and mobile rendering, chart
pixels, loading/data/error states, and repeated refreshes.