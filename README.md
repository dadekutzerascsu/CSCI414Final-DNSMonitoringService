# Distributed DNS Monitoring Service

This project measures DNS A-record response time and resolver availability for
registered domains. It stores domain configuration and timestamped lookup
results in MongoDB.

The current implementation covers:

- [Module A: Network Infrastructure](docs/module-a.md): three Docker bridge
  subnets, a routed client-to-API path, and a restricted client boundary.
- [Module B: Distributed Service](docs/module-b.md): a FastAPI service, MongoDB
  schema, repeatable domain import, and DNS lookup history.

See the [installation guide](docs/installation-guide.md) to start the stack and
exercise the API. MongoDB uses local-lab credentials and is not configured for
production deployment.