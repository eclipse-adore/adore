#!/usr/bin/env bash
# Checks broker reachability, reports server info, and lists active subscriptions.
#
# Usage: ./mqtt_check_broker.sh [/path/to/mqtt.env]

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/mqtt_common.sh" "${1:-}"

echo "=== MQTT Broker Check ==="
echo "Host : $MQTT_HOST"
echo "Port : $MQTT_PORT"
echo "User : ${MQTT_USERNAME:-<none>}"
echo ""

# TCP reachability
if ! nc -z -w3 "$MQTT_HOST" "$MQTT_PORT" 2>/dev/null; then
    echo "FAIL: Cannot reach $MQTT_HOST:$MQTT_PORT" >&2
    exit 1
fi
echo "TCP connection: OK"
echo ""

# Broker info via $SYS topics (available on mosquitto and most brokers)
echo "=== Broker Info (sampling \$SYS for 3s) ==="
mosquitto_sub "${_broker_args[@]}" \
    -t '$SYS/broker/version' \
    -t '$SYS/broker/uptime' \
    -t '$SYS/broker/clients/connected' \
    -t '$SYS/broker/messages/received' \
    -t '$SYS/broker/messages/sent' \
    -t '$SYS/broker/subscriptions/count' \
    -W 3 -v 2>/dev/null || true

echo ""
echo "=== Active Subscriptions (sampling \$SYS for 3s) ==="
mosquitto_sub "${_broker_args[@]}" \
    -t '$SYS/#' \
    -W 3 -v 2>/dev/null \
  | grep -i 'subscri' || echo "(none reported)"
