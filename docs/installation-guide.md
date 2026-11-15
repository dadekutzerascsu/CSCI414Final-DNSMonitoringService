# Installation and Quick Start

## Requirements

- Docker Engine with Docker Compose V2 (`docker compose`)
- A Tranco domain-list CSV downloaded from [tranco-list.eu](https://tranco-list.eu/)

The Tranco list is used as input data; the project does not download it or send
DNS queries automatically. Respect the source's terms and your resolver's
acceptable-use policy.

## Start the services

From the repository root:

```sh
mkdir -p data
# Download a Tranco list from the source site and extract its CSV to:
# data/top-1m.csv
docker compose -f docker/docker-compose.yml up --build -d
```

The compose stack creates three routed subnets:

| Segment | Subnet | Attached services |
| --- | --- | --- |
| Client | `172.28.10.0/24` | test client, Docker bridge gateway |
| Service | `172.28.20.0/24` | API |
| Data | `172.28.30.0/24` | API, MongoDB |

Docker's client bridge gateway (`172.28.10.1`) forwards TCP port 8000 to the
API in the separate service subnet. The API is also published on host loopback
for local development. MongoDB has no published host port and the client is
not attached to the data subnet.

## Import the domain list

After placing the CSV at `data/top-1m.csv`, import the first 1,000 valid rows:

```sh
docker compose -f docker/docker-compose.yml exec api \
  python import_domains.py /data/top-1m.csv --limit 1000
```

The importer accepts a Tranco `rank,domain` CSV or one hostname per row. It
stores the source as `Tranco` and is safe to rerun: existing domains are not
overwritten.

## Verify the routed path

```sh
docker compose -f docker/docker-compose.yml exec client ip route
docker compose -f docker/docker-compose.yml exec client \
  ping -c 1 -W 1 172.28.10.1
docker compose -f docker/docker-compose.yml exec client \
  traceroute -n -m 5 -w 1 172.28.10.1
docker compose -f docker/docker-compose.yml exec client \
  curl -fsS http://172.28.10.1:8000/health
```

The client route should use the bridge gateway `172.28.10.1`; the final
command should return `{"status":"ok","database":"connected"}`. Confirm that
the client cannot connect directly to MongoDB:

```sh
docker compose -f docker/docker-compose.yml exec client \
  curl --connect-timeout 2 http://172.28.30.20:27017/
```

That request is expected to fail. The API container accesses MongoDB over the
separate data subnet.

## Stop the services

```sh
docker compose -f docker/docker-compose.yml down
```

Add `-v` only when intentionally deleting the persisted MongoDB data.