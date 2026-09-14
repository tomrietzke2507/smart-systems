import serial
import psycopg2
import time

# --- KONFIGURATION ---
COM_PORT = 'COM4'  # <-- HIER DEINEN COM-PORT EINTRAGEN
BAUD_RATE = 9600
SENSOR_ID = 'Arduino_USB_1'

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

def main():
    conn = connect_db()
    cursor = conn.cursor()

    print(f"Öffne Verbindung zu {COM_PORT}...")
    try:
        # Verbindung zum Arduino aufbauen
        ser = serial.Serial(COM_PORT, BAUD_RATE, timeout=2)
        time.sleep(2) # Kurz warten, da der Arduino beim Verbinden oft neu startet
        print("✅ Verbunden! Lese Daten...\n")
    except Exception as e:
        print(f"❌ Konnte COM-Port nicht öffnen. Ist der Serielle Monitor noch offen? Fehler: {e}")
        exit(1)

    while True:
        try:
            # Zeile über USB einlesen und dekodieren
            line = ser.readline().decode('utf-8').strip()
            
            # Wenn die Zeile Daten enthält und unser Muster aufweist
            if line and "Aktuelle Temperatur:" in line:
                # Zerschneide den String am Doppelpunkt und nimm den rechten Teil
                # Aus "Aktuelle Temperatur: 22.50" wird "22.50"
                temp_str = line.split(":")[1].strip()
                temp_val = float(temp_str)
                
                print(f"Gelesen über USB: {temp_val}°C -> Speichere in DB...")
                
                # In die Datenbank schreiben
                cursor.execute(
                    "INSERT INTO temperatures (sensor_id, value) VALUES (%s, %s)", 
                    (SENSOR_ID, temp_val)
                )
                conn.commit()
                
        except Exception as e:
            print(f"Fehler in der Leseschleife: {e}")
            time.sleep(1)

if __name__ == '__main__':
    main()