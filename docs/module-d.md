# Module D: Observability

## Goal

The final project requires packet-level and service-level evidence. Module D
captures the network flow, logs the API response path, and correlates those
observations with a user-visible effect.

## Repeatable test and screenshots

Run these commands from the repository root. Start the stack and confirm the
health endpoint responds before collecting evidence:

```sh
docker compose -f docker/docker-compose.yml up --build -d
curl -fsS http://localhost:8000/health
```

Use three host terminal windows so the capture and logs are active for the same
request:

1. In terminal 1, start a live packet capture. Leave it running while you make
   the request, then press `Ctrl+C`. Capture this terminal as the **packet
   capture** screenshot.

   ```sh
   sudo tcpdump -i any -nn -tttt 'tcp port 8000'
   ```

2. In terminal 2, run one health request and record its start time and total
   time. Capture the response and timing output as the **metrics/timing**
   screenshot.

   ```sh
   date -Is
   curl -sS -w '\ntime_total=%{time_total}s http_code=%{http_code}\n' \
     http://localhost:8000/health
   ```

3. In terminal 3, show the API's recent timestamped logs. Capture the matching
   `GET /health` access-log entry as the **application logs** screenshot.

   ```sh
   docker compose -f docker/docker-compose.yml logs --since=2m --timestamps api
   ```

   This project does not set a fixed container name, so `docker logs
   dns-monitoring-api` may not find the API container. The Compose command above
   selects the correct service.

Use the timestamps to match the TCP connection/request in the packet capture
with the `GET /health` entry in the API logs. The curl output gives the
end-to-end time for that same request; include all three screenshots and a
short explanation in the submission. For a saved capture and timing log
instead of (or in addition to) the live terminal screenshot, run:

```sh
./security/collect_observability.sh
```

## Packet capture

Run a short capture while the API responds to a health check:

```sh
./security/collect_observability.sh
```

This script records a packet capture in
`security/evidence/dns-monitor-capture.pcap` and logs HTTP timing data in
`security/evidence/http-metrics.log`.

To collect traffic manually:

```sh
mkdir -p security/evidence
sudo tcpdump -n -i any -s 0 -w security/evidence/dns-monitor-capture.pcap \
  'port 8000 or port 27017'
```

Leave the capture running while you make a health request in another terminal,
then press `Ctrl+C`. Inspect the saved capture with Wireshark or
`tcpdump -r security/evidence/dns-monitor-capture.pcap` to confirm the API port,
MongoDB port, and the client-to-service request flow.

## Log and service evidence

The API emits health and validation results in HTTP responses, while the
application process logs operational errors and database connection status.
Useful commands:

```sh
docker compose -f docker/docker-compose.yml logs --tail=50 --timestamps api

docker compose -f docker/docker-compose.yml exec api \
  python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8000/health').read().decode())"
```

A typical health response is:

```json
{"status":"ok","database":"connected"}
```

For latency evidence, use curl's timing output:

```sh
docker compose -f docker/docker-compose.yml exec client \
  curl -sS -w 'time_namelookup=%{time_namelookup} time_connect=%{time_connect} time_total=%{time_total} http_code=%{http_code}\n' \
  http://172.28.10.1:8000/health
```

## Metrics and interpretation

Capture several health checks and summarize the results in a table like:

| Check | RTT (ms) | HTTP code | Result |
| --- | ---: | ---: | --- |
| healthy path | 4.2 | 200 | service reachable |
| failed MongoDB path | timeout | n/a | blocked access |
| HTTPS health request | 5.5 | 200 | encrypted path works |

This lets the team correlate a network event (packet flow, blocked port,
handshake, or latency increase) to an application-level effect (health check
failures, HTTP errors, or slower response times).

## Submission checklist

- Packet capture showing client->API and API->MongoDB traffic
- Example curl timing output or a saved metric log
- API log sample with health or database status
- Screenshot evidence for the packet capture, application logs, and timing result
- Brief explanation correlating the same request across the capture, logs, and timing

For example: “The packet capture shows the TCP session established at the same
time the FastAPI logs recorded the health request. Curl measured the end-to-end
latency for that request, linking the observed network traffic to the
application log entry and response time.”
