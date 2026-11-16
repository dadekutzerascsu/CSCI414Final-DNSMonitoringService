#!/bin/sh
set -eu

OUTPUT_DIR="${1:-$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)/evidence}"
mkdir -p "$OUTPUT_DIR"

if ! command -v tcpdump >/dev/null 2>&1; then
  echo "tcpdump is required for packet capture. Install it on the host or run this script on the Docker host." >&2
  exit 1
fi

CAPTURE_PATH="$OUTPUT_DIR/dns-monitor-capture.pcap"
LOG_PATH="$OUTPUT_DIR/http-metrics.log"

rm -f "$CAPTURE_PATH" "$LOG_PATH"

tcpdump -n -i any -s 0 -w "$CAPTURE_PATH" 'port 8000 or port 27017 or port 443' &
CAPTURE_PID=$!

sleep 2

curl -sS -w '\nDNS_MONITOR_STATUS time_namelookup=%{time_namelookup} time_connect=%{time_connect} time_total=%{time_total} http_code=%{http_code}\n' \
  http://127.0.0.1:8000/health > "$LOG_PATH"

sleep 2
kill "$CAPTURE_PID" || true
wait "$CAPTURE_PID" 2>/dev/null || true

echo "Packet capture written to $CAPTURE_PATH"
echo "HTTP timing log written to $LOG_PATH"
