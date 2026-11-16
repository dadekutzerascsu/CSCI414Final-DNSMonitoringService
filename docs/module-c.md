# Module C: Network Security

## Goal

The DNS monitoring platform is intentionally segmented into three routed
subnets: client, service, and data. Module C extends the network boundary by
showing the permitted path and a denied path enforced with packet-filter rules.
The required evidence is a working allowed connection, a rejected unauthorized
connection, and a copy of the firewall ruleset.

## Access control design

The service path must remain open only through the API on port 8000 and the
API-to-database path on MongoDB port 27017. Direct client-to-database traffic is
blocked by the Compose network segmentation: the client is attached only to
the client network, while MongoDB is attached only to the data network. The
reference nftables ruleset is stored in
[`../security/nftables-dns-monitor.conf`](../security/nftables-dns-monitor.conf).
Compose does not automatically load this nftables file; do not describe it as
an active host firewall unless you separately apply and verify it.

A minimal iptables/nftables policy is:

```sh
# Example: authorize API requests from the client subnet and block DB access
# from the client network while preserving the API-to-database path
nft -f security/nftables-dns-monitor.conf
```

The rules allow:

- Client subnet -> API subnet on TCP/8000
- Service subnet -> Data subnet on TCP/27017
- Established return traffic for both flows

The rules explicitly deny:

- Client subnet -> Data subnet on TCP/27017
- Client subnet -> Data subnet on UDP/27017

## Installation and verification

From the repository root, start the services and confirm they are running:

```sh
docker compose -f docker/docker-compose.yml up --build -d
docker compose -f docker/docker-compose.yml ps
```

### Screenshot 1: allowed API traffic

The host-published API health endpoint is the simplest installation check:

```sh
curl -i http://127.0.0.1:8000/health
```

This project returns HTTP 200 and `{"status":"ok","database":"connected"}` (not
`{"status":"healthy"}`). To show the intended client-network path rather than
the host-published port, run:

```sh
docker compose -f docker/docker-compose.yml exec client \
  curl -i http://172.28.10.1:8000/health
```

Capture the command and its successful response in a terminal screenshot.

### Screenshot 2: denied database traffic

From the host, MongoDB has no published port. If `nc` is installed, capture:

```sh
nc -vz 127.0.0.1 27017
```

Expected: `Connection refused`. This proves that a host connection to that port
is unavailable; it does not by itself prove client-subnet filtering. For the
network-boundary test, run this from the isolated client container:

```sh
docker compose -f docker/docker-compose.yml exec client \
  curl --connect-timeout 2 http://172.28.30.20:27017/
```

Expected: a timeout or connection failure (curl exits non-zero). This is
expected evidence of the denied direct client-to-database path. MongoDB should
still report healthy in `docker compose ... ps`, and the API health check above
should still succeed.

### Firewall/security-rule evidence

Include the nftables ruleset file, or capture the active rules with
`sudo nft list ruleset` if the ruleset has been applied in a dedicated lab
environment. The supplied file starts with `flush ruleset`; applying it replaces
the host's existing nftables rules, so do not run it on a machine whose firewall
you need to preserve. Compose network separation is active for this lab
independently of that optional host ruleset.

## TLS proof

The API supports optional HTTPS when a certificate and private key are mounted.
Generate a development certificate with:

```sh
./security/generate_tls_cert.sh
```

Then start the API with TLS enabled:

```sh
export TLS_CERTFILE=/run/secrets/api.crt
export TLS_KEYFILE=/run/secrets/api.key
docker compose -f docker/docker-compose.yml up -d --build --force-recreate api
```

Validate the protected connection from the client:

```sh
docker compose -f docker/docker-compose.yml exec client \
  sh -c 'curl -kvi --connect-timeout 3 https://172.28.10.1:8000/health'
```

Expected result:

- The TLS handshake succeeds with a self-signed certificate.
- The API returns `{"status":"ok","database":"connected"}` over HTTPS. `-k`
  skips certificate trust validation for this development certificate; it does
  not disable TLS encryption.

After the TLS test, unset the variables and recreate the API to restore HTTP:

```sh
unset TLS_CERTFILE TLS_KEYFILE
docker compose -f docker/docker-compose.yml up -d --force-recreate api
```

## Evidence package

For submission, include:

- Screenshot of the successful API health response (HTTP or optional HTTPS)
- Screenshot of the failed direct MongoDB attempt
- nftables ruleset file or active `nft list ruleset` output, clearly indicating
  whether those host rules are actually applied
- a short note explaining the allowed path and the intentional denial boundary

This shows both permitted traffic and a blocked unauthorized path.
