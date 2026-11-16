# Latency Test

## Objective

Measure the DNS monitoring service under a healthy network baseline and then compare it to a degraded network condition.

## Baseline run

```sh
docker compose -f docker/docker-compose.yml up --build -d
for i in $(seq 1 10); do
  curl -sS -w 'time_namelookup=%{time_namelookup} time_connect=%{time_connect} time_total=%{time_total} http_code=%{http_code}\n' \
    http://127.0.0.1:8000/health
  sleep 1
done
```

Expected result: the service returns `200` and the total request time remains low and stable.

## Degraded run

```sh
docker compose -f docker/docker-compose.yml exec client sh -c '
  tc qdisc add dev eth0 root netem delay 100ms loss 2% rate 5mbit
'
for i in $(seq 1 10); do
  curl -sS -w 'time_namelookup=%{time_namelookup} time_connect=%{time_connect} time_total=%{time_total} http_code=%{http_code}\n' \
    http://172.28.10.1:8000/health
  sleep 1
done

docker compose -f docker/docker-compose.yml exec client sh -c 'tc qdisc del dev eth0 root || true'
```

## Sample result table

| Condition | Requests | Median time_total | HTTP code | Result |
| --- | ---: | ---: | ---: | --- |
| Healthy | 10 | 5–10 ms | 200 | Normal response |
| Delayed / lossy | 10 | 110–140 ms | 200 | Slower but available |

The relevant evidence is the before/after timing difference; do not rely on a single request alone.
