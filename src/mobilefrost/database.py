import os
import time

import psycopg2
from psycopg2 import OperationalError


def connect_db_once():
    return psycopg2.connect(
        host=os.environ.get("DB_HOST"),
        port=os.environ.get("DB_PORT"),
        database=os.environ.get("DB_NAME"),
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASSWORD"),
    )


def connect_db():
    while True:
        try:
            return connect_db_once()
        except OperationalError as error:
            print(f"Datenbank nicht erreichbar: {error}")
            time.sleep(3)


def init_db(connection):
    try:
        cursor = connection.cursor()
        cursor.execute("""CREATE TABLE IF NOT EXISTS temperatures (
            id SERIAL PRIMARY KEY, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            sensor_id VARCHAR(50), value NUMERIC(5, 2))""")
        connection.commit()
    except Exception as error:
        connection.rollback()
        print(f"Fehler beim Erstellen der Tabelle: {error}")


def store_temperature(cursor, connection, sensor_id, temperature):
    try:
        cursor.execute(
            "INSERT INTO temperatures (sensor_id, value) VALUES (%s, %s)",
            (sensor_id, temperature),
        )
        connection.commit()
        return True
    except Exception as error:
        connection.rollback()
        print(f"Datenbankfehler ({sensor_id}): {error}")
        return False


def fetch_dashboard_data(connection, hours):
    cursor = connection.cursor()
    try:
        cursor.execute(
            """SELECT sensor_id, timestamp, value
               FROM temperatures
               WHERE timestamp >= CURRENT_TIMESTAMP - (%s * INTERVAL '1 hour')
               ORDER BY timestamp ASC""",
            (hours,),
        )
        history_rows = cursor.fetchall()
        cursor.execute(
            """SELECT DISTINCT ON (sensor_id) sensor_id, timestamp, value
               FROM temperatures
               ORDER BY sensor_id, timestamp DESC"""
        )
        latest_rows = cursor.fetchall()
    finally:
        cursor.close()

    series = {}
    for sensor_id, timestamp, value in history_rows:
        series.setdefault(sensor_id, []).append((timestamp, float(value)))

    latest = {
        sensor_id: (timestamp, float(value))
        for sensor_id, timestamp, value in latest_rows
    }
    return {"series": series, "latest": latest}