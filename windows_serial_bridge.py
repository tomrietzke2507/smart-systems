import serial
import psycopg2
import time

# --- KONFIGURATION ---
SENSORS = [
    {"id": "arduino_sensor_marten", "port": "COM4"},  # <-- COM-Port anpassen
    {"id": "arduino_sensor_andor", "port": "COM5"},   # <-- COM-Port anpassen
]
BAUD_RATE = 9600

def parse_temperature(line):
    if line and "Aktuelle Temperatur:" in line:
        return float(line.split(":")[1].strip())
    return None

def connect_db():
    print("Verbinde mit PostgreSQL in Podman...")
    try:
        conn = psycopg2.connect(
            host="localhost",      # Da Podman den Port an Windows freigibt
            port=5432,
            database="mobilefrost_db",
            user="mobilefrost_user",
            password="secretpassword"
        )
        print("✅ Datenbankverbindung steht!")
        return conn
    except Exception as e:
        print(f"❌ Fehler bei der DB-Verbindung: {e}")
        exit(1)

def init_db(conn):
    try:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS temperatures (
            id SERIAL PRIMARY KEY, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            sensor_id VARCHAR(50), value NUMERIC(5, 2))''')
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Fehler beim Erstellen der Tabelle: {e}")

def main():
    conn = connect_db()
    init_db(conn)
    cursor = conn.cursor()

    try:
        sensor_connections = [
            {
                "id": sensor["id"],
                "serial": serial.Serial(sensor["port"], BAUD_RATE, timeout=2),
            }
            for sensor in SENSORS
        ]
        time.sleep(2) # Kurz warten, da der Arduino beim Verbinden oft neu startet
        print("✅ Sensoren verbunden! Lese Daten...\n")
    except Exception as e:
        print(f"❌ Konnte COM-Port nicht öffnen. Ist der Serielle Monitor noch offen? Fehler: {e}")
        exit(1)

    while True:
        try:
            for sensor in sensor_connections:
                # Zeile über USB einlesen und dekodieren
                line = sensor["serial"].readline().decode('utf-8', errors='ignore').strip()
                temp_val = parse_temperature(line)
                if temp_val is None:
                    continue
                
                print(f"Gelesen über USB ({sensor['id']}): {temp_val}°C -> Speichere in DB...")
                
                # In die Datenbank schreiben
                cursor.execute(
                    "INSERT INTO temperatures (sensor_id, value) VALUES (%s, %s)", 
                    (sensor["id"], temp_val)
                )
                conn.commit()
                
        except Exception as e:
            print(f"Fehler in der Leseschleife: {e}")
            conn.rollback()
            time.sleep(1)

if __name__ == '__main__':
    main()