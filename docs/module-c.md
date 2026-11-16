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
blocked. The reference ruleset is stored in
[`../security/nftables-dns-monitor.conf`](../security/nftables-dns-monitor.conf).

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

## TLS proof

The API supports optional HTTPS when a certificate and private key are mounted.
Generate a development certificate with:

```sh
./security/generate_tls_cert.sh
```

Then start the API with TLS enabled:

```sh
export TLS_CERTFILE="$(pwd)/security/certs/api.crt"
export TLS_KEYFILE="$(pwd)/security/certs/api.key"
docker compose -f docker/docker-compose.yml up -d --build api
```

Validate the protected connection from the client:

```sh
docker compose -f docker/docker-compose.yml exec client \
  sh -c 'curl -vk --connect-timeout 3 https://172.28.20.10:8000/health'
```

Expected result:

- The TLS handshake succeeds with a self-signed certificate.
- The API returns `{"status":"ok","database":"connected"}` over HTTPS.

## Denial test

A direct attempt to reach MongoDB from the client is expected to fail:

```sh
docker compose -f docker/docker-compose.yml exec client \
  curl --connect-timeout 2 http://172.28.30.20:27017/
```

Expected result:

- Connection timeout or refusal.
- No direct DB path is exposed from the client zone.

## Evidence package

For submission, include:

- firewall ruleset file or nft output
- successful HTTPS command output
- failed direct MongoDB connection output
- a short note explaining the allowed path and the intentional denial boundary

This shows both permitted traffic and a blocked unauthorized path.
