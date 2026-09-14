FROM python:3.9-slim

# Installiere C-Compiler und Bibliotheken für psycopg2 (PostgreSQL)
RUN apt-get update && apt-get install -y gcc python3-dev libpq-dev && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY app.py .

# Installiere pyserial für USB und psycopg2 für die Datenbank
RUN pip install pyserial psycopg2-binary

# Deaktiviere den Python-Puffer (-u), damit Logs sofort in Podman sichtbar sind
CMD ["python", "-u", "app.py"]