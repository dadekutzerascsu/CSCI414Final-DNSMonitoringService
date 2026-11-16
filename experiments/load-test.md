# Load and Throughput Test

## Purpose

Measure how the DNS monitoring platform behaves when multiple API requests are issued in sequence. This test complements the latency check by showing request pressure and service stability under load.

## Procedure

```sh
for i in $(seq 1 20); do
  curl -sS -o /dev/null -w '%{time_total} %{http_code}\n' \
    http://127.0.0.1:8000/health
  sleep 0.2
done
```

For a more explicit throughput test, repeat the workload from the client container:

```sh
docker compose -f docker/docker-compose.yml exec client \
  sh -c 'for i in $(seq 1 20); do curl -sS -o /dev/null -w "%{time_total} %{http_code}\n" http://172.28.10.1:8000/health; done'
```

## Interpretation

A consistent series of successful responses indicates healthy service throughput.
If the response time grows significantly with each request, the bottleneck may be the application, the network path, or the database. The key is to keep the workload fixed and compare before/after results from the same test setup.

## Evidence to save

- raw timing output from the repeated requests
- average or median response time
- success/failure count
- any timeout or retry behavior under increased load
