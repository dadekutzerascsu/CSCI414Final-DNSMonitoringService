# Module F: Automation and Recovery

## Goal

Demonstrate automated health validation, a controlled API outage, and a
successful recovery. Capture separate **before**, **during failure**, and
**after recovery** screenshots showing the health-check result.

## Start the services and validate health

Run these commands from the repository root:

```sh
docker compose -f docker/docker-compose.yml up --build -d
bash experiments/validate-health.sh
```

The [health validation script](../experiments/validate-health.sh) requests
`/health`, prints the JSON response and `PASS` when healthy, and prints `FAIL`
with a nonzero exit status when the request fails.

Capture a screenshot of the command and `PASS` output as the **before**
evidence. The expected response includes
`{"status":"ok","database":"connected"}`.

## Cause a controlled failure

Stop only the API service; leave MongoDB running. Then run the validation script
again as a separate command:

```sh
docker compose -f docker/docker-compose.yml stop api
bash experiments/validate-health.sh
```

The second command should print `FAIL` because the API is unavailable. Capture
the stop and failed health-check output as the **during failure** screenshot.
The failed check is expected for this test.

## Recover and verify

Start the same Compose service, wait for the API to respond, and run the health
check again:

```sh
docker compose -f docker/docker-compose.yml start api
for attempt in $(seq 1 20); do
  if curl -fsS --max-time 2 http://127.0.0.1:8000/health >/dev/null 2>&1; then
    break
  fi
  sleep 1
done
bash experiments/validate-health.sh
```

Capture the final `PASS` and healthy JSON response as the **after recovery**
screenshot. This repository does not assign a fixed container name, so use
`docker compose ... stop api` and `start api` rather than `docker stop
dns-monitoring-api`.

## Automated recovery run

For a single-command demonstration of the whole cycle, run:

```sh
bash experiments/recover-service.sh
```

The script checks health, stops and verifies the outage, restarts the API, and
waits for health to return. Use the manual steps above when separate
before/during/after screenshots are required.

## Submission evidence

- **Before:** validation output with the health JSON and `PASS`
- **During:** failed validation and `FAIL` after stopping the API
- **After:** health JSON and `PASS` after restarting the API
- The validation script or the scripted recovery run output

This sequence confirms that the service was healthy, failed during the
controlled interruption, and returned to a healthy state after recovery.
