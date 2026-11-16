# Failover and Recovery Test

## Objective

Demonstrate that service health is automatically re-validated and that the platform recovers after a controlled outage.

## Example recovery cycle

```sh
# 1. Confirm the service is healthy
curl -fsS http://127.0.0.1:8000/health

# 2. Stop the API container to simulate a service outage
docker compose -f docker/docker-compose.yml stop api

# 3. Confirm the health endpoint fails
curl -fsS http://127.0.0.1:8000/health || echo 'API is down'

# 4. Restore the service
docker compose -f docker/docker-compose.yml up -d api

# 5. Validate recovery
curl -fsS http://127.0.0.1:8000/health
```

## Scripted version

A repeatable example is stored in the project automation scripts or can be implemented as a one-off shell command. The important requirement is to keep the sequence identical across runs so the before/after evidence is fair.

## Evidence to record

- health response before the interruption
- failure message or timeout while the service is stopped
- recovery command output
- final health response after service restart

Example log:

```text
[before] {"status":"ok","database":"connected"}
[stop] docker compose stop api
[fail] curl: (7) Failed to connect
[start] docker compose up -d api
[after] {"status":"ok","database":"connected"}
```

This demonstrates both the controlled outage and a successful recovery path.
