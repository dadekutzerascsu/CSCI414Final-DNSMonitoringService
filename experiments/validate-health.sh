#!/usr/bin/env bash
set -u

URL="${1:-http://127.0.0.1:8000/health}"

if curl -fsS --max-time 5 "$URL"; then
  printf '\nPASS\n'
else
  printf 'FAIL\n'
  exit 1
fi
