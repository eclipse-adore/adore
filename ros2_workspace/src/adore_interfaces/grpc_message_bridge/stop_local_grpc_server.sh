#!/usr/bin/env bash
set -euo pipefail

PIDFILE="${TMPDIR:-/tmp}/grpc_local_server.pid"

if [[ ! -f "$PIDFILE" ]]; then
    echo "No pidfile found at $PIDFILE -- server may not be running"
    exit 0
fi

PID="$(cat "$PIDFILE")"

if kill -0 "$PID" 2>/dev/null; then
    kill "$PID"
    echo "Local gRPC server stopped (pid $PID)"
else
    echo "Process $PID not found -- already stopped"
fi

rm -f "$PIDFILE"
