# Module F: Automation and Recovery

## Goal

Module F demonstrates that the DNS monitoring service can be validated automatically and restored after a controlled failure. The deliverable is a repeatable automation script plus a failure/recovery demonstration showing before, during, and after health checks.

The assignment specifically calls for:

- scripted deployment or validation checks
- a controlled break in service
- automatic or documented recovery
- verification that the service is healthy again after recovery

## Automation design

Use a small shell script that checks the target service and prints a clear success or failure result. A suitable example is:

```sh
#!/usr/bin/env bash
set -euo pipefail

URL="${1:-http://127.0.0.1:8000/health}"
for attempt in $(seq 1 10); do
  if curl -fsS "$URL" >/tmp/dns-health.json 2>/dev/null; then
    echo "Health check passed on attempt $attempt"
    cat /tmp/dns-health.json
    exit 0
  fi
  sleep 2
done

echo "Health check failed after 10 attempts" >&2
exit 1
```

This script is intentionally small and reusable for a CI-style validation or a manual local check.

## Controlled failure

To demonstrate recovery, deliberately stop the API or an intermediate component, wait for the health check to fail, and then restore it:

```sh
# Stop the service briefly to simulate an outage
cd /path/to/CSCI414Final-DNSMonitoringService
docker compose -f docker/docker-compose.yml stop api

# Observe that the health check fails
curl -fsS http://127.0.0.1:8000/health || echo "API is down"

# Restore service

docker compose -f docker/docker-compose.yml up -d api
```

A more realistic automation flow is to run a script that checks health, stops the service, waits, starts it again, and verifies the endpoint returns to normal.

## Recovery script example

Create a recovery helper such as `experiments/failover-recovery.sh`:

```sh
#!/usr/bin/env bash
set -euo pipefail

COMPOSE_FILE="${COMPOSE_FILE:-docker/docker-compose.yml}"
SERVICE_NAME="${SERVICE_NAME:-api}"
URL="${URL:-http://127.0.0.1:8000/health}"

function wait_healthy() {
  for _ in $(seq 1 20); do
    if curl -fsS "$URL" >/dev/null 2>&1; then
      return 0
    fi
    sleep 2
  done
  return 1
}

printf 'Checking health before disruption...\n'
wait_healthy

printf 'Stopping %s to simulate failure...\n' "$SERVICE_NAME"
docker compose -f "$COMPOSE_FILE" stop "$SERVICE_NAME"

printf 'Verifying the service is now unavailable...\n'
if curl -fsS "$URL" >/dev/null 2>&1; then
  echo 'Service unexpectedly remained healthy' >&2
  exit 1
fi

printf 'Restarting %s...\n' "$SERVICE_NAME"
docker compose -f "$COMPOSE_FILE" up -d "$SERVICE_NAME"

printf 'Waiting for recovery...\n'
if wait_healthy; then
  echo 'Recovery confirmed: service returned to healthy state.'
else
  echo 'Recovery failed: health checks did not recover.' >&2
  exit 1
fi
```

## Evidence package

For submission, keep the output from the script and a concise log showing the sequence:

- check before failure: service healthy
- controlled stop or interruption
- failing health check during outage
- recovery command
- final health check after restart

Example evidence:

```text
[before] Health check passed: {"status":"ok","database":"connected"}
[fail] Stopping api container...
[fail] curl http://127.0.0.1:8000/health -> connection refused
[recover] Starting api container...
[after] Health check passed: {"status":"ok","database":"connected"}
```

## Submission checklist

- Health-check script or equivalent validation automation
- Failure demonstration (service or link outage)
- Recovery command or script
- Before/after evidence showing service availability returned to normal

This module proves the platform is not only present but resilient under a controlled disruption.
