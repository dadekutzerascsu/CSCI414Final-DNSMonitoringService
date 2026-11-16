# Module D: Observability

## Goal

The final project requires packet-level and service-level evidence. Module D
captures the network flow, logs the API response path, and correlates those
observations with a user-visible effect.

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
docker compose -f docker/docker-compose.yml exec api \
  tcpdump -n -i any -s 0 -w /tmp/dns-monitor-capture.pcap \
  'port 8000 or port 27017' &

docker compose -f docker/docker-compose.yml exec client \
  curl -sS -w 'time_connect=%{time_connect} time_total=%{time_total}\n' \
  http://172.28.10.1:8000/health

# Stop the capture after the request completes
pkill -f 'tcpdump.*dns-monitor-capture'
```

Then inspect the capture with Wireshark or `tcpdump -r` to confirm the API port,
MongoDB port, and the client-to-service request flow.

## Log and service evidence

The API emits health and validation results in HTTP responses, while the
application process logs operational errors and database connection status.
Useful commands:

```sh
docker compose -f docker/docker-compose.yml logs --tail=50 api

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
- Brief explanation of how the network flow caused the observed service result

The key idea is to show not just that the service works, but that the traffic,
logs, and latency measurements all describe the same end-to-end transaction.
