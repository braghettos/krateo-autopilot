#!/bin/sh
set -e

# Use mounted TLS secret if available, otherwise generate self-signed
if [ -f /app/tls/tls.crt ] && [ -f /app/tls/tls.key ]; then
  CERT=/app/tls/tls.crt
  KEY=/app/tls/tls.key
else
  mkdir -p /app/certs
  CERT=/app/certs/cert.pem
  KEY=/app/certs/key.pem
  if [ ! -f "$CERT" ]; then
    openssl req -x509 -newkey rsa:2048 -nodes \
      -keyout "$KEY" -out "$CERT" \
      -days 365 -subj "/CN=krateo-voice-ui" 2>/dev/null
  fi
fi

exec uvicorn backend.server:app \
  --host 0.0.0.0 \
  --port 8080 \
  --ssl-keyfile "$KEY" \
  --ssl-certfile "$CERT"
