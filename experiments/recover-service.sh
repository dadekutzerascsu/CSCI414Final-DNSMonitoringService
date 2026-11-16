#!/usr/bin/env bash
set -euo pipefail

COMPOSE_FILE="${COMPOSE_FILE:-docker/docker-compose.yml}"
SERVICE_NAME="${SERVICE_NAME:-api}"
URL="${URL:-http://127.0.0.1:8000/health}"

wait_healthy() {
  for _ in $(seq 1 20); do
    if curl -fsS "$URL" >/dev/null 2>&1; then
      return 0
    fi
    sleep 2
  done
  return 1
}

printf 'Checking service health before failure...\n'
wait_healthy

printf 'Stopping %s to simulate failure...\n' "$SERVICE_NAME"
docker compose -f "$COMPOSE_FILE" stop "$SERVICE_NAME"

printf 'Verifying outage...\n'
if curl -fsS "$URL" >/dev/null 2>&1; then
  echo 'Service unexpectedly remained healthy' >&2
  exit 1
fi

printf 'Starting %s again...\n' "$SERVICE_NAME"
docker compose -f "$COMPOSE_FILE" up -d "$SERVICE_NAME"

printf 'Waiting for recovery...\n'
if wait_healthy; then
  echo 'Recovery confirmed.'
  curl -fsS "$URL"
else
  echo 'Recovery failed: service did not return to a healthy state.' >&2
  exit 1
fi
