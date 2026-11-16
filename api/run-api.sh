#!/bin/sh
set -eu

if [ -n "${TLS_CERTFILE:-}" ] && [ -n "${TLS_KEYFILE:-}" ] && [ -f "${TLS_CERTFILE}" ] && [ -f "${TLS_KEYFILE}" ]; then
  exec uvicorn main:app --host 0.0.0.0 --port 8000 --ssl-certfile "${TLS_CERTFILE}" --ssl-keyfile "${TLS_KEYFILE}"
fi

exec uvicorn main:app --host 0.0.0.0 --port 8000
