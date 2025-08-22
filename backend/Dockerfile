# backend/Dockerfile
FROM mcr.microsoft.com/devcontainers/python:3.10

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ACCEPT_EULA=Y \
    DEBIAN_FRONTEND=noninteractive

# Dependențe pentru pyodbc + ODBC 18 (Debian bookworm)
RUN apt-get update && apt-get install -y --no-install-recommends \
      curl gnupg apt-transport-https ca-certificates build-essential unixodbc-dev \
  && curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > /usr/share/keyrings/ms.gpg \
  && echo "deb [signed-by=/usr/share/keyrings/ms.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" > /etc/apt/sources.list.d/mssql-release.list \
  && apt-get update && apt-get install -y msodbcsql18 \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p /app/chroma_store

EXPOSE 8000
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000","--workers","4"]
