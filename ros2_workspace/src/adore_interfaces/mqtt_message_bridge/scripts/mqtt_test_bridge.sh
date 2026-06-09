#!/usr/bin/env bash
# Exercises the bridge topic mappings defined in a bridge_config.yaml.
# For each ros2_to_mqtt mapping: publishes on the MQTT topic and listens for it.
# For each mqtt_to_ros2 mapping: same in the other direction.
#
# Usage: ./mqtt_test_bridge.sh [/path/to/mqtt.env] [/path/to/bridge_config.yaml]

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/mqtt_common.sh" "${1:-}"

CONFIG="${2:-$(dirname "$SCRIPT_DIR")/config/bridge_config.yaml}"
TIMEOUT=5
PASS=0
FAIL=0

if [[ ! -f "$CONFIG" ]]; then
    echo "ERROR: bridge config not found: $CONFIG" >&2
    exit 1
fi

echo "=== MQTT Bridge Topic Test ==="
echo "Broker : $MQTT_HOST:$MQTT_PORT"
echo "Config : $CONFIG"
echo ""

_test_topic() {
    local direction="$1"
    local topic="$2"
    local payload="test-$(date +%s%N)"
    local tmpfile
    tmpfile=$(mktemp)

    mosquitto_sub "${_broker_args[@]}" -t "$topic" -C 1 -W "$TIMEOUT" \
        > "$tmpfile" 2>/dev/null &
    local sub_pid=$!
    sleep 0.3

    mosquitto_pub "${_broker_args[@]}" -t "$topic" -m "$payload"

    if wait "$sub_pid" 2>/dev/null && [[ "$(cat "$tmpfile")" == "$payload" ]]; then
        echo "  PASS [$direction] $topic"
        (( PASS++ )) || true
    else
        echo "  FAIL [$direction] $topic" >&2
        (( FAIL++ )) || true
    fi
    rm -f "$tmpfile"
}

# Parse YAML with awk - extract mqtt_topic values from each section
_extract_mqtt_topics() {
    local section="$1"
    awk "
        /^${section}:/ { in_section=1; next }
        /^[a-z]/ && !/^${section}:/ { in_section=0 }
        in_section && /mqtt_topic:/ { gsub(/.*mqtt_topic:[[:space:]]*\"|\"/, \"\"); print }
    " "$CONFIG"
}

echo "--- ros2_to_mqtt topics ---"
while IFS= read -r topic; do
    [[ -z "$topic" ]] && continue
    _test_topic "ros2->mqtt" "$topic"
done < <(_extract_mqtt_topics "ros2_to_mqtt")

echo ""
echo "--- mqtt_to_ros2 topics ---"
while IFS= read -r topic; do
    [[ -z "$topic" ]] && continue
    _test_topic "mqtt->ros2" "$topic"
done < <(_extract_mqtt_topics "mqtt_to_ros2")

echo ""
echo "Results: $PASS passed, $FAIL failed"
[[ $FAIL -eq 0 ]]
