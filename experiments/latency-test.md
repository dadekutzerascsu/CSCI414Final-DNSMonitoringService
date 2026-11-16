# Latency Test

Use the [Module E performance procedure](../docs/module-e.md) for a repeatable
100-request baseline and delayed run, including the correct Compose client
network path, `tc` setup and cleanup, results table, and screenshot checklist.

Run both benchmarks from the Compose `client` container. Applying `tc` to the
client's `eth0` does not affect a benchmark run from the host against
`localhost:8000`.
