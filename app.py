import os, time, serial, psycopg2
from psycopg2 import OperationalError

# Passe hier Deine USB-Namen an (z.B. /dev/arduino_sensor_marten oder /dev/ttyACM0)
SENSORS = [
    {"id": "arduino_sensor_marten", "port": "/dev/arduino_sensor_marten"},
    {"id": "arduino_sensor_andor", "port": "/dev/arduino_sensor_andor"},
    {"id": "arduino_sensor_luis", "port": "/dev/arduino_sensor_luis"},
]
PORT_AKTOR  = '/dev/arduino_aktor'  
BAUD_RATE = 9600

def parse_temperature(line):
    if line and "Aktuelle Temperatur:" in line:
        return float(line.split(":")[1].strip())
    return None

def format_display_value(temp_val):
    if temp_val is None:
        return "--.-"
    return f"{temp_val:.1f}"[-4:]

def format_display_command(last_temperatures):
    values = [
        format_display_value(last_temperatures.get(sensor["id"]))
        for sensor in SENSORS
    ]
    return f"D:{';'.join(values)}\n"

def connect_db():
    while True:
        try:
            conn = psycopg2.connect(
                host=os.environ.get("DB_HOST"), port=os.environ.get("DB_PORT"),
                database=os.environ.get("DB_NAME"), user=os.environ.get("DB_USER"),
                password=os.environ.get("DB_PASSWORD")
            )
            return conn
        except OperationalError:
            time.sleep(3)

# FIX 1: Tabelle sicherstellen, bevor wir reinschreiben
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
    print("Starte Mobilefrost Zentrale (Sensor & Aktor)...")
    conn = connect_db()
    init_db(conn) # Ruft den Fix 1 auf
    cursor = conn.cursor()
    
    try:
        sensor_connections = [
            {
                "id": sensor["id"],
                "serial": serial.Serial(sensor["port"], BAUD_RATE, timeout=2),
            }
            for sensor in SENSORS
        ]
        ser_aktor = serial.Serial(PORT_AKTOR, BAUD_RATE, timeout=2)
        time.sleep(2)
        print("✅ Sensoren und Aktor verbunden!")
    except Exception as e:
        print(f"❌ USB-Fehler: {e}")
        exit(1)

    last_temperatures = {}

    while True:
        try:
            for sensor in sensor_connections:
                line = sensor["serial"].readline().decode('utf-8', errors='ignore').strip()
                temp_val = parse_temperature(line)
                if temp_val is None:
                    continue

                sensor_id = sensor["id"]
                last_temperatures[sensor_id] = temp_val
                print(f"Gemessen ({sensor_id}): {temp_val}°C")
                
                # 1. Daten in Datenbank speichern
                cursor.execute("INSERT INTO temperatures (sensor_id, value) VALUES (%s, %s)", (sensor_id, temp_val))
                conn.commit()

                # 2. Display mit den letzten Werten aller Sensoren aktualisieren
                max_temp = max(last_temperatures.values())
                display_cmd = format_display_command(last_temperatures)
                print(f"LCD-Kommando: {display_cmd.strip()}")
                ser_aktor.write(display_cmd.encode('utf-8'))
                time.sleep(0.2) 

                # 3. Logik: Kühlen & Lüften, sobald ein Sensor > 26 Grad misst
                if max_temp > 26.0:
                    print("🚨 Zu warm! Lüfter AN & Klappe AUF.")
                    ser_aktor.write("F:255\n".encode('utf-8'))
                    time.sleep(0.5) 
                    ser_aktor.write("S:90\n".encode('utf-8'))
                else:
                    print("✅ Temperatur OK. Lüfter AUS & Klappe ZU.")
                    ser_aktor.write("F:0\n".encode('utf-8'))
                    time.sleep(0.5)
                    ser_aktor.write("S:0\n".encode('utf-8'))
                    
        except Exception as e:
            print(f"Fehler: {e}")
            # FIX 2: Wenn die Datenbank meckert, die blockierte Transaktion zurücksetzen!
            conn.rollback() 
            time.sleep(1)

if __name__ == '__main__':
    main()