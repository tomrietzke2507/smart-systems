import os, time, serial, psycopg2
from psycopg2 import OperationalError

# Passe hier Deine USB-Namen an (z.B. /dev/arduino_sensor oder /dev/ttyACM0)
PORT_SENSOR = '/dev/arduino_sensor'  
PORT_AKTOR  = '/dev/arduino_aktor'  
BAUD_RATE = 9600

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
        ser_sensor = serial.Serial(PORT_SENSOR, BAUD_RATE, timeout=2)
        ser_aktor = serial.Serial(PORT_AKTOR, BAUD_RATE, timeout=2)
        time.sleep(2)
        print("✅ Beide Arduinos verbunden!")
    except Exception as e:
        print(f"❌ USB-Fehler: {e}")
        exit(1)

    while True:
        try:
            line = ser_sensor.readline().decode('utf-8', errors='ignore').strip()
            if line and "Aktuelle Temperatur:" in line:
                temp_val = float(line.split(":")[1].strip())
                print(f"Gemessen: {temp_val}°C")
                
                # 1. Daten in Datenbank speichern
                cursor.execute("INSERT INTO temperatures (sensor_id, value) VALUES (%s, %s)", ("Arduino_1", temp_val))
                conn.commit()

                # 2. Display aktualisieren
                display_cmd = f"T:{temp_val:.1f}\n"
                ser_aktor.write(display_cmd.encode('utf-8'))
                time.sleep(0.2) 

                # 3. Logik: Kühlen & Lüften bei > 26 Grad
                if temp_val > 26.0:
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