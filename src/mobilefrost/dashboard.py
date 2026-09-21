from datetime import timezone

from flask import Flask, jsonify, render_template, request

from .database import connect_db_once, fetch_dashboard_data


ALLOWED_HOURS = {1, 24, 168}


def load_dashboard_data(hours):
    connection = connect_db_once()
    try:
        return fetch_dashboard_data(connection, hours)
    finally:
        connection.close()


def create_app(data_loader=load_dashboard_data):
    application = Flask(__name__)

    @application.get("/")
    def dashboard_page():
        return render_template("dashboard.html")

    @application.get("/api/temperatures")
    def temperature_data():
        try:
            hours = int(request.args.get("hours", "24"))
        except ValueError:
            return jsonify(error="Ungültiger Zeitraum"), 400

        if hours not in ALLOWED_HOURS:
            return jsonify(error="Ungültiger Zeitraum"), 400

        try:
            data = data_loader(hours)
        except Exception as error:
            application.logger.error("Dashboard database error: %s", error)
            return jsonify(error="Datenbank nicht erreichbar"), 503

        return jsonify(_serialize_data(data, hours))

    return application


def _serialize_data(data, hours):
    series = {
        sensor_id: [
            {"timestamp": _serialize_timestamp(timestamp), "value": float(value)}
            for timestamp, value in points
        ]
        for sensor_id, points in data["series"].items()
    }
    latest = {
        sensor_id: {
            "timestamp": _serialize_timestamp(timestamp),
            "value": float(value),
        }
        for sensor_id, (timestamp, value) in data["latest"].items()
    }
    return {"hours": hours, "series": series, "latest": latest}


def _serialize_timestamp(timestamp):
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    return timestamp.isoformat()


def main():
    create_app().run(host="0.0.0.0", port=8080)


if __name__ == "__main__":
    main()