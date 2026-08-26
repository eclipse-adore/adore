#!/usr/bin/env bash
# Spawns a grpc_subscribe.py listener then a grpc_publish.py sender and verifies
# at least one message is received. Exits 0 on success, 1 on timeout or error.
#
# Usage: ./grpc_test_pubsub.sh [/path/to/grpc.env] [topic] [timeout_seconds]

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACKAGE_DIR="$(dirname "$SCRIPT_DIR")"
source "$SCRIPT_DIR/grpc_common.sh" "${1:-}"

TOPIC="${2:-/grpc_chatter}"
TIMEOUT="${3:-8}"

echo "=== gRPC Pub/Sub Round-Trip Test ==="
echo "Server  : $GRPC_ADDRESS"
echo "Topic   : $TOPIC"
echo "Timeout : ${TIMEOUT}s"
echo ""

_tmpfile=$(mktemp)
trap 'rm -f "$_tmpfile"; kill "$_sub_pid" 2>/dev/null || true' EXIT

GRPC_HOST="$GRPC_HOST" GRPC_PORT="$GRPC_PORT" \
    python3 "$PACKAGE_DIR/grpc_subscribe.py" --address "$GRPC_ADDRESS" --topic "$TOPIC" --count 1 \
    > "$_tmpfile" 2>&1 &
_sub_pid=$!

sleep 0.5

GRPC_HOST="$GRPC_HOST" GRPC_PORT="$GRPC_PORT" \
    python3 "$PACKAGE_DIR/grpc_publish.py" --address "$GRPC_ADDRESS" --topic "$TOPIC" --count 1 \
    >> "$_tmpfile" 2>&1 &
_pub_pid=$!

_deadline=$(( SECONDS + TIMEOUT ))
while kill -0 "$_sub_pid" 2>/dev/null; do
    if (( SECONDS >= _deadline )); then
        echo "FAIL: timed out after ${TIMEOUT}s" >&2
        cat "$_tmpfile" >&2
        exit 1
    fi
    sleep 0.2
done

wait "$_sub_pid" 2>/dev/null
kill "$_pub_pid" 2>/dev/null || true

if grep -q "seq=" "$_tmpfile"; then
    echo "PASS: message received"
    grep "seq=" "$_tmpfile"
else
    echo "FAIL: no message received" >&2
    cat "$_tmpfile" >&2
    exit 1
fi
