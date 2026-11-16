# Module E: Network Performance

## Goal

Compare API performance under a normal network path and a controlled delay.
The test uses the Compose client for both runs so the `tc` impairment affects
the benchmark traffic.

## Setup and baseline

Run these commands from the repository root. Rebuild the client so it includes
ApacheBench (`ab`) and start the services:

```sh
docker compose -f docker/docker-compose.yml up --build -d
docker compose -f docker/docker-compose.yml exec client \
  curl -fsS http://172.28.10.1:8000/health
```

Run 100 requests with concurrency 10 from the client container. Capture the
benchmark summary as the **baseline** screenshot:

```sh
docker compose -f docker/docker-compose.yml exec -T client \
  ab -n 100 -c 10 http://172.28.10.1:8000/health
```

Record `Complete requests`, `Failed requests`, and the `mean` value in the
`Total` row under `Connection Times (ms)`. The success count is completed
requests minus failed requests; calculate the success rate as
`success count / 100 * 100%`. Take a screenshot that includes these summary
values.

## Apply delay and measure again

Add a 100 ms egress delay to the Compose client's `eth0`, confirm the qdisc is
active, then rerun the identical benchmark. Capture the qdisc and benchmark
summary as the **impaired** screenshot.

```sh
docker compose -f docker/docker-compose.yml exec client \
  tc qdisc add dev eth0 root netem delay 100ms

docker compose -f docker/docker-compose.yml exec client \
  tc qdisc show dev eth0

docker compose -f docker/docker-compose.yml exec -T client \
  ab -n 100 -c 10 http://172.28.10.1:8000/health
```

The client has `NET_ADMIN` so `tc` can configure its own interface. Run the
benchmark from that same container: a host request to `localhost:8000` does
not traverse the client's impaired interface. Remove the impairment after the
test, even if you are done collecting screenshots:

```sh
docker compose -f docker/docker-compose.yml exec client \
  tc qdisc del dev eth0 root
```

## Results

The following values were measured against the running stack in this workspace
with the commands above. Results vary by host; rerun the test and replace these
values with your own before submitting. Use the `Connection Times (ms) → Total
→ mean` field for the latency column.

| Condition | Requests (successful / 100) | Success rate | Mean latency |
| --- | ---: | ---: | ---: |
| Baseline | 100 / 100 | 100% | 11 ms |
| 100 ms netem delay | 100 / 100 | 100% | 208 ms |

Include screenshots of the baseline `ab` summary, the active `tc qdisc`, and
the impaired `ab` summary. Explain whether latency increased and whether the
service remained available. The configured 100 ms is an egress delay, not a
guaranteed measured latency; observed request times also include TCP,
application, and benchmark overhead.

## Submission checklist

- Baseline and impaired benchmark screenshots
- The `tc qdisc show dev eth0` output showing the applied impairment
- A results table populated with the measured request counts, success rates,
  and mean request times
- A brief comparison of the observed latency and availability
