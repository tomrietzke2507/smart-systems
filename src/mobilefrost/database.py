import os
import time

import psycopg2
from psycopg2 import OperationalError


def connect_db():
    while True:
        try:
            return psycopg2.connect(
                host=os.environ.get("DB_HOST"),
                port=os.environ.get("DB_PORT"),
                database=os.environ.get("DB_NAME"),
                user=os.environ.get("DB_USER"),
                password=os.environ.get("DB_PASSWORD"),
            )
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