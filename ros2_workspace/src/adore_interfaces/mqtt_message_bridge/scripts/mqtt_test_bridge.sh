#!/usr/bin/env bash
# Round-trips every mqtt_topic declared in a bridge_config.yaml through the broker.
# This proves reachability and ACL grants for the configured topics; it does not
# require the bridge node to be running.
#
# Usage: ./mqtt_test_bridge.sh [/path/to/broker_config.yaml] [/path/to/bridge_config.yaml]

set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/mqtt_common.sh" "${1:-}"

CONFIG="${2:-${1:-$(dirname "$SCRIPT_DIR")/config/bridge_config.yaml}}"
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

# A subscription filter cannot be published to, so '+' and '#' are replaced with
# a concrete segment that still matches the filter.
_concrete_topic() {
    local topic="${1//+/probe}"
    if [[ "$topic" == "#" ]]; then
        echo probe
    elif [[ "$topic" == */# ]]; then
        echo "${topic%/#}/probe"
    else
        echo "$topic"
    fi
}

_test_topic() {
    local direction="$1"
    local filter="$2"
    local topic
    topic="$(_concrete_topic "$filter")"
    local payload="test-$(date +%s%N)"
    local tmpfile
    tmpfile=$(mktemp)

    mosquitto_sub "${_broker_args[@]}" -t "$filter" -C 1 -W "$TIMEOUT" \
        > "$tmpfile" 2>/dev/null &
    local sub_pid=$!
    sleep 0.3

    mosquitto_pub "${_broker_args[@]}" -t "$topic" -m "$payload" 2>/dev/null

    if wait "$sub_pid" 2>/dev/null && [[ "$(cat "$tmpfile")" == "$payload" ]]; then
        echo "  PASS [$direction] $filter"
        (( PASS++ ))
    else
        echo "  FAIL [$direction] $filter (published to $topic)" >&2
        (( FAIL++ ))
    fi
    rm -f "$tmpfile"
}

_extract_mqtt_topics() {
    awk -v section="$1" '
        $0 ~ "^" section ":" { in_section = 1; next }
        /^[^[:space:]#]/     { in_section = 0 }
        in_section && /mqtt_topic:/ {
            sub(/^.*mqtt_topic:[[:space:]]*/, "")
            sub(/[[:space:]]*#.*$/, "")
            gsub(/^["\047]|["\047]$/, "")
            sub(/[[:space:]]+$/, "")
            if (length($0)) print
        }
    ' "$CONFIG"
}

for section in ros2_to_mqtt mqtt_to_ros2; do
    echo "--- $section topics ---"
    found=0
    while IFS= read -r topic; do
        [[ -z "$topic" ]] && continue
        found=1
        _test_topic "$section" "$topic"
    done < <(_extract_mqtt_topics "$section")
    [[ "$found" -eq 0 ]] && echo "  (none declared)"
    echo ""
done

echo "Results: $PASS passed, $FAIL failed"
[[ $FAIL -eq 0 ]]
