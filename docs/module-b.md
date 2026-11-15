# Module B: Distributed Service

## Service and data model

The FastAPI application runs in the service segment and communicates with
MongoDB only through the data segment. Its API provides:

- `POST /domains` — register a hostname.
- `GET /domains` and `GET /domains/{domain}` — list and retrieve registrations.
- `PATCH /domains/{domain}` — enable or disable monitoring.
- `POST /domains/{domain}/checks` — perform an A-record lookup and persist the
  result.
- `GET /domains/{domain}/checks` — retrieve newest-first lookup history.
- `GET /health` — verify that the API can reach MongoDB.

Each `domains` document contains a unique normalized hostname, source, enabled
flag, and creation/update timestamps. Each `checks` document records its
hostname, UTC check time, success state, measured latency, DNS response code,
returned addresses, TTL, and error detail. An index on
`(domain, checked_at)` supports per-domain history queries.

DNS failures are stored as measurements with `success: false`; malformed
hostnames, unknown registrations, duplicate registrations, and disabled
monitoring requests return HTTP 422, 404, 409, and 409 respectively.

## Repeatable examples

Register and read a domain from the host:

```sh
curl -i -X POST http://127.0.0.1:8000/domains \
  -H 'Content-Type: application/json' \
  -d '{"domain":"example.com","source":"manual"}'
curl -i http://127.0.0.1:8000/domains/example.com
```

These requests traverse the routed client-to-service path:

```sh
docker compose -f docker/docker-compose.yml exec client \
  curl -i -X PATCH http://172.28.10.1:8000/domains/example.com \
  -H 'Content-Type: application/json' -d '{"enabled":true}'
docker compose -f docker/docker-compose.yml exec client \
  curl -i -X POST http://172.28.10.1:8000/domains/example.com/checks
docker compose -f docker/docker-compose.yml exec client \
  curl -i http://172.28.10.1:8000/domains/example.com/checks
```

To see validation and lookup errors, try a malformed hostname (HTTP 422), an
unregistered valid hostname (HTTP 404), or disable a registered hostname and
attempt a check (HTTP 409). A valid hostname whose DNS lookup fails still
creates a stored check record; inspect its `success`, `response_code`, and
`error` fields.

The sample domain `example.com` and any manually added domains are not a
substitute for the course dataset. Follow the [installation guide](installation-guide.md)
to import at least 1,000 domains from Tranco; imported records are labeled with
their source and are not queried until a check is explicitly requested.