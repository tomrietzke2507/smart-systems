FROM python:3.9-slim

# Installiere C-Compiler und Bibliotheken für psycopg2 (PostgreSQL)
RUN apt-get update && apt-get install -y gcc python3-dev libpq-dev && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml ./
COPY src ./src

# Installiere die Anwendung und ihre Abhängigkeiten
RUN pip install --no-cache-dir .

# Deaktiviere den Python-Puffer (-u), damit Logs sofort sichtbar sind
CMD ["python", "-u", "-m", "mobilefrost"]