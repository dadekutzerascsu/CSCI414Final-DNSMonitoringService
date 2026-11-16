# Module E: Network Performance

## Goal

The DNS monitoring platform must prove that it works in both normal and degraded network conditions. Module E compares a healthy baseline against a constrained network and shows how the service behaves when latency, loss, or bandwidth limits are introduced.

The required evidence is a before/after measurement table and a short explanation of whether the bottleneck is in the network path or in the application itself.

## Baseline measurement

Start from the normal stack and confirm the API is reachable:

```sh
docker compose -f docker/docker-compose.yml up --build -d
curl -sS -w 'time_namelookup=%{time_namelookup} time_connect=%{time_connect} time_total=%{time_total} http_code=%{http_code}\n' \
  http://127.0.0.1:8000/health
```

Capture 10–20 healthy requests and record the median RTT, total request time, and HTTP success rate. The same client-to-API path should be used for every run so the comparison stays fair.

## Introduce a controlled impairment

Use `tc/netem` to add delay and loss between the client and API path. On the host, or inside the client container when `tc` is available, apply a small impairment such as:

```sh
docker compose -f docker/docker-compose.yml exec client sh -c '
  tc qdisc add dev eth0 root netem delay 100ms loss 2% rate 5mbit
'
```

Then rerun the same check repeatedly:

```sh
docker compose -f docker/docker-compose.yml exec client \
  sh -c 'for i in $(seq 1 10); do curl -sS -w "time_total=%{time_total} http_code=%{http_code}\n" http://172.28.10.1:8000/health; done'
```

When the test is complete, remove the impairment:

```sh
docker compose -f docker/docker-compose.yml exec client sh -c 'tc qdisc del dev eth0 root || true'
```

## Evidence to collect

Record the following for each run:

- HTTP status code
- total request time (`time_total`)
- connect time and DNS lookup time
- number of successful requests out of the total attempts
- observed error or timeout behavior when a threshold is crossed

Example table:

| Condition | Requests | Median RTT | Success rate | Notes |
| --- | ---: | ---: | ---: | --- |
| Healthy baseline | 20 | 5 ms | 100% | Normal API path |
| 100 ms delay + 2% loss | 20 | 116 ms | 95% | Slower but still available |
| Severe loss / bandwidth cap | 20 | 650 ms+ | <100% | Queueing and retries visible |

## Interpretation

A healthy baseline should show low and stable end-to-end latency. After applying `tc/netem`, the same workload should slow down measurably but remain functionally correct unless the impairment exceeds the service or network tolerance. The main goal is to show that increased network delay or packet loss caused the observed slowdown, not that the application logic failed by itself.

For a submission packet, include:

- the exact curl timing output for the baseline and degraded tests
- the `tc` command used to create the impairment
- a short comparison table explaining the change in latency and availability
- a note distinguishing network delay from API processing time

## Submission checklist

- Baseline health-check timing output
- Degraded-path timing output
- `tc/netem` rules or equivalent impairment command
- Short explanation of the bottleneck source and the measured effect
