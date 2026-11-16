# Module A: Network Infrastructure

## Topology

The compose stack in [`docker-compose.yml`](../docker/docker-compose.yml)
creates three independent Docker bridge segments:

| Segment | CIDR | Docker gateway | Endpoint |
| --- | --- | --- | --- |
| Client | `172.28.10.0/24` | Docker bridge gateway `172.28.10.1` | test client `172.28.10.10` |
| Service | `172.28.20.0/24` | Docker bridge gateway `172.28.20.1` | API `172.28.20.10` |
| Data | `172.28.30.0/24` | Docker bridge gateway `172.28.30.1` | API `172.28.30.10`, MongoDB `172.28.30.20` |

The request path is **client (`172.28.10.10`) → Docker host's client-bridge
gateway address (`172.28.10.1:8000`) → Docker published-port forwarding to the
API (`172.28.20.10:8000`) → MongoDB (`172.28.30.20:27017`)**. Compose publishes
port 8000 on `172.28.10.1`; Docker forwards that connection to the API's
service-network interface. The API is also attached to the data network and
connects to MongoDB there (using the Compose service name `mongodb`). This is
Docker bridge networking and published-port forwarding, not FRRouting, BGP,
or a separate router.

The client has only a client-network interface. MongoDB is only on the data
network and has no published host port. Docker's bridge isolation therefore
prevents the client from opening a direct connection to MongoDB; the API can
reach it because the API is attached to both the service and data networks.

The [topology diagram](../network/topology.drawio) and
[subnet plan](../network/subnet-plan.md) show the addresses and forwarding
path.

## Setup and verification

Follow the [installation guide](installation-guide.md) to start the stack,
then run these checks:

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

## Results

Observed output from the commands above with Docker Compose on this host
(latency values can vary):

```text
$ docker compose -f docker/docker-compose.yml exec client ip route
default via 172.28.10.1 dev eth0
172.28.10.0/24 dev eth0 proto kernel scope link src 172.28.10.10

$ docker compose -f docker/docker-compose.yml exec client ping -c 1 -W 1 172.28.10.1
PING 172.28.10.1 (172.28.10.1) 56(84) bytes of data.
64 bytes from 172.28.10.1: icmp_seq=1 ttl=64 time=0.135 ms

1 packets transmitted, 1 received, 0% packet loss

$ docker compose -f docker/docker-compose.yml exec client traceroute -n -m 5 -w 1 172.28.10.1
traceroute to 172.28.10.1 (172.28.10.1), 5 hops max, 46 byte packets
1  172.28.10.1  0.013 ms  0.008 ms  0.007 ms

$ docker compose -f docker/docker-compose.yml exec client curl -fsS http://172.28.10.1:8000/health
{"status":"ok","database":"connected"}

$ docker compose -f docker/docker-compose.yml exec client curl --connect-timeout 2 http://172.28.30.20:27017/
curl: (28) Connection timed out after 2002 milliseconds
# Expected: this client-to-database attempt fails (curl exit status 28).
```

The route and ping/traceroute confirm that the client reaches its Docker
gateway. The health response confirms the published-port path reaches the API
and that the API can reach MongoDB. The direct database attempt times out,
consistent with the client's network boundary and MongoDB's unpublished port.

## Limitations and future improvements

The traceroute target is the client bridge gateway, so it confirms only that
gateway hop; it does not expose Docker's internal published-port forwarding
or the API-to-database hop. The observed connectivity is from this Compose
runtime and host, not a guarantee of identical routing/firewall behavior on
every Docker platform. For stronger repeatable evidence, capture the container
network attachments and Docker's published-port rules alongside these checks;
a separate router/firewall appliance would be a different topology and is not
part of this implementation.