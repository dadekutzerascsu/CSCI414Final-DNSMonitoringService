#!/bin/sh
set -eu

CERT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)/certs"
mkdir -p "$CERT_DIR"

openssl req -x509 -nodes -newkey rsa:2048 -sha256 -days 365 \
  -subj "/CN=api.local/O=DNS Monitoring Service" \
  -keyout "$CERT_DIR/api.key" \
  -out "$CERT_DIR/api.crt"

chmod 600 "$CERT_DIR/api.key"
chmod 644 "$CERT_DIR/api.crt"

echo "Generated TLS certificate at $CERT_DIR/api.crt"
echo "Generated TLS key at $CERT_DIR/api.key"
