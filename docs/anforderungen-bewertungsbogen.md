# Nachweis zum Bewertungsbogen

Dieses Dokument ordnet die Anforderungen aus dem Bewertungsbogen „Technisches
Fachgespräch - Umsetzung Challenge 1-2“ dem aktuellen Stand des Repositories zu.
„Umgesetzt“ bedeutet, dass der Nachweis im Code, in der Konfiguration oder im
Arduino-Sketch erkennbar ist. Der praktische Hardwareaufbau und die Präsentation
müssen zusätzlich live vorgeführt werden.

## Challenge I: Ice Truck Problem

| Anforderung | Punkte | Status | Nachweis / offene Ergänzung |
| --- | ---: | --- | --- |
| Mindestens ein Sensor ist am Arduino funktionsfähig angeschlossen | 5 | Umgesetzt | [`sketch_humidity.ino`](../sketches/sketch_humidity/sketch_humidity.ino) liest einen DHT11 aus und sendet Temperatur sowie Luftfeuchte. Der elektrische Aufbau muss praktisch gezeigt werden. |
| Mindestens eine LED ist am Arduino funktionsfähig angeschlossen | 4 | Umgesetzt | Der Sketch verwendet die RGB-LED-Pins 9, 10 und 11 und setzt sie mit `analogWrite`. Die leuchtende LED muss live demonstriert werden. |
| Die Leuchtstärke der LED ändert sich abhängig vom Sensorwert | 6 | Teilweise | [`sketch_humidity.ino`](../sketches/sketch_humidity/sketch_humidity.ino) ändert abhängig von der Temperatur die Farbe. Die drei Farbkanäle werden jedoch nur mit festen Werten angesteuert; eine echte temperaturabhängige Helligkeitskurve ist im Repository nicht belegt. Bei roter LED wird der Lüfter ab `> 26.0 °C` eingeschaltet. |
| Mehrere Arduinos kommunizieren mit dem Raspberry Pi | 5 | Umgesetzt | [`config.py`](../src/mobilefrost/config.py) definiert drei Sensor-Arduinos und einen Aktor. [`sensor_io.py`](../src/mobilefrost/sensor_io.py) verbindet sich über serielle Ports und liest die Sensorwerte. |
| Messdaten werden in einer SQL-Datenbank protokolliert | 4 | Umgesetzt | [`database.py`](../src/mobilefrost/database.py) erstellt `temperatures` und speichert Werte; [`controller.py`](../src/mobilefrost/controller.py) begrenzt die Speicherung pro Sensor auf zehn Sekunden. |
| Datenformate der angeschlossenen Sensoren werden dargestellt | 5 | Umgesetzt | [`sensor_io.py`](../src/mobilefrost/sensor_io.py) parst `Aktuelle Temperatur: <wert>`. Der DHT11-Sketch sendet zusätzlich `Aktuelle Luftfeuchtigkeit: <wert>`. Beispiele stehen in der [README](../README.md). |
| Luftsensor wird vom Raspberry Pi über Arduino mit Transistor gesteuert | 8 | Nicht nachgewiesen | Der DHT11 wird gelesen, aber im Repository ist keine Transistor-Schaltung oder Raspberry-Pi-Steuerung des Luftsensors dokumentiert. Der Hardwareaufbau und ein passender Steuerbefehl müssten ergänzt bzw. vorgeführt werden. |
| Ventil beziehungsweise Servomotor wird vom Raspberry Pi über Arduino gesteuert | 3 | Umgesetzt | [`controller.py`](../src/mobilefrost/controller.py) sendet `S:90` erst ab `30.0 °C` und `S:0` darunter; [`sketch_fanANDled.ino`](../sketches/sketch_fanANDled/sketch_fanANDled.ino) verarbeitet den Befehl mit der Servo-Bibliothek. |
| Das Szenario wurde sinnvoll erweitert | 5 | Umgesetzt | Erweiterungen sind SQL-Historie, Web-Dashboard, MQTT, automatische Kühlregel, LCD-Anzeige und Wiederverbindung fehlender Sensoren. |

**Zwischensumme Challenge I: 45 Punkte**

## Challenge II: Ice Truck Extension

| Anforderung | Punkte | Status | Nachweis / offene Ergänzung |
| --- | ---: | --- | --- |
| Kommunikation über MQTT ist realisiert | 8 | Umgesetzt | [`mqtt_io.py`](../src/mobilefrost/mqtt_io.py) veröffentlicht Temperatur- und Kühlstatus-Nachrichten und empfängt Lüfter- sowie Klappenbefehle. Mosquitto ist in [`compose.yml`](../compose.yml) enthalten. |
| Organisation und Hierarchie der Topics wird dargestellt | 5 | Umgesetzt | Die Topics folgen den Bereichen `mobilefrost/temperatures`, `mobilefrost/status` und `mobilefrost/actuators`. Eine vollständige Übersicht steht in der [README](../README.md). |
| Steuerung ist über Node-RED realisiert | 9 | Teilweise | Node-RED ist als Service in [`compose.yml`](../compose.yml) vorbereitet. Ein versionierter Flow oder eine konkrete Node-RED-Steuerung ist im Repository jedoch nicht enthalten und muss für die Präsentation noch eingerichtet werden. |
| Ein weiteres digitales Endgerät ist über MQTT eingebunden | 8 | Teilweise | MQTT Dash oder MQTT Explorer können die dokumentierten Topics verwenden. Eine konkrete Gerätekonfiguration oder ein Screenshot ist im Repository nicht enthalten und muss praktisch nachgewiesen werden. |
| Zusätzliche Funktionen sind realisiert | 8 | Umgesetzt | Vorhanden sind Dashboard mit Zeiträumen, PostgreSQL-Historie, retained MQTT-Werte, automatische Kühlung, Temperaturkorrektur für Luis und Wiederverbindung fehlender Sensoren. |
| Präsentation mit Überblick, rotem Faden, Teamanteilen, Visualisierung und Zeitplanung | 10 | Offen | Diese Anforderung betrifft die Durchführung des Fachgesprächs und kann nicht aus dem Quellcode bewertet werden. |
| Technische Entscheidungen werden fachlich fundiert erläutert | 7 | Offen | Für das Gespräch sollten insbesondere serielle Kommunikation, MQTT-Topic-Struktur, SQL-Speicherung, PWM/Servo-Steuerung und die automatische Kühlregel vorbereitet werden. |

**Zwischensumme Challenge II: 55 Punkte**

## Vorführung und Vorbereitung

Für eine vollständige Bewertung sollten zusätzlich praktisch vorbereitet werden:

1. Sensor-, LED-, Transistor- und Servo-Verdrahtung sichtbar aufbauen.
2. Einen Temperaturwert verändern und die Reaktion von LED, Lüfter, Servo und LCD zeigen.
3. Mehrere serielle Arduino-Verbindungen und die Datenbankeinträge demonstrieren.
4. MQTT-Nachrichten mit MQTT Explorer oder einer mobilen MQTT-App zeigen.
5. Einen Node-RED-Flow erstellen, importieren und mit dem Broker `mosquitto:1883`
   verbinden.
6. Die Teamaufgaben, Zeitplanung und technischen Entscheidungen für die Präsentation
   festlegen.