#!/usr/bin/env bash
# Publishes a test message and verifies it is received back on the same topic.
# Exits 0 on success, 1 on timeout or mismatch.
#
# Usage: ./mqtt_test_pubsub.sh [/path/to/mqtt.env] [topic] [message]

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/mqtt_common.sh" "${1:-}"

TOPIC="${2:-mqtt/bridge/test}"
PAYLOAD="${3:-ping-$(date +%s)}"
TIMEOUT=5

echo "=== MQTT Pub/Sub Round-Trip Test ==="
echo "Broker  : $MQTT_HOST:$MQTT_PORT"
echo "Topic   : $TOPIC"
echo "Payload : $PAYLOAD"
echo ""

# Subscribe in the background, write received message to a temp file
_tmpfile=$(mktemp)
trap 'rm -f "$_tmpfile"' EXIT

mosquitto_sub "${_broker_args[@]}" \
    -t "$TOPIC" -C 1 -W "$TIMEOUT" \
    > "$_tmpfile" 2>/dev/null &
_sub_pid=$!

sleep 0.3  # Give the subscriber time to connect

mosquitto_pub "${_broker_args[@]}" \
    -t "$TOPIC" -m "$PAYLOAD"

wait "$_sub_pid" 2>/dev/null
_received=$(cat "$_tmpfile")

if [[ "$_received" == "$PAYLOAD" ]]; then
    echo "PASS: received '$_received'"
else
    echo "FAIL: expected '$PAYLOAD', got '${_received:-<nothing>}'" >&2
    exit 1
fi
