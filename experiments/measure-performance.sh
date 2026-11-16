#!/usr/bin/env bash
set -euo pipefail

URL="${URL:-http://127.0.0.1:8000/health}"
RUNS="${RUNS:-10}"

echo "Running ${RUNS} health checks against ${URL}"
for i in $(seq 1 "$RUNS"); do
  curl -sS -o /dev/null -w "request=$i time_total=%{time_total} http_code=%{http_code}\n" "$URL" || {
    echo "request ${i}: failed" >&2
    exit 1
  }
done
