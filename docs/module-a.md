# Module A: Network Infrastructure

## Topology

The compose stack in [`docker-compose.yml`](../docker/docker-compose.yml)
creates three independent Docker bridge segments:

| Segment | CIDR | Router | Endpoint |
| --- | --- | --- | --- |
| Client | `172.28.10.0/24` | Docker bridge gateway `172.28.10.1` | test client `172.28.10.10` |
| Service | `172.28.20.0/24` | Docker bridge gateway `172.28.20.1` | API `172.28.20.10` |
| Data | `172.28.30.0/24` | Docker bridge gateway `172.28.30.1` | API `172.28.30.10`, MongoDB `172.28.30.20` |

Docker's bridge gateway provides the routed/NAT path: port 8000 on the client
bridge gateway is forwarded to the API on the service subnet. The API has a
separate interface on the data subnet; the client has none. MongoDB is not
published to the host, so the client can reach the API but cannot connect
directly to the database.

This design uses Docker bridge routing and port forwarding, not FRRouting,
BGP, or a separately managed router container.

The [topology diagram](../network/topology.drawio) and
[subnet plan](../network/subnet-plan.md) show the addresses and forwarding
path.

## Connectivity evidence

Start the stack and run the checks in the
[installation guide](installation-guide.md):

```sh
docker compose -f docker/docker-compose.yml exec client ip route
docker compose -f docker/docker-compose.yml exec client \
  ping -c 1 -W 1 172.28.10.1
docker compose -f docker/docker-compose.yml exec client \
  traceroute -n -m 5 -w 1 172.28.10.1
docker compose -f docker/docker-compose.yml exec client \
  curl -fsS http://172.28.10.1:8000/health
docker compose -f docker/docker-compose.yml exec client \
  curl --connect-timeout 2 http://172.28.30.20:27017/
```

Expected results:

- The client default route points to `172.28.10.1`.
- The API health check succeeds over the routed client-to-service path.
- The attempted client-to-database connection fails because Docker does not
  publish MongoDB or forward direct client-subnet traffic to the data segment.
- The API-to-MongoDB connection uses the data subnet directly.

For submission evidence, record the command output, the compose network
configuration, and a topology diagram showing all three CIDRs and the Docker
bridge gateway forwarding path.