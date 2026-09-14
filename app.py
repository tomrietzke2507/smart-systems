import os
import time
import serial
import psycopg2
from psycopg2 import OperationalError

# --- KONFIGURATION ---
COM_PORT = '/dev/ttyACM0'  # Der Standard-USB-Port auf dem Raspberry Pi
BAUD_RATE = 9600
SENSOR_ID = 'Arduino_Kuehlraum_1'

def connect_db():
    print("Verbinde mit PostgreSQL...")
    while True:
        try:
            conn = psycopg2.connect(
                host=os.environ.get("DB_HOST"),
                port=os.environ.get("DB_PORT"),
                database=os.environ.get("DB_NAME"),
                user=os.environ.get("DB_USER"),
                password=os.environ.get("DB_PASSWORD")
            )
            print("✅ Mit PostgreSQL verbunden!")
            return conn
        except OperationalError:
            print("Warte auf Datenbank (noch nicht bereit)...")
            time.sleep(3)

def init_db(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS temperatures (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            sensor_id VARCHAR(50),
            value NUMERIC(5, 2)
        )
    ''')
    conn.commit()

def main():
    print("Starte Mobilefrost USB-Gateway auf dem Raspberry Pi...")
    conn = connect_db()
    init_db(conn)
    cursor = conn.cursor()

    # 1. Serielle Verbindung aufbauen (mit Warteschleife)
    while True:
        try:
            ser = serial.Serial(COM_PORT, BAUD_RATE, timeout=2)
            time.sleep(2) # Dem Arduino Zeit zum Neustarten geben
            print(f"✅ Verbunden mit Arduino an {COM_PORT}")
            break
        except Exception as e:
            print(f"❌ Warte auf Arduino an {COM_PORT}... Einstecken!")
            time.sleep(3)

    # 2. Endlosschleife zum Datenlesen
    while True:
        try:
            # Zeile einlesen und bereinigen
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            
            # Prüfen, ob es unsere gesuchte Temperatur-Zeile ist
            if line and "Aktuelle Temperatur:" in line:
                # Zahl vom Text trennen
                temp_str = line.split(":")[1].strip()
                temp_val = float(temp_str)
                
                print(f"🌡️ Gemessen: {temp_val}°C -> Speichere in DB")
                
                # In die Datenbank schreiben
                cursor.execute(
                    "INSERT INTO temperatures (sensor_id, value) VALUES (%s, %s)", 
                    (SENSOR_ID, temp_val)
                )
                conn.commit()
                
        except Exception as e:
            print(f"⚠️ Fehler beim Lesen/Speichern: {e}")
            time.sleep(1)

if __name__ == '__main__':
    main()