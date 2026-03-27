# Dockerfile for GoodWe Standalone Server
FROM python:3.13-slim

WORKDIR /app

# Install gcc for building crc16
RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

# Example environment variable configuration (override with docker run -e ...)
ENV PORT=8080
ENV MQTT_BROKER=localhost
ENV MQTT_PORT=1883
ENV MQTT_CLIENT_ID=GoodWe
ENV MQTT_KEEPALIVE=60
# ENV MQTT_USERNAME=youruser
# ENV MQTT_PASSWORD=yourpass

CMD ["python", "acceptor.py"]
