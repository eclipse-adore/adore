#!/usr/bin/env bash
# Exercises the bridge topic mappings defined in bridge_config.yaml.
# For each ros2_to_grpc and grpc_to_ros2 mapping: verifies the gRPC server
# accepts a publish stream on that topic without error.
#
# Usage: ./grpc_test_bridge.sh [/path/to/grpc.env] [/path/to/bridge_config.yaml]

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACKAGE_DIR="$(dirname "$SCRIPT_DIR")"
source "$SCRIPT_DIR/grpc_common.sh" "${1:-}"

CONFIG="${2:-$PACKAGE_DIR/config/bridge_config.yaml}"
TIMEOUT=5
PASS=0
FAIL=0

if [[ ! -f "$CONFIG" ]]; then
    echo "ERROR: bridge config not found: $CONFIG" >&2
    exit 1
fi

echo "=== gRPC Bridge Topic Test ==="
echo "Server : $GRPC_ADDRESS"
echo "Config : $CONFIG"
echo ""

_extract_topics() {
    local section="$1"
    awk "
        /^${section}:/ { in_section=1; next }
        /^[a-z]/ && !/^${section}:/ { in_section=0 }
        in_section && /ros_topic:/ { gsub(/.*ros_topic:[[:space:]]*\"?|\"?[[:space:]]*$/, \"\"); print }
    " "$CONFIG"
}

_test_topic() {
    local direction="$1"
    local topic="$2"
    local _tmpfile
    _tmpfile=$(mktemp)

    python3 "$PACKAGE_DIR/grpc_publish.py" \
        --address "$GRPC_ADDRESS" --topic "$topic" --count 1 \
        > "$_tmpfile" 2>&1
    local rc=$?

    if [[ $rc -eq 0 ]] && grep -q "Published" "$_tmpfile"; then
        echo "  PASS [$direction] $topic"
        (( PASS++ )) || true
    else
        echo "  FAIL [$direction] $topic" >&2
        cat "$_tmpfile" >&2
        (( FAIL++ )) || true
    fi
    rm -f "$_tmpfile"
}

echo "--- ros2_to_grpc topics ---"
while IFS= read -r topic; do
    [[ -z "$topic" ]] && continue
    _test_topic "ros2->grpc" "$topic"
done < <(_extract_topics "ros2_to_grpc")

echo ""
echo "--- grpc_to_ros2 topics ---"
while IFS= read -r topic; do
    [[ -z "$topic" ]] && continue
    _test_topic "grpc->ros2" "$topic"
done < <(_extract_topics "grpc_to_ros2")

echo ""
echo "Results: $PASS passed, $FAIL failed"
[[ $FAIL -eq 0 ]]
