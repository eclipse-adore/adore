#!/usr/bin/env bash
set -euo pipefail

GRPC_HOST="${GRPC_HOST:-0.0.0.0}"
GRPC_PORT="${GRPC_PORT:-50051}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PIDFILE="${TMPDIR:-/tmp}/grpc_local_server.pid"
LOGFILE="${TMPDIR:-/tmp}/grpc_local_server.log"

if [[ -f "$PIDFILE" ]] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
    echo "Local gRPC server already running (pid $(cat "$PIDFILE"))"
    exit 0
fi

python3 "$SCRIPT_DIR/grpc_server.py" --host "$GRPC_HOST" --port "$GRPC_PORT" \
    > "$LOGFILE" 2>&1 &
echo $! > "$PIDFILE"
echo "Local gRPC server started (pid $(cat "$PIDFILE")) on ${GRPC_HOST}:${GRPC_PORT}"
echo "Logs: $LOGFILE"
