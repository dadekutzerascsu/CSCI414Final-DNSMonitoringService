# Distributed DNS Monitoring Service

This project measures DNS A-record response time and resolver availability for
registered domains. It stores domain configuration and timestamped lookup
results in MongoDB.

The current implementation covers:

- [Module A: Network Infrastructure](docs/module-a.md): three Docker bridge
  subnets, a routed client-to-API path, and a restricted client boundary.
- [Module B: Distributed Service](docs/module-b.md): a FastAPI service, MongoDB
  schema, repeatable domain import, and DNS lookup history.
- [Module C: Network Security](docs/module-c.md): firewall policy, TLS-enabled
  API access, and blocked unauthorized traffic.
- [Module D: Observability](docs/module-d.md): packet capture, endpoint timing,
  and log correlation evidence.
- [Module E: Network Performance](docs/module-e.md): baseline, degraded-path,
  and measurement-based comparison of service behavior under impairment.
- [Module F: Automation and Recovery](docs/module-f.md): health validation,
  controlled failure, and scripted recovery evidence.

The experiment notes in [experiments/latency-test.md](experiments/latency-test.md),
[experiments/load-test.md](experiments/load-test.md), and
[experiments/failover-test.md](experiments/failover-test.md) provide the
repeatable test procedures for Modules E and F.

See the [installation guide](docs/installation-guide.md) to start the stack and
exercise the API. MongoDB uses local-lab credentials and is not configured for
production deployment.