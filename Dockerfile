# Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Copia il file requirements.txt e installa le dipendenze
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia il codice sorgente
COPY src/ ./src/

# Espone la porta di Streamlit (8501)
EXPOSE 8501

# Avvia la dashboard sicura
CMD ["streamlit", "run", "src/dashboard_secure.py", "--server.port=8501", "--server.enableCORS=false"]
