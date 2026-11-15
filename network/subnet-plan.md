# Network Subnet Plan

The Compose file creates three Docker bridge networks. Docker assigns `.1` as
the gateway for each subnet.

| Zone | Subnet | Gateway | Static addresses |
| --- | --- | --- | --- |
| Client | `172.28.10.0/24` | `172.28.10.1` | test client `172.28.10.10` |
| Service | `172.28.20.0/24` | `172.28.20.1` | API `172.28.20.10` |
| Data | `172.28.30.0/24` | `172.28.30.1` | API `172.28.30.10`, MongoDB `172.28.30.20` |

The Docker host forwards TCP port 8000 on the client bridge gateway to the
API's service-subnet address. The API is dual-homed so it can reach MongoDB
over the data subnet. The client is only attached to the client subnet, and
MongoDB has no published host port.

Verify the networks and attached services with:

```sh
docker inspect "$(docker compose -f docker/docker-compose.yml ps -q api)" \
  --format '{{json .NetworkSettings.Networks}}'
docker compose -f docker/docker-compose.yml exec client ip route
docker compose -f docker/docker-compose.yml exec client \
  curl -fsS http://172.28.10.1:8000/health
```

The network list is also directly available in
[`docker-compose.yml`](../docker/docker-compose.yml); the related connectivity
checks are documented in [`module-a.md`](../docs/module-a.md).