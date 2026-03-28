#!/bin/sh
set -e

CERT_DIR=/app/certs
mkdir -p "$CERT_DIR"

# Generate self-signed cert if not mounted
if [ ! -f "$CERT_DIR/cert.pem" ]; then
  openssl req -x509 -newkey rsa:2048 -nodes \
    -keyout "$CERT_DIR/key.pem" \
    -out "$CERT_DIR/cert.pem" \
    -days 365 \
    -subj "/CN=krateo-voice-ui" \
    2>/dev/null
fi

exec uvicorn backend.server:app \
  --host 0.0.0.0 \
  --port 8080 \
  --ssl-keyfile "$CERT_DIR/key.pem" \
  --ssl-certfile "$CERT_DIR/cert.pem"
